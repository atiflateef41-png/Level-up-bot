# Made by BAXX
# LevelUp Legacy Web Bot (No Root) - Render Ready
# Warning: Use only on test accounts. Ban risk is high.

import os, json, asyncio, logging, time, threading, struct, socket, base64, hashlib
from flask import Flask, request, jsonify, render_template_string
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("levelup")

app = Flask(__name__)
ACCOUNTS_DB = {}

# ─── AES KEYS (From Legacy Project) ──────────────────────────
AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
AES_IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

# ─── Flask Dashboard UI ───────────────────────────────────
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LevelUp | Made by BAXX</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background: #0f172a; color: #e2e8f0; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        h1 { color: #38bdf8; font-size: 28px; }
        .card { background: #1e293b; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        .input-group { display: flex; gap: 10px; margin-top: 10px; }
        input[type="text"] { flex: 1; padding: 12px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: white; outline: none; }
        button { background: #38bdf8; color: #0f172a; border: none; padding: 12px 20px; border-radius: 6px; font-weight: bold; cursor: pointer; transition: 0.2s; }
        button:hover { background: #0ea5e9; }
        button.delete { background: #ef4444; color: white; padding: 6px 12px; font-size: 12px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #334155; }
        th { color: #94a3b8; font-size: 14px; text-transform: uppercase; }
        .status { padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
        .status.live { background: #166534; color: #4ade80; }
        .status.error { background: #7f1d1d; color: #f87171; }
        .status.loading { background: #854d0e; color: #facc15; }
        .stat-box { background: #1e293b; padding: 20px; border-radius: 10px; text-align: center; }
        .footer { text-align: center; margin-top: 40px; font-size: 14px; color: #38bdf8; font-weight: bold; }
        .logs { background: #000; color: #0f0; font-family: monospace; padding: 10px; border-radius: 6px; height: 150px; overflow-y: auto; font-size: 12px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 LevelUp Legacy Bot</h1>
            <div style="font-size: 12px; color: #64748b;">Made by BAXX</div>
        </div>

        <div class="card">
            <h2 style="font-size: 18px; margin-bottom: 10px;">Add Account (JWT Token)</h2>
            <div class="input-group">
                <input type="text" id="token-input" placeholder="Paste your JWT Token here...">
                <button onclick="addAccount()">Add & Connect</button>
            </div>
            <div id="msg" style="margin-top: 10px; font-size: 14px;"></div>
        </div>

        <div class="card">
            <h2 style="font-size: 18px; margin-bottom: 10px;">Monitored Accounts (Live)</h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Level</th>
                        <th>Status</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody id="acc-list">
                    <tr><td colspan="4" style="text-align:center; color:#64748b;">No accounts added yet.</td></tr>
                </tbody>
            </table>
        </div>

        <div class="card">
            <h2 style="font-size: 18px; margin-bottom: 10px;">Live Logs</h2>
            <div class="logs" id="log-box">Waiting for connection...</div>
        </div>

        <div class="footer">Made by BAXX</div>
    </div>

    <script>
        let logs = [];
        async function fetchStats() {
            try {
                const res = await fetch('/api/stats');
                const data = await res.json();
                
                const tbody = document.getElementById('acc-list');
                if(data.accounts.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#64748b;">No accounts added yet.</td></tr>';
                } else {
                    tbody.innerHTML = data.accounts.map(acc => `
                        <tr>
                            <td><code>${acc.id}</code></td>
                            <td>${acc.level}</td>
                            <td><span class="status ${acc.status}">${acc.status.toUpperCase()}</span></td>
                            <td><button class="delete" onclick="deleteAccount('${acc.id}')">Stop</button></td>
                        </tr>
                    `).join('');
                }
                
                if(data.logs && data.logs.length > 0) {
                    document.getElementById('log-box').innerHTML = data.logs.join('<br>');
                    document.getElementById('log-box').scrollTop = document.getElementById('log-box').scrollHeight;
                }
            } catch (e) { console.error(e); }
        }

        async function addAccount() {
            const token = document.getElementById('token-input').value.trim();
            if(!token) return alert("Paste a JWT Token!");
            
            document.getElementById('msg').innerText = "Connecting to server...";
            document.getElementById('msg').style.color = "#facc15";

            const res = await fetch('/api/add', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({token: token})
            });
            const data = await res.json();
            
            if(data.success) {
                document.getElementById('msg').innerText = "✅ Bot started! Check logs.";
                document.getElementById('msg').style.color = "#4ade80";
                document.getElementById('token-input').value = '';
                fetchStats();
            } else {
                document.getElementById('msg').innerText = "❌ " + data.error;
                document.getElementById('msg').style.color = "#f87171";
            }
        }

        async function deleteAccount(id) {
            await fetch('/api/delete', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id: id})
            });
            fetchStats();
        }

        fetchStats();
        setInterval(fetchStats, 2000);
    </script>
</body>
</html>
"""

# ─── Crypto & Socket Logic (Legacy) ───────────────────────
def aes_encrypt(payload, key, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(payload, AES.block_size))

def build_tcp_startup_packet(account_id, token, server_time, key, iv, region="IND"):
    uid_hex = f"{int(account_id):016x}"
    timestamp_hex = f"{int(server_time):08x}"
    encode_token = token.encode()
    encrypted_packet = aes_encrypt(encode_token, key, iv).hex()
    encrypted_packet_length = f"{len(encrypted_packet) // 2:08x}"
    prefix = '7114' # IND region
    return f"{prefix}{uid_hex}{timestamp_hex}00000000{encrypted_packet_length}{encrypted_packet}"

async def connect_to_ff(account_id, token, server_ip, region="IND"):
    global ACCOUNTS_DB
    acc_key = str(account_id)
    
    try:
        ACCOUNTS_DB[acc_key]["logs"].append(f"[*] Connecting to {server_ip}...")
        
        reader, writer = await asyncio.open_connection(server_ip, 443)
        
        # Fake JWT extract (token structure)
        server_time = int(time.time())
        packet_hex = build_tcp_startup_packet(account_id, token, server_time, AES_KEY, AES_IV, region)
        
        writer.write(bytes.fromhex(packet_hex))
        await writer.drain()
        
        ACCOUNTS_DB[acc_key]["logs"].append("[+] TCP handshake sent.")
        ACCOUNTS_DB[acc_key]["status"] = "live"
        
        # Send KeepAlive every 10s
        while True:
            await asyncio.sleep(10)
            keepalive_hex = "0214" # IND keepalive
            writer.write(bytes.fromhex(keepalive_hex))
            await writer.drain()
            ACCOUNTS_DB[acc_key]["logs"].append("[*] Keepalive sent.")
            
    except Exception as e:
        ACCOUNTS_DB[acc_key]["status"] = "error"
        ACCOUNTS_DB[acc_key]["logs"].append(f"[-] Connection error: {e}")

# ─── Flask Routes ─────────────────────────────────────────
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/stats')
def api_stats():
    accounts = []
    for aid, data in ACCOUNTS_DB.items():
        accounts.append({
            "id": aid,
            "level": data.get("level", "?"),
            "status": data.get("status", "loading")
        })
    logs = list(ACCOUNTS_DB.values())[-1]["logs"] if ACCOUNTS_DB else []
    return jsonify({"accounts": accounts, "logs": logs[-10:]}) # last 10 logs

@app.route('/api/add', methods=['POST'])
def api_add():
    data = request.json
    token = data.get('token')
    
    if not token or len(token) < 50:
        return jsonify({"success": False, "error": "Invalid JWT Token length."})

    # For this demo, fake a UID based on token
    account_id = str(abs(hash(token)))[:9]
    
    ACCOUNTS_DB[account_id] = {
        "token": token,
        "status": "loading",
        "level": "?",
        "logs": ["[*] Bot started.", "[*] Parsing token..."]
    }
    
    # Start background connection task
    # In a real setup, we'd call Garena's API to get the actual IP
    # Here we use the known IND IP
    threading.Thread(target=lambda: asyncio.run(connect_to_ff(account_id, token, "client.ind.freefiremobile.com")), daemon=True).start()
    
    return jsonify({"success": True})

@app.route('/api/delete', methods=['POST'])
def api_delete():
    data = request.json
    aid = data.get('id')
    if aid in ACCOUNTS_DB:
        del ACCOUNTS_DB[aid]
    return jsonify({"success": True})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)