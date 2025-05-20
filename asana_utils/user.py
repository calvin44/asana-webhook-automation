from typing import Dict
from asana import UsersApi
from asana.rest import ApiException
from loguru import logger
from asana_utils.api import get_asana_client


def find_user_by_gid(user_gid: str) -> Dict:
    """
    Retrieve user information from user_gid
    """
    user_api = UsersApi(get_asana_client())
    try:
        api_response = user_api.get_user(user_gid, {})
        return api_response
    except ApiException as e:
        logger.error(f"No user found from user gid: {user_gid}: {e}")
        return {}
