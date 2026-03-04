import os
import json
import time
import requests
from flask import Flask, request

# ================== CONFIG ==================
PAGE_ACCESS_TOKEN = "EAATZBufLpmNMBQ3su57hX6kbd5n6DPa1tMSHT9G32aerZC6JhxFAnHkMy7D2D130jTaXFJBcZBSkDN8YjVenbwrEgUFH8RZAuasP4JJEi3Bsvv9AfV8Lu6prPJRJ1ij8KAduuxXTGrKDwU8sxZAZAE2ZBilic2ruRgXHHdmVH5a9j0PHQ3JtEgtNseSC1Tb9AZBVF92tmKOulYz4Bmr2uZCgMIbmspFTz6oLISzcODn8zdFYZD"
VERIFY_TOKEN = "yahya2009"
GEMINI_API_KEY = "AIzaSyBdX7PvaNf4oqLcqcQg6911iXcp68akMxM"
PHONE_NUMBER = "01228768422"

DATA_FILE = "users.json"

# ================== INIT ==================
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Bot is running ✅", 200

# ================== SAFE FILE HANDLING ==================
def load_users():
    try:
        if not os.path.exists(DATA_FILE):
            return {}
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
    except:
        pass

# ================== SEND FUNCTIONS ==================
def send_typing(recipient_id):
    try:
        requests.post(
            "https://graph.facebook.com/v25.0/me/messages",
            params={"access_token": PAGE_ACCESS_TOKEN},
            json={
                "recipient": {"id": recipient_id},
                "sender_action": "typing_on"
            }
        )
        time.sleep(1.2)
    except:
        pass

def send_message(recipient_id, text):
    try:
        requests.post(
            "https://graph.facebook.com/v25.0/me/messages",
            params={"access_token": PAGE_ACCESS_TOKEN},
            json={
                "recipient": {"id": recipient_id},
                "message": {"text": text}
            }
        )
    except:
        pass

# ================== AI CLASSIFICATION ==================
def analyze_message_ai(text):
    return "normal"

# ================== VERIFY WEBHOOK ==================
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Verification failed", 403

# ================== RECEIVE MESSAGES ==================
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        users = load_users()

        if data.get("object") != "instagram":
            return "ignored", 200

        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})

                if "messages" in value:
                    for message in value["messages"]:
                        sender_id = message["from"]["id"]
                        message_text = message.get("text", {}).get("body", "")

                        if not message_text:
                            continue

                        if sender_id not in users:
                            users[sender_id] = {"count": 0}

                        classification = analyze_message_ai(message_text)

                        if classification == "ask_number":
                            users[sender_id]["count"] += 1
                            reply = f"ده رقمي 👇\n{PHONE_NUMBER}"
                        elif classification == "repeat_request":
                            reply = f"كنت باعتلك الرقم 😅\n{PHONE_NUMBER}"
                        elif classification == "serious_insult":
                            reply = "احترم نفسك لو سمحت."
                        elif classification == "light_insult":
                            reply = "ليه كده بس 😅"
                        else:
                            reply = "أنا ماسح الانستا 😅\nكلمني واتساب أحسن."

                        send_typing(sender_id)
                        send_message(sender_id, reply)
                        save_users(users)

        return "EVENT_RECEIVED", 200

    except Exception as e:
        print("ERROR:", e)
        return "error", 200

# ================== RUN ==================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
