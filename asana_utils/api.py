from typing import Dict
import asana
import asana.api_client
from asana.rest import ApiException
from Utils.resources import ASANA_PAT, CUSTOM_FIELD_GID
from asana import CustomFieldsApi


def get_asana_client():
    """
    Returns an Asana client instance.
    """

    configuration = asana.Configuration()
    configuration.access_token = ASANA_PAT
    api_client = asana.api_client.ApiClient(configuration)

    return api_client


def get_enum_custom_fields() -> Dict[str, str]:
    """
    Retrieve the enum options for a specific Asana custom field.

    This function uses the Asana API to fetch the available enum options
    (e.g., dropdown choices) for a given custom field identified by CUSTOM_FIELD_GID.

    Returns:
        Dict[str, str]: A dictionary mapping enum option GID to enum option name,
                        or an empty dict if the request fails or no options are found.
    """

    custom_field_instance = CustomFieldsApi(get_asana_client())
    opts = {
        "opt_fields": "enum_options.name",
    }
    try:
        api_response = custom_field_instance.get_custom_field(
            CUSTOM_FIELD_GID, opts
        )

        enum_options = {}
        for enum_option in api_response["enum_options"]:
            enum_options[enum_option["gid"]] = enum_option["name"]
        return enum_options

    except ApiException as e:
        print(f"Exception when calling CustomFieldsApi->get_custom_field: {e}")
        return {}
