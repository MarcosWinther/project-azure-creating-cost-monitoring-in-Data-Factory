from azure.identity import DefaultAzureCredential
from azure.mgmt.datafactory import DataFactoryManagementClient
from azure.mgmt.datafactory.models import *
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.monitor.models import DiagnosticSettingsResource

# Variáveis
subscription_id = "<SEU_ID_DE_ASSINATURA>"
resource_group = "<SEU_RESOURCE_GROUP>"
factory_name = "<NOME_DO_SEU_DATA_FACTORY>"
location = "eastus"  # ajuste conforme necessário
workspace_resource_id = "<RESOURCE_ID_DO_LOG_ANALYTICS_WORKSPACE>"  # Ex: "/subscriptions/.../resourceGroups/.../providers/Microsoft.OperationalInsights/workspaces/..."

# Autenticação
credentials = DefaultAzureCredential()
adf_client = DataFactoryManagementClient(credentials, subscription_id)
resource_client = ResourceManagementClient(credentials, subscription_id)
monitor_client = MonitorManagementClient(credentials, subscription_id)

# 1. Criar o Data Factory
factory = Factory(location=location)
factory_result = adf_client.factories.begin_create_or_update(resource_group, factory_name, factory).result()
print(f"Data Factory criado: {factory_result.name}")

# 2. Criar uma Pipeline de monitoramento
pipeline_name = "Pipeline-Monitoramento-Custos"
activities = [
    WaitActivity(name="Aguardar5s", type_properties=WaitActivityTypeProperties(wait_time_in_seconds=5))
]
pipeline_resource = PipelineResource(activities=activities, description="Pipeline de exemplo para monitoramento")
adf_client.pipelines.create_or_update(resource_group, factory_name, pipeline_name, pipeline_resource)
print(f"Pipeline criada: {pipeline_name}")

# 3. Criar um trigger recorrente (a cada 1 hora)
trigger_name = "TriggerRecorrenteMonitoramento"
trigger = ScheduleTriggerRecurrence(frequency="Hour", interval=1)
pipeline_ref = PipelineReference(reference_name=pipeline_name)
trigger_resource = TriggerResource(
    properties=ScheduleTrigger(recurrence=trigger, pipelines=[TriggerPipelineReference(pipeline_reference=pipeline_ref)])
)
adf_client.triggers.create_or_update(resource_group, factory_name, trigger_name, trigger_resource)
adf_client.triggers.begin_start(resource_group, factory_name, trigger_name).result()
print(f"Trigger '{trigger_name}' criado e ativado.")

# 4. (Opcional) Habilitar envio de logs para o Log Analytics
diagnostic_name = "ADF-Diagnostic-Settings"
settings = DiagnosticSettingsResource(
    logs=[
        {
            "category": "PipelineRuns",
            "enabled": True,
            "retentionPolicy": {"enabled": False, "days": 0}
        },
        {
            "category": "ActivityRuns",
            "enabled": True,
            "retentionPolicy": {"enabled": False, "days": 0}
        }
    ],
    metrics=[],
    workspace_id=workspace_resource_id
)
monitor_client.diagnostic_settings.create_or_update(factory_result.id, diagnostic_name, settings)
print("Configuração de diagnóstico enviada para o Log Analytics.")

