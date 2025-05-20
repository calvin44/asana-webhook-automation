from typing import Dict
from asana.rest import ApiException
from asana import CustomFieldsApi
from loguru import logger
from utils.resources import CUSTOM_FIELD_GID
from asana_utils.api import get_asana_client


def get_enum_custom_fields_by_gid() -> Dict[str, str]:
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


def get_enum_custom_fields_by_name() -> Dict[str, str]:
    """
    Retrieve the enum options for a specific Asana custom field, with names as keys.

    This function uses the Asana API to fetch the available enum options
    (e.g., dropdown choices) for a given custom field identified by CUSTOM_FIELD_GID.

    Returns:
        Dict[str, str]: A dictionary mapping enum option name to enum option GID,
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
            enum_options[enum_option["name"]] = enum_option["gid"]
        return enum_options

    except ApiException as e:
        print(f"Exception when calling CustomFieldsApi->get_custom_field: {e}")
        return {}


def get_option_info(option_text: str) -> Dict:
    """
    Get info [gid, name, etc.] from asana API and filter out the option by text
    """
    try:
        options = get_enum_custom_fields_by_name()
        logger.debug(f"Fetched options by name: {options}")
        return options[option_text]
    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"Could not find enum options: {option_text}: {e}")
        return {}
