
from asana import WebhooksApi
from asana.rest import ApiException
from Utils.resources import PROJECT_GID, TARGET_URL, WORKSPACE_GID
from asana_utils.api import get_asana_client


def check_webhook_exists():
    webhook_api_instance = WebhooksApi(get_asana_client())
    opts = {
        "limit": 100,
        "workspace": WORKSPACE_GID,
        "resource": PROJECT_GID,
    }
    try:
        api_response = list(
            webhook_api_instance.get_webhooks(WORKSPACE_GID, opts))

        if len(api_response) == 0:
            return False

        for webhook in api_response:
            if webhook["target"] != TARGET_URL or webhook["resource"]["gid"] != PROJECT_GID:
                continue
            return True

    except ApiException as e:
        print("Exception when calling WebhooksApi->get_webhooks: %s\n" % e)
        return False
