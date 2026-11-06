"""A small local web interface: buttons for each step, logs shown live. Binds to 127.0.0.1 only."""
from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

STEPS = [
    ("doctor", "1. Check", "Looks at both phones and your Mac's free space.", []),
    ("pull", "2. Copy from Android", "Copies the chat backup (and media if ticked) over USB.", ["media"]),
    ("decrypt", "3. Decrypt", "Needs the 64-digit key from WhatsApp's encrypted backup.", ["key"]),
    ("backup", "4. Back up iPhone", "Takes a COMPLETE backup. Can take a long time.", ["password"]),
    ("build", "5. Build", "Adds the Android chats to a copy of the backup.", ["password", "media"]),
    ("check", "6. Safety check", "Proves nothing outside WhatsApp changed. Must say OK.", ["password"]),
    ("restore", "7. Restore to iPhone", "FULL restore. Archive your Finder backups first.", ["password", "confirm"]),
]
PAGE = """<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Chatferry</title><style>
:root{color-scheme:light dark;--bg:#fff;--fg:#1c1c1e;--card:#f2f2f7;--ac:#0a7a55;--warn:#b3261e}
@media(prefers-color-scheme:dark){:root{--bg:#111;--fg:#eee;--card:#1e1e22;--ac:#3ecf9a;--warn:#ff8a80}}
body{font:16px/1.5 system-ui;background:var(--bg);color:var(--fg);max-width:820px;margin:0 auto;padding:16px}
.card{background:var(--card);border-radius:12px;padding:14px 16px;margin:12px 0}h1{margin:.2em 0}
button{font:inherit;background:var(--ac);color:#fff;border:0;border-radius:8px;padding:8px 16px;cursor:pointer}
button:disabled{opacity:.4}input[type=password],input[type=text]{font:inherit;padding:6px;width:100%;box-sizing:border-box;margin:6px 0}
pre{background:#000;color:#9fe;padding:12px;border-radius:8px;min-height:160px;max-height:50vh;overflow:auto;white-space:pre-wrap}
.warn{color:var(--warn)}small{opacity:.75}</style>
<h1>Chatferry</h1>
<p class=warn><b>Experimental.</b> Moves Android WhatsApp chats into an iPhone that is already set up. Step 7 is a
full restore of your iPhone. Keep two Finder backups archived first. Not affiliated with WhatsApp or Apple.</p>
<div class=card><label>Backup password (only if your iPhone backups are encrypted)
<input type=password id=password autocomplete=off></label>
<label>64-digit WhatsApp key<input type=password id=key autocomplete=off></label>
<label><input type=checkbox id=media> Include media (slower, less tested)</label>
<small>Secrets stay in this browser tab and are passed to the local process only. Nothing is uploaded.</small></div>
<div id=steps></div><pre id=log>Ready.</pre>
<script>
const T=new URLSearchParams(location.search).get('t');const STEPS=__STEPS__;let busy=false;
const box=document.getElementById('steps');
STEPS.forEach(([id,title,desc,needs])=>{const d=document.createElement('div');d.className='card';
d.innerHTML=`<b>${title}</b><br><small>${desc}</small><br>`+(needs.includes('confirm')?
`<label><input type=checkbox id=confirm> I archived my Finder backups and understand this is a full restore</label><br>`:'')+
`<button id=b_${id}>Run</button>`;box.appendChild(d);
d.querySelector('button').onclick=async()=>{if(busy)return;
if(needs.includes('confirm')&&!document.getElementById('confirm').checked){alert('Tick the confirmation first.');return}
busy=true;document.querySelectorAll('button').forEach(b=>b.disabled=true);
await fetch('/run?t='+T,{method:'POST',body:JSON.stringify({step:id,password:password.value,key:key.value,media:media.checked})});poll()}});
async function poll(){const r=await (await fetch('/log?t='+T)).json();const l=document.getElementById('log');
l.textContent=r.log||'Ready.';l.scrollTop=l.scrollHeight;if(r.running){setTimeout(poll,800)}else{busy=false;
document.querySelectorAll('button').forEach(b=>b.disabled=false)}}
poll();
</script>"""


class State:
    log = ""
    running = False
    lock = threading.Lock()


def serve(work: Path, port: int = 8765) -> None:
    token = secrets.token_urlsafe(16)
    page = PAGE.replace("__STEPS__", json.dumps(STEPS))

    def run(step: str, data: dict) -> None:
        env = dict(os.environ, CHATFERRY_BACKUP_PASSWORD=data.get("password", ""), CHATFERRY_KEY=data.get("key", ""),
                   PYTHONUNBUFFERED="1")
        cmd = [sys.executable, "-m", "chatferry", "--work", str(work), step]
        if step in ("pull", "build") and not data.get("media"):
            cmd.append("--no-media")
        State.log = f"$ chatferry {step}\n"
        proc = subprocess.Popen(cmd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True)
        for chunk in iter(lambda: proc.stdout.read(1), ""):
            State.log += chunk
        State.log += f"\n[finished with code {proc.wait()}]"
        State.running = False

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def ok(self, body: bytes, kind="text/html"):
            self.send_response(200)
            self.send_header("Content-Type", kind + "; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)

        def auth(self) -> bool:
            if parse_qs(urlparse(self.path).query).get("t") != [token]:
                self.send_error(403)
                return False
            return True

        def do_GET(self):
            if not self.auth():
                return
            if urlparse(self.path).path == "/log":
                self.ok(json.dumps({"log": State.log[-60000:], "running": State.running}).encode(), "application/json")
            else:
                self.ok(page.encode())

        def do_POST(self):
            if not self.auth():
                return
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            step = data.get("step")
            with State.lock:
                if State.running or step not in {s[0] for s in STEPS}:
                    return self.send_error(409)
                State.running = True
            threading.Thread(target=run, args=(step, data), daemon=True).start()
            self.ok(b"{}", "application/json")

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/?t={token}"
    print(f"Chatferry is open at {url}\nPress Ctrl+C here to stop it.")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
