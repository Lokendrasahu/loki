from flask import Flask, request, jsonify
from telethon import TelegramClient, events
import asyncio, json, time, threading, os

# Telegram Credentials
API_ID = 33886333
API_HASH = "979753e6fdb91479f7153d533788e87f"
SESSION = "askplex_session"
TARGET = "askplexbot"  # without @

app = Flask(__name__)

# Create event loop for Telethon
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
client = TelegramClient(SESSION, API_ID, API_HASH, loop=loop)

latest_reply = {"reply": "No reply yet"}

# Event listener for new messages
@client.on(events.NewMessage(from_users=TARGET))
async def handler(event):
    msg = event.raw_text.strip()
    print(f"📩 {msg}")
    if msg.lower().startswith("thinking"):
        return
    latest_reply["reply"] = msg
    with open("reply.json", "w", encoding="utf-8") as f:
        json.dump({"reply": msg, "timestamp": time.time()}, f)

# Flask endpoint for iPhone Shortcuts
@app.route("/send", methods=["POST"])
def send_message():
    data = request.get_json(force=True)
    q = (data or {}).get("question", "").strip()

    if not q:
        return jsonify({"ok": False, "error": "Missing question"}), 400

    async def run():
        async with client.conversation(TARGET, timeout=60) as conv:
            await conv.send_message(q)
            try:
                resp = await conv.get_response()
                return resp.raw_text
            except asyncio.TimeoutError:
                return "⏳ No reply (timeout)"

    future = asyncio.run_coroutine_threadsafe(run(), loop)
    try:
        result = future.result(timeout=65)
        return jsonify({"ok": True, "reply": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "ok": True,
        "status": "running",
        "usage": "POST /send { 'question': 'your message' }"
    })

def loop_runner():
    asyncio.set_event_loop(loop)
    loop.run_forever()

if __name__ == "__main__":
    threading.Thread(target=loop_runner, daemon=True).start()
    asyncio.run_coroutine_threadsafe(client.start(), loop)
    print(f"✅ Telegram started for @{TARGET}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
