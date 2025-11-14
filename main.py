from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import InputPeerUser
from flask import Flask, request, jsonify
import asyncio, threading, json, time, os

# ============================
# HARD-CODED CONFIG
# ============================

API_ID = 33886333
API_HASH = "979753e6fdb91479f7153d533788e87f"

SESSION_STRING = "1BVtsOL4BuyZpgmGfZ6xsw-VcDebep9dYVcwONPc9HOtu-xsn9ddAe2krvuuh0Z7MtZDjVluYRiC3i7Yh0WpORXEQ2hp0MruOOUh-BbKu0-NXvUIkQbnlYl0yvN-SCtT8HJabHdT_R97gkgkq88k5mMrHhPAb3hGOLBMMpfgvGk9ybRBHgW_kFJ2pth5uXKyg_rqJX4tuy_2Rb8iCIND0Dk46VsQy4-oS5jYq8YcXGnYjH3fSfmW5BZnrmxyIbT4CXu8mbgxIT5FE9UIdYLkAWS0B9MX4ZXkpbYwWYKsy_8bCGdAA7ec6owt_FvPekOjSYxYOL40biRC2zbNYnMb_eJMhqMEtpyw="

TARGET = InputPeerUser(
    user_id=8131321158,
    access_hash=7356519516453717310
)

# ============================
# Flask App
# ============================

app = Flask(__name__)

# ============================
# Async Loop & Telegram Client
# ============================

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

client = TelegramClient(
    StringSession(SESSION_STRING),
    API_ID,
    API_HASH,
    loop=loop
)

# ============================
# Reply Storage
# ============================

latest_reply = {"reply": "", "timestamp": 0}

# ============================
# Telegram Listener
# ============================

@client.on(events.NewMessage(from_users=TARGET.user_id))
async def handle_reply(event):
    msg = event.raw_text.strip()

    if msg.lower().startswith("thinking"):
        return
    
    latest_reply["reply"] = msg
    latest_reply["timestamp"] = time.time()

    with open("reply.json", "w") as f:
        json.dump(latest_reply, f)

    print("📩 Reply:", msg)


# ============================
# ROUTES
# ============================

@app.route("/")
def health():
    return jsonify({"ok": True, "status": "running"})

@app.route("/send", methods=["POST"])
def send_message():
    data = request.get_json(force=True)
    text = (data or {}).get("question", "").strip()

    if not text:
        return jsonify({"ok": False, "error": "Missing question"}), 400

    async def _send():
        await client.send_message(TARGET, text)
        print("✅ Sent:", text)

    fut = asyncio.run_coroutine_threadsafe(_send(), loop)
    fut.result(timeout=15)

    return jsonify({"ok": True, "status": "sent"})

@app.route("/reply", methods=["GET"])
def reply():
    if latest_reply["reply"]:
        return jsonify({"ok": True, "reply": latest_reply["reply"], "timestamp": latest_reply["timestamp"]})

    if os.path.exists("reply.json"):
        try:
            with open("reply.json") as f:
                return jsonify({"ok": True, "reply": json.load(f)["reply"]})
        except:
            pass

    return jsonify({"ok": False, "error": "No reply yet"}), 404


# ============================
# Background Loop
# ============================

def start_loop():
    asyncio.set_event_loop(loop)
    loop.run_forever()


# ============================
# MAIN START
# ============================

if __name__ == "__main__":
    print("🚀 Starting...")

    threading.Thread(target=start_loop, daemon=True).start()

    asyncio.run_coroutine_threadsafe(client.start(), loop).result(timeout=25)
    print("✅ Telegram connected")

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
