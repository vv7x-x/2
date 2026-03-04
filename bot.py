import os
import json
import time
import requests
from flask import Flask, request, jsonify
from google import genai

# ================== CONFIG ==================
PAGE_ID = "588645321009003"
PAGE_ACCESS_TOKEN = "EAATZBufLpmNMBQ3su57hX6kbd5n6DPa1tMSHT9G32aerZC6JhxFAnHkMy7D2D130jTaXFJBcZBSkDN8YjVenbwrEgUFH8RZAuasP4JJEi3Bsvv9AfV8Lu6prPJRJ1ij8KAduuxXTGrKDwU8sxZAZAE2ZBilic2ruRgXHHdmVH5a9j0PHQ3JtEgtNseSC1Tb9AZBVF92tmKOulYz4Bmr2uZCgMIbmspFTz6oLISzcODn8zdFYZD"
VERIFY_TOKEN = "yahya2009"
GEMINI_API_KEY = "AIzaSyBdX7PvaNf4oqLcqcQg6911iXcp68akMxM"

PHONE_NUMBER = "01228768422"
DATA_FILE = "users.json"

# ================== INIT ==================
app = Flask(__name__)

client = genai.Client(api_key=GEMINI_API_KEY)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

# ================== UTILS ==================
def load_users():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def send_typing(sender_id):
    requests.post(
        f"https://graph.facebook.com/v25.0/me/messages",
        params={"access_token": PAGE_ACCESS_TOKEN},
        json={
            "recipient": {"id": sender_id},
            "sender_action": "typing_on"
        }
    )
    time.sleep(1.5)

def send_message(sender_id, text):
    requests.post(
        f"https://graph.facebook.com/v19.0/me/messages",
        params={"access_token": PAGE_ACCESS_TOKEN},
        json={
            "recipient": {"id": sender_id},
            "message": {"text": text}
        }
    )

# ================== AI CLASSIFICATION ==================
def analyze_message_ai(text):
    prompt = f"""
صنف الرسالة التالية إلى واحدة فقط من:
normal
ask_number
repeat_request
serious_insult
light_insult

أرجع كلمة واحدة فقط بدون شرح.

الرسالة:
{text}
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text.strip().lower()
    except:
        return "normal"

# ================== WEBHOOK VERIFY ==================
@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Verification failed", 403

# ================== WEBHOOK RECEIVE ==================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    users = load_users()

    for entry in data.get("entry", []):
        for messaging in entry.get("messaging", []):
            sender_id = messaging["sender"]["id"]
            message_text = messaging.get("message", {}).get("text", "")

            if not message_text:
                continue

            if sender_id not in users:
                users[sender_id] = {"count": 0, "muted": False}

            user = users[sender_id]
            classification = analyze_message_ai(message_text)

            if classification == "ask_number":
                user["count"] += 1
                reply = f"ده رقمي 👇\n{PHONE_NUMBER}"
            else:
                reply = "أنا ماسح الانستا 😅\nكلمني واتساب أحسن."

            send_typing(sender_id)
            send_message(sender_id, reply)
            save_users(users)

    return "EVENT_RECEIVED", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
