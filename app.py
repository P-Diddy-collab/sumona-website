from flask import Flask, request, make_response, send_from_directory
import uuid, os, requests
from datetime import datetime

app = Flask(__name__, static_folder=".")

MAX_DEVICES = 999999
COOKIE_NAME = "sid"
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def HEADERS():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": "Bearer " + SUPABASE_KEY,
        "Content-Type": "application/json"
    }

BLOCK_HTML = """<!DOCTYPE html>
<html lang="bn"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>অ্যাক্সেস সীমিত</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#080c14;color:#fff;font-family:sans-serif;
  display:flex;align-items:center;justify-content:center;min-height:100vh}
.box{text-align:center;padding:48px 40px;max-width:420px;width:90%;
  border:1px solid rgba(232,184,109,0.25);border-radius:24px;
  background:rgba(255,255,255,0.03)}
.lock{font-size:64px;margin-bottom:20px}
h2{color:#e8b86d;font-size:22px;margin-bottom:12px}
p{color:rgba(255,255,255,0.5);font-size:15px;line-height:1.8}
.pill{display:inline-block;margin-top:20px;padding:8px 20px;
  border-radius:30px;background:rgba(232,184,109,0.12);
  border:1px solid rgba(232,184,109,0.3);color:#e8b86d;font-size:13px}
</style></head><body>
<div class="box">
  <div class="lock">&#128274;</div>
  <h2>অ্যাক্সেস সীমিত</h2>
  <p>এই সাইটে সর্বোচ্চ <strong style="color:#e8b86d">MAX_D</strong>টি
  ডিভাইস অ্যাক্সেস করতে পারবে।<br><br>
  ইতিমধ্যে <strong style="color:#e8b86d">COUNT_D</strong>টি ডিভাইস
  যুক্ত আছে।</p>
  <div class="pill">&#128101; COUNT_D / MAX_D ডিভাইস পূর্ণ</div>
</div></body></html>"""

def get_count():
    r = requests.get(
        SUPABASE_URL + "/rest/v1/devices?select=device_id",
        headers=HEADERS()
    )
    return len(r.json()) if r.ok else 0

def device_exists(device_id):
    r = requests.get(
        SUPABASE_URL + "/rest/v1/devices?device_id=eq." + device_id + "&select=device_id",
        headers=HEADERS()
    )
    return r.ok and len(r.json()) > 0

def add_device(device_id):
    requests.post(
        SUPABASE_URL + "/rest/v1/devices",
        headers=HEADERS(),
        json={
            "device_id": device_id,
            "joined": str(datetime.now()),
            "last_seen": str(datetime.now()),
            "visits": 1
        }
    )

def update_device(device_id):
    requests.patch(
        SUPABASE_URL + "/rest/v1/devices?device_id=eq." + device_id,
        headers=HEADERS(),
        json={"last_seen": str(datetime.now())}
    )

@app.route("/")
def index():
    device_id = request.cookies.get(COOKIE_NAME)
    count = get_count()
    if device_id and device_exists(device_id):
        update_device(device_id)
        return send_from_directory(".", "index.html")
    if count < MAX_DEVICES:
        new_id = str(uuid.uuid4())
        add_device(new_id)
        resp = make_response(send_from_directory(".", "index.html"))
        resp.set_cookie(
            COOKIE_NAME, new_id,
            max_age=60*60*24*365*10,
            httponly=True, samesite="Lax"
        )
        return resp
    html = BLOCK_HTML.replace("MAX_D", str(MAX_DEVICES)).replace("COUNT_D", str(count))
    return make_response(html, 403)

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
