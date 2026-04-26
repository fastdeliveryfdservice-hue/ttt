from flask import Flask, request, render_template_string
import sqlite3
import random
import string
import os

app = Flask(__name__)
DB = "fds.db"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS parcels (
        tracking TEXT PRIMARY KEY,
        sender TEXT,
        receiver TEXT,
        status TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- TRACKING NUMBER ----------------
def generate_tracking():
    return "FDS" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

# ---------------- HOME TRACK PAGE ----------------
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
            result = f"""
            <div style="margin-top:20px;padding:20px;background:#222;color:white">
                <h2>Tracking: {p[0]}</h2>
                <p><b>Sender:</b> {p[1]}</p>
                <p><b>Receiver:</b> {p[2]}</p>
                <p><b>Status:</b> {p[3]}</p>
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
                background:#0f172a;
                color:white;
                text-align:center;
            }}
            input {{
                width:80%;
                padding:10px;
                border-radius:10px;
            }}
            button {{
                padding:10px;
                background:orange;
                border:none;
                border-radius:10px;
            }}
        </style>
    </head>
    <body>
        <h1>🚚 Fast Delivery Service</h1>

        <form method="POST">
            <input name="tracking" placeholder="Enter Tracking Number">
            <br><br>
            <button>TRACK</button>
        </form>

        {result}

    </body>
    </html>
    """

# ---------------- ADMIN CREATE ----------------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        tracking = generate_tracking()

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO parcels VALUES (?,?,?,?)",
                  (tracking,
                   request.form["sender"],
                   request.form["receiver"],
                   request.form["status"]))
        conn.commit()
        conn.close()

        return f"<h2>Created Tracking: {tracking}</h2>"

    return """
    <h2>Admin Panel</h2>
    <form method="POST">
        Sender:<br><input name="sender"><br><br>
        Receiver:<br><input name="receiver"><br><br>
        Status:<br><input name="status" value="Processing"><br><br>
        <button>Create Parcel</button>
    </form>
    """

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
