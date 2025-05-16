from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Asana API details
WORKSPACE_GID = os.getenv("WORKSPACE_GID")
PROJECT_GID = os.getenv("PROJECT_GID")
ASANA_PAT = os.getenv("ASANA_PAT")
TARGET_URL = os.getenv("TARGET_URL")
CUSTOM_FIELD_GID = os.getenv("CUSTOM_FIELD_GID")
