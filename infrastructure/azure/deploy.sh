#!/usr/bin/env bash
# ==============================================================================
# MatchMind Azure Deployment Script (Bash / CI/CD)
# Microsoft Premier League Hackathon: "Inside the Game"
# ==============================================================================

set -euo pipefail

RESOURCE_GROUP="${1:-rg-matchmind-hackathon}"
LOCATION="${2:-eastus2}"
ENVIRONMENT="${3:-dev}"

echo "=========================================================="
echo "   MatchMind Azure Infrastructure Deployment Script        "
echo "=========================================================="

echo "[1/4] Checking Azure CLI login..."
if ! az account show > /dev/null 2>&1; then
    echo "Please authenticate with 'az login' first."
    exit 1
fi

echo "[2/4] Creating Resource Group: $RESOURCE_GROUP in $LOCATION..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output table

echo "[3/4] Registering Azure resource providers..."
for provider in Microsoft.App Microsoft.OperationalInsights Microsoft.CognitiveServices Microsoft.DocumentDB Microsoft.ContainerRegistry; do
    az provider register --namespace "$provider" --output none 2>/dev/null || true
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BICEP_FILE="$SCRIPT_DIR/bicep/main.bicep"
PARAMS_FILE="$SCRIPT_DIR/env/dev.parameters.json"

echo "[4/4] Deploying Bicep template: $BICEP_FILE..."
az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --template-file "$BICEP_FILE" \
    --parameters "$PARAMS_FILE" \
    --parameters environment="$ENVIRONMENT" location="$LOCATION" \
    --output table

echo "Deployment complete!"
