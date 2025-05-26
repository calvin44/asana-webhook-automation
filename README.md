# Asana Automation Webhook Handler

This project provides a FastAPI-based server that listens to Asana webhook events and automates task processing based on specific business rules.

It is primarily designed to assist with internal task triaging by:
- Automatically categorizing or deleting tasks that don’t meet data requirements
- Detecting and processing form-based task submissions
- Supporting automated feasibility evaluation, requirement clarification, and approval flows

## Features

✅ Handles webhook handshakes and verifies `X-Hook-Secret`  
✅ Categorizes tasks based on custom field values  
✅ Deletes tasks with insufficient information  
✅ Sends notifications via Slack  
✅ Groups Asana events by task for efficient rule processing  
✅ Background task handling for responsiveness

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/asana-automation.git
cd asana-automation
2. Install dependencies
Ensure you're using Python 3.11 or later:

bash
Copy
Edit
pip install -r requirements.txt
3. Configure environment variables
Create a .env file in the root directory and configure the following:

env
Copy
Edit
ASANA_PERSONAL_ACCESS_TOKEN=your_token_here
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz
WEBHOOK_SECRET=my_webhook_secret
If you're unsure about these values, check your Asana developer console or Slack app integrations.

Usage
Run the FastAPI app
bash
Copy
Edit
uvicorn main:app --reload
This will start the server at http://localhost:8000.

Asana Webhook Setup
Register a webhook in Asana with a POST URL to:

arduino
Copy
Edit
http://your-server.com/asana-webhook
Asana will send a X-Hook-Secret header on the first handshake request. The server will echo it back to confirm the webhook registration.

Project Structure
bash
Copy
Edit
.
├── main.py                    # Main FastAPI app handling webhook logic
├── scoring_system/           # Business value scoring logic
├── asana_utils/              # Asana-related task/event utilities
├── utils/                    # Notification tools (e.g., Slack)
├── requirements.txt          # Project dependencies
└── .env                      # Environment variables (not committed)
Rule Logic Overview
✅ Requirement Clarifying
Triggered by new tasks

If the task is in the “Requirement Clarifying” stage:

Keep the task if it contains both a description and an attachment

Delete it otherwise, and send a Slack notification

Other automation rules for "Pending Approval" and "Feasibility Evaluating" are also run in the background for newly changed tasks.

Contributing
If you’d like to contribute or extend this automation, feel free to open a pull request or issue.

License
MIT

Author
Calvin Fredicson

