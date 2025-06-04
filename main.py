import os
import requests
import time
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def ask_gpt(prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "Ты менеджер по продажам на Авито. Отвечай на сообщения клиентов профессионально, доброжелательно и кратко."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }

    # Пытаемся сделать 3 попытки в случае перегрузки (429)
    for attempt in range(3):
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 429:
            time.sleep(2 ** attempt)
            continue
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"]
        return reply

    return "Извините, сейчас слишком много запросов. Попробуйте позже."

def send_telegram_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.json

    chat_id = data["message"]["chat"]["id"]
    user_message = data["message"]["text"]

    reply = ask_gpt(user_message)
    send_telegram_message(chat_id, reply)

    return "ok"

@app.route("/", methods=["GET"])
def index():
    return "AvitoExpertGPT Telegram Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)