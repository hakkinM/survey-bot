import json
import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file

import anthropic

load_dotenv()

app = Flask(__name__)

# Load the survey template once at startup
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "template", "first_template.json")
with open(TEMPLATE_PATH) as f:
    TEMPLATE = json.load(f)

client = anthropic.Anthropic()

SYSTEM_PROMPT = f"""You are a friendly survey chatbot conducting a developer survey. Here is the survey template you must follow:

{json.dumps(TEMPLATE, indent=2)}

RULES:
1. Start by greeting the developer briefly (one sentence).
2. Select up to {TEMPLATE['max_questions']} question areas. Prioritize required=true areas first.
3. Ask ONE question at a time. Wait for the response before moving on.
4. Use the "intent" field to craft natural, developer-friendly questions — don't repeat the intent verbatim.
5. For rating_1_to_5: prompt with the 1-5 scale. If the answer isn't a number, gently re-ask once.
6. For open_text: accept any free-form response.
7. After all questions are answered, thank the developer and output the completed survey as a JSON block wrapped in <SURVEY_COMPLETE> tags.

The completed survey JSON must follow this exact schema:
{{
  "survey_id": "<from template>",
  "respondent_id": "<generate a short uuid>",
  "completed_at": "<ISO 8601 timestamp>",
  "responses": [
    {{
      "area_id": "<area_id>",
      "question_asked": "<the exact question you asked>",
      "answer": "<the developer's answer>",
      "response_type": "<response_type from template>"
    }}
  ]
}}

For rating_1_to_5, the answer must be an integer (not a string).

Output the completed survey like this — nothing else after the closing tag:
<SURVEY_COMPLETE>
{{...completed survey JSON...}}
</SURVEY_COMPLETE>
"""


@app.route("/")
def index():
    return send_file("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    messages = data.get("messages", [])

    if not messages:
        return jsonify({"error": "No messages provided"}), 400

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    reply = response.content[0].text
    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
