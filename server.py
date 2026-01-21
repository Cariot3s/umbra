import os
import json
import hashlib
from functools import wraps
from flask import Flask, request, session, redirect, jsonify, send_from_directory

from sqlalchemy import (
    create_engine, Column, Integer, String,
    Boolean, ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, sessionmaker

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = os.path.join(BASE_DIR, "pages")
CORE_DIR = os.path.join(BASE_DIR, "core")

SECRET_KEY = "umbra-no-perdona"

app = Flask(__name__)
app.secret_key = SECRET_KEY

# =====================================================
# BASE DE DATOS (POSTGRESQL - RENDER)
# =====================================================

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no definida")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()
Base = declarative_base()

# =====================================================
# MODELOS
# =====================================================

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

class Progress(Base):
    __tablename__ = "progress"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    level_id = Column(String, nullable=False)
    completed = Column(Boolean, default=True)

class Level(Base):
    __tablename__ = "levels"
    id = Column(String, primary_key=True)
    data = Column(JSON, nullable=False)

Base.metadata.create_all(engine)

# =====================================================
# UTILIDADES
# =====================================================

def hash_pw(text):
    return hashlib.sha256(text.encode()).hexdigest()

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

def get_user():
    if "user" not in session:
        return None
    return db.query(User).filter_by(username=session["user"]).first()

def set_last_page(user, path):
    db.merge(Progress(
        user_id=user.id,
        level_id="__last_page__",
        completed=True
    ))
    db.commit()

# =====================================================
# ENTRY
# =====================================================

@app.route("/")
def root():
    return send_from_directory(
        os.path.join(PAGES_DIR, "entry"),
        "index.html"
    )

# =====================================================
# REGISTRO / LOGIN (MODIFICADO)
# =====================================================

@app.route("/register", methods=["POST"])
def register():
    user = request.form.get("user", "").lower().strip()
    pw   = request.form.get("pass", "")

    if not user or not pw:
        return "Datos incompletos", 400

    if db.query(User).filter_by(username=user).first():
        return "Usuario ya existe", 400

    db.add(User(username=user, password_hash=hash_pw(pw)))
    db.commit()

    session["user"] = user
    return jsonify(success=True)

@app.route("/login", methods=["POST"])
def login():
    user = request.form.get("user", "").lower().strip()
    pw   = request.form.get("pass", "")

    u = db.query(User).filter_by(username=user).first()
    if u and u.password_hash == hash_pw(pw):
        session["user"] = user
        return jsonify(success=True)

    return "Credenciales incorrectas", 403

@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/")

# =====================================================
# VALIDACIÓN DE NIVELES (MISMA LÓGICA)
# =====================================================

@app.route("/api/validate", methods=["POST"])
@login_required
def validate():
    data = request.get_json(force=True)
    level_id = data.get("level")

    user = get_user()
    if not user:
        return jsonify(ok=False)

    lvl = db.query(Level).filter_by(id=level_id).first()
    if not lvl:
        return jsonify(ok=False)

    rule = lvl.data

    if "answer" in rule:
        answer = data.get("answer", "").strip().lower()
        if answer != rule["answer"].lower():
            return jsonify(ok=False)

    if rule.get("type") == "login":
        u = data.get("user", "").lower().strip()
        p = data.get("pass", "").lower().strip()
        if u != rule["user"] or p != rule["pass"]:
            return jsonify(ok=False)

    db.merge(Progress(
        user_id=user.id,
        level_id=level_id,
        completed=True
    ))
    db.commit()

    return jsonify(ok=True, redirect=rule["next"])

# =====================================================
# CONTINUAR PARTIDA
# =====================================================

@app.route("/api/session_status")
def session_status():
    if "user" not in session:
        return jsonify(logged_in=False)

    return jsonify(
        logged_in=True,
        last_page=None
    )

# =====================================================
# SERVIR RECURSOS (SIN CAMBIOS)
# =====================================================

@app.route("/pages/<path:filename>")
@login_required
def pages(filename):
    return send_from_directory(PAGES_DIR, filename)

@app.route("/core/<path:filename>")
def core(filename):
    return send_from_directory(CORE_DIR, filename)

@app.route("/audio/<path:filename>")
@login_required
def audio(filename):
    return send_from_directory(os.path.join(CORE_DIR, "audio"), filename)

# =====================================================
# MAIN (RENDER USA GUNICORN)
# =====================================================

if __name__ == "__main__":
    app.run(debug=True)
