import asana
import asana.api_client
from utils.resources import ASANA_PAT


def get_asana_client():
    """
    Returns an Asana client instance.
    """

    configuration = asana.Configuration()
    configuration.access_token = ASANA_PAT
    api_client = asana.api_client.ApiClient(configuration)

    return api_client
