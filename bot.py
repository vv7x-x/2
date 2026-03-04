import os
import json
import time
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

# ================== CONFIG ==================
PAGE_ID = "588645321009003"  # غيره لو هتستخدم صفحة تانية
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

PHONE_NUMBER = "01228768422"
DATA_FILE = "users.json"

# ================== INIT ==================
app = Flask(__name__)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

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
        f"https://graph.facebook.com/v19.0/{PAGE_ID}/messages",
        params={"access_token": PAGE_ACCESS_TOKEN},
        json={
            "recipient": {"id": sender_id},
            "sender_action": "typing_on"
        }
    )
    time.sleep(1.5)

def send_message(sender_id, text):
    requests.post(
        f"https://graph.facebook.com/v19.0/{PAGE_ID}/messages",
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
        response = model.generate_content(prompt)
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
        for change in entry.get("changes", []):
            value = change.get("value", {})

            if "messages" in value:
                for message in value["messages"]:
                    sender_id = message["from"]["id"]
                    message_text = message.get("text", "")

                    if not message_text:
                        continue

                    if sender_id not in users:
                        users[sender_id] = {
                            "count": 0,
                            "muted": False
                        }

                    user = users[sender_id]
                    classification = analyze_message_ai(message_text)

                    # ====== MUTE MODE ======
                    if user["muted"]:
                        if classification == "normal":
                            user["muted"] = False
                        else:
                            save_users(users)
                            continue

                    # ====== SERIOUS INSULT ======
                    if classification == "serious_insult":
                        send_typing(sender_id)
                        send_message(sender_id,
                            "الأسلوب ده ميليقش 👀\n"
                            "لما تحب نتكلم باحترام ابعت رسالة محترمة."
                        )
                        user["muted"] = True

                    # ====== LIGHT INSULT ======
                    elif classification == "light_insult":
                        send_typing(sender_id)
                        send_message(sender_id,
                            "خف علينا شوية 😂\n"
                            "قول اللي عندك بس بهدوء."
                        )

                    # ====== ASK NUMBER ======
                    elif classification == "ask_number":
                        user["count"] += 1

                        replies = {
                            1: f"ده رقمي اهو 👇\n{PHONE_NUMBER}",
                            2: "يا عم ما بعتهولك فوق 😂\nركز بس وهتلاقيه.",
                            3: "هو احنا هنفضل نعيد ونزيد؟ 😅\nالرقم فوق والله.",
                            4: "بقولك ايه احفظه عندك بقى 😂"
                        }

                        reply = replies.get(user["count"], "خلاص بقى 😅 مش هبعته تاني.")

                        send_typing(sender_id)
                        send_message(sender_id, reply)

                    # ====== REPEAT REQUEST ======
                    elif classification == "repeat_request":
                        send_typing(sender_id)
                        send_message(sender_id,
                            f"اهو يا سيدي 👇\n{PHONE_NUMBER}"
                        )

                    # ====== NORMAL ======
                    else:
                        send_typing(sender_id)
                        send_message(sender_id,
                            "يا أهلاً 👋\n"
                            "أنا ماسح الانستا ومبفتحوش كتير 😅\n"
                            "لو عايزني بجد كلمني واتساب أحسن."
                        )

                    save_users(users)

    return "EVENT_RECEIVED", 200


# ================== RUN ==================
if __name__ == "__main__":
    app.run(port=5000)
