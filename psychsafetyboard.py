import streamlit as st
import sqlite3
import datetime
import json
import hashlib
import base64
from cryptography.fernet import Fernet
import matplotlib.pyplot as plt

# =================================
# PAGE CONFIG — DARK THEME
# =================================
st.set_page_config(
    page_title="Personal Board",
    page_icon="🧭",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# =================================
# LANGUAGES
# =================================
TEXT = {
    "fr": {
        "title": "🧭 Board personnel",
        "auth": "Authentification",
        "login": "Login",
        "password": "Mot de passe",
        "signin": "Se connecter",
        "signup": "Créer un compte",
        "notice": (
            "🔐 **Sécurité & confidentialité**\n\n"
            "- Utilise un **login et mot de passe dédiés**, différents de tes comptes habituels.\n"
            "- Aucun email n’est collecté.\n"
            "- Aucune donnée n’est exploitée ou transmise.\n"
            "- Ce board est un **outil personnel de visualisation**.\n\n"
            "**Chiffrement** :\n"
            "- Données chiffrées localement (AES / Fernet).\n"
            "- Le serveur ne stocke que des données chiffrées.\n"
            "- Sans ton mot de passe, elles sont illisibles."
        ),
        "today": "États du jour",
        "history": "Historique",
        "export": "📤 Export chiffré",
        "import": "📥 Import chiffré",
        "mobile": "Mode mobile",
        "logout": "Se déconnecter",
        "connected": "Connecté en tant que"
    },
    "en": {
        "title": "🧭 Personal board",
        "auth": "Authentication",
        "login": "Username",
        "password": "Password",
        "signin": "Sign in",
        "signup": "Create account",
        "notice": (
            "🔐 **Security & privacy**\n\n"
            "- Use a **dedicated username and password**, different from usual accounts.\n"
            "- No email is collected.\n"
            "- No data is shared or exploited.\n"
            "- This board is a **personal visualization tool**.\n\n"
            "**Encryption**:\n"
            "- Data encrypted locally (AES / Fernet).\n"
            "- Server stores only encrypted data.\n"
            "- Without your password, data is unreadable."
        ),
        "today": "Today’s states",
        "history": "History",
        "export": "📤 Encrypted export",
        "import": "📥 Encrypted import",
        "mobile": "Mobile mode",
        "logout": "Log out",
        "connected": "Logged in as"
    },
    "eo": {
        "title": "🧭 Persona Tabulo",
        "auth": "Aŭtentikigo",
        "login": "Uzantnomo",
        "password": "Pasvorto",
        "signin": "Ensaluti",
        "signup": "Krei konton",
        "notice": (
            "🔐 **Sekureco & privateco**\n\n"
            "- Uzu **apartajn ensalutilojn**, malsamajn ol viaj kutimaj.\n"
            "- Neniu retpoŝto kolektiĝas.\n"
            "- Neniuj datumoj estas uzataj.\n"
            "- Persona vida ilo.\n\n"
            "**Ĉifrado**:\n"
            "- Loka AES / Fernet ĉifrado.\n"
            "- Nur ĉifritaj datumoj stokitaj.\n"
            "- Sen pasvorto, nelegebla."
        ),
        "today": "Hodiaŭaj ŝtatoj",
        "history": "Historio",
        "export": "📤 Ĉifrita eksporto",
        "import": "📥 Ĉifrita importo",
        "mobile": "Poŝtelefona reĝimo",
        "logout": "Elsaluti",
        "connected": "Ensalutis kiel"
    }
}

# =================================
# SESSION INIT
# =================================
if "lang" not in st.session_state:
    st.session_state.lang = "fr"
if "mobile" not in st.session_state:
    st.session_state.mobile = False
if "user" not in st.session_state:
    st.session_state.user = None
if "crypto" not in st.session_state:
    st.session_state.crypto = None

lang = st.selectbox(
    "🌍 Language / Langue / Lingvo",
    ["fr", "en", "eo"],
    format_func=lambda x: {"fr": "Français", "en": "English", "eo": "Esperanto"}[x]
)
st.session_state.lang = lang
T = TEXT[lang]

st.session_state.mobile = st.checkbox(T["mobile"], value=st.session_state.mobile)

# =================================
# PARAMETERS
# =================================
PARAMS = {
    "Climat": {
        "label": {"fr": "🌦 Climat du jour", "en": "🌦 Daily climate", "eo": "🌦 Hodiaŭa klimato"},
        "states": {
            1: {"fr": "🌫 Tendu", "en": "🌫 Tense", "eo": "🌫 Streĉita"},
            2: {"fr": "🌥 Neutre", "en": "🌥 Neutral", "eo": "🌥 Neŭtrala"},
            3: {"fr": "☀️ Chaleureux", "en": "☀️ Warm", "eo": "☀️ Varma"}
        },
        "color": "#5DA9E9"
    },
    "Charge": {
        "label": {"fr": "🧠 Charge mentale", "en": "🧠 Mental load", "eo": "🧠 Mensa ŝarĝo"},
        "states": {
            1: {"fr": "🪨 Lourde", "en": "🪨 Heavy", "eo": "🪨 Peza"},
            2: {"fr": "⚖️ Gérable", "en": "⚖️ Manageable", "eo": "⚖️ Regulebla"},
            3: {"fr": "🌬 Légère", "en": "🌬 Light", "eo": "🌬 Malpeza"}
        },
        "color": "#E15554"
    },
    "Autonomie": {
        "label": {"fr": "🧭 Autonomie", "en": "🧭 Autonomy", "eo": "🧭 Aŭtonomio"},
        "states": {
            1: {"fr": "🔒 Subie", "en": "🔒 Constrained", "eo": "🔒 Limigita"},
            2: {"fr": "🧩 Partagée", "en": "🧩 Shared", "eo": "🧩 Komuna"},
            3: {"fr": "🕊 Pleine", "en": "🕊 Full", "eo": "🕊 Plena"}
        },
        "color": "#3BB273"
    },
    "Parole": {
        "label": {"fr": "🗣 Paroles libres", "en": "🗣 Free speech", "eo": "🗣 Libera parolo"},
        "states": {
            1: {"fr": "🤐 Retenues", "en": "🤐 Restrained", "eo": "🤐 Retenitaj"},
            2: {"fr": "💬 Prudentes", "en": "💬 Cautious", "eo": "💬 Prudentaj"},
            3: {"fr": "📣 Libres", "en": "📣 Free", "eo": "📣 Liberaj"}
        },
        "color": "#9B7EDE"
    }
}

# =================================
# DB & CRYPTO
# =================================
conn = sqlite3.connect("data.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS entries (username TEXT, date TEXT, payload BLOB, PRIMARY KEY (username, date))")
conn.commit()

def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()
def derive_key(p): return Fernet(base64.urlsafe_b64encode(hashlib.sha256(p.encode()).digest()))
def encrypt(d, f): return f.encrypt(json.dumps(d).encode())
def decrypt(b, f): return json.loads(f.decrypt(b).decode())

# =================================
# AUTH
# =================================
st.title(T["title"])

if not st.session_state.user:
    st.subheader(T["auth"])
    st.info(T["notice"])

    u = st.text_input(T["login"])
    p = st.text_input(T["password"], type="password")

    if st.button(T["signin"]):
        cur.execute("SELECT password_hash FROM users WHERE username=?", (u,))
        r = cur.fetchone()
        if r and r[0] == hash_password(p):
            st.session_state.user = u
            st.session_state.crypto = derive_key(p)
            st.rerun()
        else:
            st.error("Invalid credentials")

    if st.button(T["signup"]):
        try:
            cur.execute("INSERT INTO users VALUES (?,?)", (u, hash_password(p)))
            conn.commit()
            st.success("Account created")
        except:
            st.error("User already exists")

    st.stop()

# =================================
# USER CONTEXT
# =================================
user = st.session_state.user
crypto = st.session_state.crypto
today = datetime.date.today().isoformat()

st.caption(f"{T['connected']} **{user}**")

# =================================
# LOAD TODAY
# =================================
cur.execute("SELECT payload FROM entries WHERE username=? AND date=?", (user, today))
row = cur.fetchone()
state = decrypt(row[0], crypto) if row else {k: 1 for k in PARAMS}

# =================================
# UI
# =================================
st.subheader(T["today"])
for k, cfg in PARAMS.items():
    if st.session_state.mobile:
        state[k] = st.radio(
            cfg["label"][lang],
            [1, 2, 3],
            index=state[k]-1,
            format_func=lambda x, c=cfg: c["states"][x][lang],
            key=k
        )
    else:
        state[k] = st.segmented_control(
            cfg["label"][lang],
            [1, 2, 3],
            default=state[k],
            format_func=lambda x, c=cfg: c["states"][x][lang],
            key=k
        )

cur.execute("INSERT OR REPLACE INTO entries VALUES (?,?,?)", (user, today, encrypt(state, crypto)))
conn.commit()

# =================================
# EXPORT / IMPORT (CORRIGÉ)
# =================================
cur.execute("SELECT date, payload FROM entries WHERE username=?", (user,))
rows = cur.fetchall()

export_data = {
    date: base64.b64encode(payload).decode("utf-8")
    for date, payload in rows
}

export_blob = encrypt(export_data, crypto)

st.download_button(T["export"], export_blob, file_name=f"{user}_board.enc")

uploaded = st.file_uploader(T["import"])
if uploaded:
    try:
        imported = decrypt(uploaded.read(), crypto)
        for date, payload_b64 in imported.items():
            payload = base64.b64decode(payload_b64)
            cur.execute("INSERT OR REPLACE INTO entries VALUES (?,?,?)", (user, date, payload))
        conn.commit()
        st.success("Import OK")
        st.rerun()
    except Exception as e:
        st.error("Import impossible")
        st.caption(str(e))

# =================================
# GRAPH
# =================================
st.subheader(T["history"])

cur.execute("""
SELECT date, payload FROM entries
WHERE username=?
ORDER BY date DESC
LIMIT 90
""", (user,))
rows = cur.fetchall()

dates = []
history = {k: [] for k in PARAMS}

for d, p in reversed(rows):
    data = decrypt(p, crypto)
    dates.append(d)
    for k in PARAMS:
        history[k].append(data[k])

plt.style.use("dark_background")
fig, ax = plt.subplots(figsize=(10, 4))

for k, cfg in PARAMS.items():
    ax.plot(dates, history[k], label=cfg["label"][lang], color=cfg["color"], linewidth=2, marker="o")

ax.set_ylim(0.5, 3.5)
ax.grid(alpha=0.2)
ax.legend(frameon=False)
ax.tick_params(axis="x", rotation=45)

st.pyplot(fig)

# =================================
# LOGOUT
# =================================
if st.button(T["logout"]):
    st.session_state.user = None
    st.session_state.crypto = None
    st.rerun()

