from telethon import TelegramClient, events
from telethon.tl.types import InputPeerUser
from flask import Flask, request, jsonify
import asyncio, threading, os, json, time

API_ID = 33886333
API_HASH = "979753e6fdb91479f7153d533788e87f"
SESSION = "askplex_session"
TARGET = InputPeerUser(user_id=8131321158, access_hash=7356519516453717310)

app = Flask(__name__)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
client = TelegramClient(SESSION, API_ID, API_HASH, loop=loop)

# ============================
# Telegram Reply Listener
# ============================
@client.on(events.NewMessage(from_users=TARGET.user_id))
async def handle_reply(event):
    msg = event.raw_text.strip()
    if not msg.lower().startswith("thinking"):
        print(f"📩 {msg}")
        with open("reply.json", "w", encoding="utf-8") as f:
            json.dump({"reply": msg, "timestamp": time.time()}, f)

# ============================
# Flask Routes
# ============================

@app.route("/", methods=["GET"])
def health():
    return jsonify({"ok": True, "status": "running", "usage": "POST /send { 'question': 'your message' }"})

@app.route("/send", methods=["POST"])
def send_msg():
    data = request.get_json(force=True)
    q = (data or {}).get("question", "").strip()
    if not q:
        return jsonify({"ok": False, "error": "Missing question"}), 400

    async def run():
        await client.send_message(TARGET, q)
        print("✅ Sent:", q)
        return "Thinking..."

    try:
        fut = asyncio.run_coroutine_threadsafe(run(), loop)
        res = fut.result(timeout=20)
        return jsonify({"ok": True, "reply": res})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/reply", methods=["GET"])
def get_latest_reply():
    """Fetch the most recent saved reply."""
    try:
        with open("reply.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify({
            "ok": True,
            "reply": data.get("reply", ""),
            "timestamp": data.get("timestamp")
        })
    except FileNotFoundError:
        return jsonify({"ok": False, "error": "No reply yet"}), 404

# ============================
# Background Event Loop
# ============================
def loop_forever():
    asyncio.set_event_loop(loop)
    loop.run_forever()

if __name__ == "__main__":
    threading.Thread(target=loop_forever, daemon=True).start()
    asyncio.run_coroutine_threadsafe(client.start(), loop)
    print("✅ Telegram client started")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
