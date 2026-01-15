import os
import json
import hashlib
from functools import wraps
from flask import Flask, request, session, redirect, jsonify, send_from_directory

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PAGES_DIR = os.path.join(BASE_DIR, "pages")
CORE_DIR = os.path.join(BASE_DIR, "core")

USERS_FILE    = os.path.join(DATA_DIR, "users.json")
PROGRESS_FILE = os.path.join(DATA_DIR, "progress.json")
LEVELS_FILE   = os.path.join(DATA_DIR, "levels.json")

SECRET_KEY = "umbra-no-perdona"

app = Flask(__name__)
app.secret_key = SECRET_KEY

# =====================================================
# UTILIDADES
# =====================================================

def load_json(path, default):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def hash_pw(text):
    return hashlib.sha256(text.encode()).hexdigest()

users    = load_json(USERS_FILE, {})
progress = load_json(PROGRESS_FILE, {})
levels   = load_json(LEVELS_FILE, {})

# =====================================================
# SESIÓN
# =====================================================

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect("/")
        return fn(*args, **kwargs)
    return wrapper

def get_state(user):
    return progress.setdefault(user, {})

def set_last_page(user, path):
    state = get_state(user)
    state["last_page"] = path
    save_json(PROGRESS_FILE, progress)

# =====================================================
# ENTRY (RUTA RAÍZ CORREGIDA)
# =====================================================

@app.route("/")
def root():
    # Punto de entrada oficial del juego
    return send_from_directory(
        os.path.join(PAGES_DIR, "entry"),
        "index.html"
    )

# =====================================================
# REGISTRO / LOGIN
# =====================================================

@app.route("/register", methods=["POST"])
def register():
    user = request.form.get("user", "").lower().strip()
    pw   = request.form.get("pass", "")

    if not user or not pw:
        return "Datos incompletos", 400

    if user in users:
        return "Usuario ya existe", 400

    users[user] = hash_pw(pw)
    save_json(USERS_FILE, users)

    progress[user] = {}
    save_json(PROGRESS_FILE, progress)

    session["user"] = user
    return jsonify(success=True)

@app.route("/login", methods=["POST"])
def login():
    user = request.form.get("user", "").lower().strip()
    pw   = request.form.get("pass", "")

    if user in users and users[user] == hash_pw(pw):
        session["user"] = user
        return jsonify(success=True)

    return "Credenciales incorrectas", 403

@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/")

# =====================================================
# VALIDACIÓN DE NIVELES
# =====================================================

@app.route("/api/validate", methods=["POST"])
@login_required
def validate():
    data = request.get_json(force=True)
    level_id = data.get("level")
    user = session["user"]

    rule = levels.get(level_id)
    if not rule:
        return jsonify(ok=False)

    if "answer" in rule:
        answer = data.get("answer", "").strip().lower()
        if answer != rule["answer"].lower():
            return jsonify(ok=False)

    if rule.get("type") == "login":
        u = data.get("user", "").lower().strip()
        p = data.get("pass", "").lower().strip()
        if u != rule["user"] or p != rule["pass"]:
            return jsonify(ok=False)

    get_state(user)[level_id] = True
    save_json(PROGRESS_FILE, progress)

    return jsonify(ok=True, redirect=rule["next"])

# =====================================================
# CONTINUAR PARTIDA
# =====================================================

@app.route("/api/session_status")
def session_status():
    if "user" not in session:
        return jsonify(logged_in=False)

    user = session["user"]
    state = get_state(user)

    return jsonify(
        logged_in=True,
        last_page=state.get("last_page")
    )

# =====================================================
# SERVIR RECURSOS
# =====================================================

@app.route("/pages/<path:filename>")
@login_required
def pages(filename):
    user = session["user"]
    real_path = "/pages/" + filename
    set_last_page(user, real_path)
    return send_from_directory(PAGES_DIR, filename)

@app.route("/core/<path:filename>")
def core(filename):
    return send_from_directory(CORE_DIR, filename)

@app.route("/audio/<path:filename>")
@login_required
def audio(filename):
    return send_from_directory(os.path.join(CORE_DIR, "audio"), filename)

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    app.run(debug=True)
