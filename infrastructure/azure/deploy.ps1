<#
.SYNOPSIS
    Deploys MatchMind to Microsoft Azure using Azure Bicep.
    Microsoft Premier League Hackathon: "Inside the Game"

.DESCRIPTION
    Creates resource group, registers providers, deploys Azure OpenAI, Azure AI Speech,
    Cosmos DB, and Azure Container Apps hosting MatchMind.
#>

param (
    [string]$ResourceGroupName = "rg-matchmind-hackathon",
    [string]$Location = "eastus2",
    [string]$Environment = "dev",
    [string]$SubscriptionId = ""
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   MatchMind Azure Infrastructure Deployment Script        " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Login verification
Write-Host "[1/5] Verifying Azure CLI authentication..." -ForegroundColor Yellow
$account = az account show --output json 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "Not logged in to Azure. Running 'az login'..." -ForegroundColor Yellow
    az login
}

if ($SubscriptionId) {
    Write-Host "Setting subscription: $SubscriptionId" -ForegroundColor Yellow
    az account set --subscription $SubscriptionId
}

$currentSub = az account show --query name -o tsv
Write-Host "Active Subscription: $currentSub" -ForegroundColor Green

# 2. Resource Group
Write-Host "[2/5] Creating or verifying Resource Group '$ResourceGroupName' in '$Location'..." -ForegroundColor Yellow
az group create --name $ResourceGroupName --location $Location --output table

# 3. Register Required Resource Providers
Write-Host "[3/5] Registering required Azure resource providers..." -ForegroundColor Yellow
$providers = @(
    "Microsoft.App",
    "Microsoft.OperationalInsights",
    "Microsoft.CognitiveServices",
    "Microsoft.DocumentDB",
    "Microsoft.ContainerRegistry"
)
foreach ($prov in $providers) {
    az provider register --namespace $prov --output none
}

# 4. Deploy Bicep Template
Write-Host "[4/5] Deploying Azure Bicep Infrastructure..." -ForegroundColor Yellow
$bicepPath = Join-Path $PSScriptRoot "bicep\main.bicep"
$paramPath = Join-Path $PSScriptRoot "env\dev.parameters.json"

$deployment = az deployment group create `
    --resource-group $ResourceGroupName `
    --template-file $bicepPath `
    --parameters $paramPath `
    --parameters environment=$Environment location=$Location `
    --output json | ConvertFrom-Json

# 5. Output Results
Write-Host "[5/5] Deployment Successful! Output endpoints:" -ForegroundColor Green
Write-Host "----------------------------------------------------------" -ForegroundColor Green
$outputs = $deployment.properties.outputs
Write-Host "Container App URL : $($outputs.containerAppUrl.value)" -ForegroundColor Cyan
Write-Host "OpenAI Endpoint   : $($outputs.openAiEndpoint.value)" -ForegroundColor Cyan
Write-Host "Speech Endpoint   : $($outputs.speechEndpoint.value)" -ForegroundColor Cyan
Write-Host "Cosmos DB Endpoint: $($outputs.cosmosEndpoint.value)" -ForegroundColor Cyan
Write-Host "ACR Login Server  : $($outputs.acrLoginServer.value)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Green
