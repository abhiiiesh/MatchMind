// ==============================================================================
// MatchMind Master Infrastructure as Code Template (Azure Bicep)
// Microsoft Premier League Hackathon: "Inside the Game"
// ==============================================================================

targetScope = 'resourceGroup'

@description('Environment name prefix (e.g. dev, prod)')
param environment string = 'dev'

@description('Azure region for deployment')
param location string = resourceGroup().location

@description('Base application name')
param appName string = 'matchmind'

@description('Docker image name or ACR image URI for the unified MatchMind engine')
param containerImage string = 'mcr.microsoft.com/azuredocs/aci-helloworld:latest'

// Resource Names
var prefix = '${appName}-${environment}'
var logAnalyticsName = '${prefix}-logs'
var appEnvName = '${prefix}-cae'
var acrName = replace('${appName}${environment}acr', '-', '')
var openAiName = '${prefix}-openai'
var speechName = '${prefix}-speech'
var cosmosName = '${prefix}-cosmos'
var containerAppName = '${prefix}-engine'

// 1. Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// 2. Azure Container Registry (ACR)
resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

// 3. Azure OpenAI Service
resource openAi 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: openAiName
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: openAiName
    publicNetworkAccess: 'Enabled'
  }
}

// 3a. Model Deployment: GPT-4o
resource gpt4oDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openAi
  name: 'gpt-4o'
  sku: {
    name: 'Standard'
    capacity: 20
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-05-13'
    }
  }
}

// 3b. Model Deployment: GPT-4o-mini
resource gpt4oMiniDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openAi
  name: 'gpt-4o-mini'
  sku: {
    name: 'Standard'
    capacity: 30
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o-mini'
      version: '2024-07-18'
    }
  }
  dependsOn: [
    gpt4oDeployment
  ]
}

// 4. Azure AI Speech Cognitive Service
resource speech 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: speechName
  location: location
  kind: 'SpeechServices'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: speechName
    publicNetworkAccess: 'Enabled'
  }
}

// 5. Azure Cosmos DB (Serverless NoSQL for match state & RAG vector search)
resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' = {
  name: cosmosName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
  }
}

// 6. Azure Container Apps Managed Environment
resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: appEnvName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// 7. MatchMind Azure Container App
resource matchmindApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
    }
    template: {
      containers: [
        {
          name: 'matchmind'
          image: containerImage
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
          }
          env: [
            {
              name: 'ENVIRONMENT'
              value: 'production'
            }
            {
              name: 'PORT'
              value: '8000'
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: openAi.properties.endpoint
            }
            {
              name: 'AZURE_SPEECH_KEY'
              value: speech.listKeys().key1
            }
            {
              name: 'AZURE_SPEECH_REGION'
              value: location
            }
            {
              name: 'AZURE_COSMOS_ENDPOINT'
              value: cosmos.properties.documentEndpoint
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

// Outputs
output containerAppUrl string = 'https://${matchmindApp.properties.configuration.ingress.fqdn}'
output openAiEndpoint string = openAi.properties.endpoint
output speechEndpoint string = speech.properties.endpoint
output cosmosEndpoint string = cosmos.properties.documentEndpoint
output acrLoginServer string = acr.properties.loginServer
