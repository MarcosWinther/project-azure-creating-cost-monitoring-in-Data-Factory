#!/bin/bash

# Variáveis (edite conforme seu ambiente)
SUBSCRIPTION_ID="<SEU_ID_DE_ASSINATURA>"
RESOURCE_GROUP="<SEU_RESOURCE_GROUP>"
LOCATION="eastus"
ADF_NAME="<NOME_DO_SEU_DATA_FACTORY>"
LOG_ANALYTICS_WORKSPACE="<NOME_DO_WORKSPACE>"
LA_RESOURCE_GROUP="<RESOURCE_GROUP_DO_WORKSPACE>"

# Login e seleção da assinatura (no Cloud Shell geralmente já está ativo)
az account set --subscription "$SUBSCRIPTION_ID"

echo "Criando grupo de recursos (se necessário)..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

echo "Criando Azure Data Factory..."
az datafactory create --resource-group "$RESOURCE_GROUP" --factory-name "$ADF_NAME" --location "$LOCATION"

echo "Criando Pipeline de exemplo (atividade de espera)..."
cat <<EOF > pipeline.json
{
  "properties": {
    "activities": [
      {
        "name": "Aguardar5s",
        "type": "Wait",
        "typeProperties": {
          "waitTimeInSeconds": 5
        }
      }
    ],
    "description": "Pipeline de monitoramento de exemplo"
  }
}
EOF

az datafactory pipeline create --resource-group "$RESOURCE_GROUP" --factory-name "$ADF_NAME" --name "Pipeline-Monitoramento-Custos" --pipeline "$(cat pipeline.json)"

echo "Criando Trigger de execução recorrente (1 hora)..."
cat <<EOF > trigger.json
{
  "properties": {
    "type": "ScheduleTrigger",
    "pipelines": [
      {
        "pipelineReference": {
          "referenceName": "Pipeline-Monitoramento-Custos",
          "type": "PipelineReference"
        }
      }
    ],
    "recurrence": {
      "frequency": "Hour",
      "interval": 1
    }
  }
}
EOF

az datafactory trigger create --resource-group "$RESOURCE_GROUP" --factory-name "$ADF_NAME" --name "TriggerRecorrenteMonitoramento" --trigger "$(cat trigger.json)"
az datafactory trigger start --resource-group "$RESOURCE_GROUP" --factory-name "$ADF_NAME" --name "TriggerRecorrenteMonitoramento"

echo "Buscando ID do Log Analytics Workspace..."
WORKSPACE_ID=$(az monitor log-analytics workspace show --resource-group "$LA_RESOURCE_GROUP" --workspace-name "$LOG_ANALYTICS_WORKSPACE" --query "id" -o tsv)

echo "Habilitando Diagnóstico (Log Analytics)..."
az monitor diagnostic-settings create \
  --name "ADF-Diagnostic-Settings" \
  --resource "$(az datafactory show --resource-group "$RESOURCE_GROUP" --name "$ADF_NAME" --query id -o tsv)" \
  --workspace "$WORKSPACE_ID" \
  --logs '[{"category":"PipelineRuns","enabled":true},{"category":"ActivityRuns","enabled":true}]'

echo "✅ Configuração concluída com sucesso!"
