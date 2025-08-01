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
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
G_SHEET_CREDENTIAL = os.getenv("G_SHEET_CREDENTIAL")

# Project scoring
SCORING_DOC_NAME = "Project Scoring System"
SCORING_SHEETNAME = "Project Scoring"