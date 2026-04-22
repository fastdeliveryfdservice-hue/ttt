 from flask import Flask, request, redirect, session
import sqlite3
import random
import string
import datetime

app = Flask(__name__)
app.secret_key = "fds_secure_key_2026"

DB = "fds.db"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS parcels (
        tracking TEXT PRIMARY KEY,
        sender TEXT,
        sender_location TEXT,
        receiver TEXT,
        receiver_address TEXT,
        status_index INTEGER,
        created TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- TRACKING NUMBER ----------------
def generate_tracking():
    return "FDS" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

# ---------------- STATUS ----------------
STAGES = [
    "Order Received 📦",
    "Processing at Warehouse 🏬",
    "Package Dispatched 📤",
    "In Transit ✈️",
    "Arrived at Hub 🏢",
    "With Courier 👷",
    "Out for Delivery 🚚",
    "Delivered ✅"
]

# ---------------- HOME PAGE ----------------
@app.route("/", methods=["GET", "POST"])
def home():
    result = ""

    if request.method == "POST":
        t = request.form["tracking"]

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT * FROM parcels WHERE tracking=?", (t,))
        p = c.fetchone()
        conn.close()

        if not p:
            result = "<h3 style='color:red'>Tracking Not Found</h3>"
        else:
            timeline = ""

            for i, step in enumerate(STAGES):
                color = "#00ff88" if i <= p[5] else "#444"
                live = "🔥 LIVE" if i == p[5] else ""

                timeline += f"""
                <div style="padding:10px;margin:5px;border-left:4px solid {color};background:#111;">
                    <b>{step}</b> {live}
                </div>
                """

            result = f"""
            <div style="background:#0f172a;color:white;padding:20px;margin-top:20px;text-align:left;">
                <h2>Tracking: {p[0]}</h2>

                <p><b>Status:</b> {STAGES[p[5]]}</p>

                <hr>

                <p><b>Sender:</b> {p[1]}</p>
                <p><b>Sender Location:</b> {p[2]}</p>

                <p><b>Receiver:</b> {p[3]}</p>
                <p><b>Receiver Address:</b> {p[4]}</p>

                <hr>

                <h3>Shipment Timeline</h3>
                {timeline}
            </div>
            """

    return f"""
<html>
<head>
<title>Fast Delivery Service</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>
body {{
    font-family: Arial;
    background: #0f172a;
    color: white;
    text-align: center;
}}

input {{
    width: 80%;
    padding: 12px;
    margin: 5px;
}}

button {{
    padding: 12px;
    background: orange;
    border: none;
    font-weight: bold;
}}
</style>
</head>

<body>

<h1>🚚 Fast Delivery Service</h1>
<p>Global Tracking System</p>

<form method="POST">
<input name="tracking" placeholder="Enter Tracking Number"><br><br>
<button>TRACK</button>
</form>

{result}

</body>
</html>
"""

# ---------------- ADMIN LOGIN ----------------
@app.route("/fds-secure-admin", methods=["GET", "POST"])
def admin():
    error = ""

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if email == "fastdeliveryfdservice@gmail.com" and password == "Dazzyrams":
            session["admin"] = True
            return redirect("/dashboard")
        else:
            error = "Invalid login"

    return f"""
    <h2>Admin Login</h2>

    <form method="POST">
        <input name="email" placeholder="Email"><br><br>
        <input name="password" type="password" placeholder="Password"><br><br>
        <button>Login</button>
    </form>

    <p style="color:red">{error}</p>
    """

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/fds-secure-admin")

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM parcels")
    data = c.fetchall()
    conn.close()

    out = ""

    for d in data:
        out += f"""
        <p>
        <b>{d[0]}</b> | {STAGES[d[5]]}
        <a href="/update/{d[0]}">Update</a>
        </p>
        """

    return f"""
    <h1>Admin Dashboard</h1>

    <a href="/create"><button>Create Parcel</button></a>
    <a href="/logout"><button style="background:red;color:white;">Logout</button></a>

    <hr>

    {out}
    """

# ---------------- CREATE PARCEL ----------------
@app.route("/create", methods=["GET", "POST"])
def create():
    if not session.get("admin"):
        return redirect("/fds-secure-admin")

    if request.method == "POST":
        t = generate_tracking()

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        c.execute("""
        INSERT INTO parcels VALUES (?,?,?,?,?,?,?)
        """, (
            t,
            request.form["sender"],
            request.form["sender_location"],
            request.form["receiver"],
            request.form["receiver_address"],
            0,
            str(datetime.datetime.now())
        ))

        conn.commit()
        conn.close()

        return f"<h2>Tracking Created: {t}</h2>"

    return """
    <h2>Create Parcel</h2>

    <form method="POST">
    Sender:<input name="sender"><br>
    Sender Location:<input name="sender_location"><br><br>

    Receiver:<input name="receiver"><br>
    Receiver Address:<input name="receiver_address"><br><br>

    <button>Create Parcel</button>
    </form>
    """

# ---------------- UPDATE STATUS ----------------
@app.route("/update/<tracking>")
def update(tracking):
    if not session.get("admin"):
        return redirect("/fds-secure-admin")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT status_index FROM parcels WHERE tracking=?", (tracking,))
    row = c.fetchone()

    if row and row[0] < len(STAGES) - 1:
        c.execute("UPDATE parcels SET status_index=? WHERE tracking=?",
                  (row[0] + 1, tracking))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
