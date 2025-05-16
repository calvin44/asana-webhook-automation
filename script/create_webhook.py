import asana
from asana.rest import ApiException
from loguru import logger

from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()


configuration = asana.Configuration()
configuration.access_token = os.getenv("ASANA_PAT")
api_client = asana.ApiClient(configuration)

# create an instance of the API class
webhooks_api_instance = asana.WebhooksApi(api_client)
# dict | The webhook workspace and target.
body = {"data": {
    "resource": os.getenv("PROJECT_GID"),
    "target": os.getenv("TARGET_URL"),
    "filters": [
        {
            "resource_type": "task",
            "action": "changed"
        },
        {
            "resource_type": "task",
            "action": "added"
        }
    ]
}}

opts = {
    # list[str] | This endpoint returns a resource which excludes some properties by default. To include those optional properties, set this query parameter to a comma-separated list of the properties you wish to include.
    'opt_fields': "active,created_at,delivery_retry_count,failure_deletion_timestamp,filters,filters.action,filters.fields,filters.resource_subtype,last_failure_at,last_failure_content,last_success_at,next_attempt_after,resource,resource.name,target",
}

try:
    # Establish a webhook
    api_response = webhooks_api_instance.create_webhook(body, opts)
    logger.info(f"Webhook created successfully: {api_response}")
except ApiException as e:
    logger.error(f"Exception when calling WebhooksApi->create_webhook: {e}")
