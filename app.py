from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_socketio import SocketIO, emit
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import sqlite3
import re
import random
import json
from threading import Lock
from models import create_table_resultado
import os

db_lock = Lock()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

DB_FILE = "banco.db"
create_table_resultado()
socketio = SocketIO(app, cors_allowed_origins="*")


# -----------------------------
# Banco de dados
# -----------------------------
def connect_data():
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn




def create_tables():
    conn = connect_data()
    cursor = conn.cursor()

    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            estado TEXT,
            municipio TEXT,
            cargo TEXT NOT NULL,
            telefone TEXT
        )
    """)

    conn.commit()
    conn.close()


def create_table_sorteio():
    conn = connect_data()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sorteio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT NOT NULL UNIQUE,
            estado TEXT NOT NULL,
            municipio TEXT NOT NULL,
            cargo TEXT NOT NULL,
            criado DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


# Garante que todas as tabelas existem ao iniciar
create_tables()
create_table_sorteio()


def create_admin_user():
    conn = connect_data()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ?", ("admin",))
    user = cursor.fetchone()

    if not user:
        senha_hash = generate_password_hash("admin123")
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            ("admin", senha_hash)
        )
    conn.commit()
    conn.close()


create_admin_user()


# -----------------------------
# Proteção de login
# -----------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Faça login para acessar esta página.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# -----------------------------
# Login / Logout
# -----------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = connect_data()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash("Login realizado com sucesso.")
            return redirect(url_for('admin'))
        else:
            flash("Usuário ou senha incorretos.")
            return redirect(url_for('login'))

    return render_template("login.html")


@app.route('/logout')
def logout():
    session.clear()
    flash("Você saiu da sessão.")
    return redirect(url_for('login'))


# -----------------------------
# Editar participante
# FIX: @login_required deve vir DEPOIS de @app.route
# FIX: consulta usava "name" em vez de "nome"
# -----------------------------
@app.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar(id):
    conn = connect_data()
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        estado = request.form.get("estado", "").strip()
        municipio = request.form.get("municipio", "").strip()
        cargo = request.form.get("cargo", "").strip()
        telefone = re.sub(r"\D", "", request.form.get("telefone", ""))

        erros = []

        if not name:
            erros.append("Nome é obrigatório.")
        if not estado:
            erros.append("Estado é obrigatório.")
        if not municipio:
            erros.append("Município é obrigatório.")
        if not cargo:
            erros.append("Cargo é obrigatório.")
        if not re.match(r"^\d{10,11}$", telefone):
            erros.append("Telefone inválido. Informe 10 ou 11 números com DDD.")

        if erros:
            for erro in erros:
                flash(erro, "danger")

            participant = {
                "id": id,
                "nome": name,
                "estado": estado,
                "municipio": municipio,
                "cargo": cargo,
                "telefone": request.form.get("telefone", "").strip()
            }

            conn.close()
            return render_template("editar.html", participant=participant)

        cursor.execute("""
            UPDATE clientes
            SET nome = ?, estado = ?, municipio = ?, cargo = ?, telefone = ?
            WHERE id = ?
        """, (name, estado, municipio, cargo, telefone, id))

        conn.commit()
        conn.close()

        flash("Participante atualizado com sucesso.", "success")
        return redirect(url_for("admin"))

    # FIX: coluna era "name", corrigido para "nome"
    participant = cursor.execute("""
        SELECT id, nome, estado, municipio, cargo, telefone
        FROM clientes
        WHERE id = ?
    """, (id,)).fetchone()

    conn.close()

    if not participant:
        flash("Participante não encontrado.", "danger")
        return redirect(url_for("admin"))

    return render_template("editar.html", participant=participant)


# -----------------------------
# Deletar em massa
# FIX: agora executa o DELETE de fato
# FIX: @login_required na ordem correta
# -----------------------------
@app.route("/deletar-massa", methods=["POST"])
@login_required
def deletar_massa():
    ids = request.form.getlist("ids")

    if not ids:
        flash("Nenhum registro selecionado.", "warning")
        return redirect(url_for("admin"))

    conn = connect_data()
    cursor = conn.cursor()

    placeholders = ",".join("?" for _ in ids)
    cursor.execute(f"DELETE FROM sorteio WHERE id IN ({placeholders})", ids)

    conn.commit()
    conn.close()

    flash(f"{cursor.rowcount} registro(s) excluído(s).", "success")
    return redirect(url_for("admin"))


# -----------------------------
# Página inicial / cadastro
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        nome = request.form.get("name", "").strip()
        telefone = re.sub(r"\D", "", request.form.get("telefone", ""))
        estado = request.form.get("estado", "").strip()
        municipio = request.form.get("municipio", "").strip()
        cargo = request.form.get("cargo", "").strip()

        erros = []

        if not nome:
            erros.append("Nome obrigatório.")
        if not cargo:
            erros.append("Cargo obrigatório.")
        if not re.match(r"^\d{10,11}$", telefone):
            erros.append("Telefone inválido. Informe 10 ou 11 números.")

        if erros:
            for erro in erros:
                flash(erro)
            return render_template("index.html")

        conn = connect_data()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO clientes (nome, estado, municipio, cargo, telefone)
            VALUES (?, ?, ?, ?, ?)
        """, (nome, estado, municipio, cargo, telefone))

        conn.commit()
        conn.close()

        return redirect(url_for("sucesso", nome=nome))

    return render_template("index.html")


@app.route("/sucesso")
def sucesso():
    nome = request.args.get("nome", "")
    return render_template("sucesso.html", nome=nome)


# -----------------------------
# Admin / lista participantes
# -----------------------------
@app.route("/admin")
@login_required
def admin():
    conn = connect_data()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nome, telefone, estado, municipio, cargo
        FROM sorteio
        ORDER BY id
    """)
    participantes = cursor.fetchall()

    secretarios_educacao = cursor.execute("""
        SELECT COUNT(*) FROM sorteio
        WHERE LOWER(cargo) LIKE '%secretário de educação%'
           OR LOWER(cargo) LIKE '%secretario de educacao%'
    """).fetchone()[0]

    prefeitos = cursor.execute("""
        SELECT COUNT(*) FROM sorteio
        WHERE LOWER(cargo) LIKE '%prefeito%'
    """).fetchone()[0]

    diretores = cursor.execute("""
        SELECT COUNT(*) FROM sorteio
        WHERE LOWER(cargo) LIKE '%diretor%'
    """).fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        participantes=participantes,
        secretarios_educacao=secretarios_educacao,
        prefeitos=prefeitos,
        diretores=diretores
    )


# -----------------------------
# Página de sorteio
# FIX: era GET-only mas tentava checar POST — corrigido para aceitar POST também
# -----------------------------
@app.route("/pagina-sorteio", methods=["GET", "POST"])
@login_required
def pagina_sorteio():
    if request.method == "POST":
        nome = request.form.get("name", "").strip()
        telefone = request.form.get("telefone", "").strip()
        estado = request.form.get("estado", "").strip()
        municipio = request.form.get("municipio", "").strip()
        cargo = request.form.get("cargo", "").strip()

        conn = connect_data()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sorteio (nome, telefone, estado, municipio, cargo)
            VALUES (?, ?, ?, ?, ?)
        """, (nome, telefone, estado, municipio, cargo))

        conn.commit()
        conn.close()

        return redirect(url_for("telao"))

    return render_template("sorteio.html")


# -----------------------------
# API - listar participantes
# FIX: @login_required na ordem correta
# FIX: filtro de cargo agora usa o parâmetro recebido
# -----------------------------
@app.route("/api/participantes", methods=["GET"])
@login_required
def api_participantes():
    cargo = request.args.get("cargo", "").strip()

    conn = connect_data()
    cursor = conn.cursor()

    if cargo:
        participantes = cursor.execute("""
            SELECT * FROM clientes WHERE cargo = ?
        """, (cargo,)).fetchall()
    else:
        participantes = cursor.execute("""
            SELECT * FROM clientes
        """).fetchall()

    conn.close()

    resultado = [
        {
            "id": p["id"],
            "nome": p["nome"],
            "estado": p["estado"],
            "municipio": p["municipio"],
            "cargo": p["cargo"],
            "telefone": p["telefone"]
        }
        for p in participantes
    ]

    return jsonify(resultado)


# -----------------------------
# API - sorteio DME (Secretário de Educação)
# FIX: @login_required na ordem correta
# -----------------------------
@app.route("/sortear-dme", methods=["POST"])
@login_required
def sortear_dme():
    conn = connect_data()
    cursor = conn.cursor()

    participantes = cursor.execute("""
        SELECT id, nome, estado, municipio, cargo, telefone
        FROM sorteio
        WHERE LOWER(cargo) = LOWER(?)
    """, ("Secretário de Educação",)).fetchall()

    if not participantes:
        conn.close()
        return jsonify({"erro": "Nenhum Secretário de Educação encontrado."}), 404

    sorteado = random.choice(participantes)

    participantes_json = [
        {
            "id": p["id"],
            "nome": p["nome"],
            "estado": p["estado"],
            "municipio": p["municipio"],
            "cargo": p["cargo"],
            "telefone": p["telefone"]
        }
        for p in participantes
    ]

    sorteado_json = {
        "id": sorteado["id"],
        "nome": sorteado["nome"],
        "estado": sorteado["estado"],
        "municipio": sorteado["municipio"],
        "cargo": sorteado["cargo"],
        "telefone": sorteado["telefone"]
    }

    payload = {
        "tipo": "secretario_educacao",
        "participantes": participantes_json,
        "sorteado": sorteado_json,
        "total_participantes": len(participantes)
    }

    cursor.execute("""
        INSERT INTO sorteio_resultado (dados)
        VALUES (?)
    """, (json.dumps(payload, ensure_ascii=False),))

    conn.commit()
    id_sorteio = cursor.lastrowid
    conn.close()

    evento = {"id": id_sorteio, **payload}
    socketio.emit("novo_sorteio", evento)

    return jsonify({"ok": True, "id": id_sorteio, "sorteado": sorteado_json})


# -----------------------------
# API - sorteio geral
# FIX: @login_required na ordem correta
# -----------------------------
@app.route("/sortear", methods=["POST"])
@login_required
def sortear():
    conn = connect_data()
    cursor = conn.cursor()

    participantes = cursor.execute("""
        SELECT id, nome, estado, municipio, cargo, telefone
        FROM sorteio
    """).fetchall()

    if not participantes:
        conn.close()
        return jsonify({"erro": "Nenhum participante encontrado."}), 404

    sorteado = random.choice(participantes)

    participantes_json = [
        {
            "id": p["id"],
            "nome": p["nome"],
            "estado": p["estado"],
            "municipio": p["municipio"],
            "cargo": p["cargo"],
            "telefone": p["telefone"]
        }
        for p in participantes
    ]

    sorteado_json = {
        "id": sorteado["id"],
        "nome": sorteado["nome"],
        "estado": sorteado["estado"],
        "municipio": sorteado["municipio"],
        "cargo": sorteado["cargo"],
        "telefone": sorteado["telefone"]
    }

    payload = {
        "tipo": "normal",
        "participantes": participantes_json,
        "sorteado": sorteado_json,
        "total_participantes": len(participantes)
    }

    cursor.execute("""
        INSERT INTO sorteio_resultado (dados)
        VALUES (?)
    """, (json.dumps(payload, ensure_ascii=False),))

    conn.commit()
    id_sorteio = cursor.lastrowid
    conn.close()

    evento = {"id": id_sorteio, **payload}
    socketio.emit("novo_sorteio", evento)

    return jsonify({"ok": True, "id": id_sorteio, "sorteado": sorteado_json})


@app.route("/tela-sorteio/<int:id>")
@login_required
def tela_sorteio(id):
    return render_template("tela-sorteio.html", id_sorteio=id)


# -----------------------------
# Buscar sorteio por ID
# FIX: @login_required na ordem correta
# FIX: buscava em "sorteio" (sem coluna dados), corrigido para "sorteio_resultado"
# -----------------------------
@app.route("/sorteio/<int:id>")
@login_required
def get_sorteio(id):
    conn = connect_data()
    cursor = conn.cursor()

    row = cursor.execute("""
        SELECT dados FROM sorteio_resultado
        WHERE id = ?
    """, (id,)).fetchone()

    conn.close()

    if not row:
        return jsonify({"erro": "Sorteio não encontrado"}), 404

    dados = json.loads(row["dados"])
    sorteado = dados.get("sorteado", {})

    return jsonify({
        "nome": sorteado.get("nome", ""),
        "cargo": sorteado.get("cargo", ""),
        "municipio": sorteado.get("municipio", ""),
        "estado": sorteado.get("estado", ""),
        "telefone": sorteado.get("telefone", "")
    })


@app.route("/api/sorteio/<int:id>")
@login_required
def api_sorteio(id):
    conn = connect_data()
    cursor = conn.cursor()

    row = cursor.execute("""
        SELECT dados FROM sorteio_resultado
        WHERE id = ?
    """, (id,)).fetchone()

    conn.close()

    if not row:
        return jsonify({"erro": "Sorteio não encontrado"}), 404

    return jsonify(json.loads(row["dados"]))


# -----------------------------
# Cadastro sorteio (tela pública)
# FIX: removido conn.close() duplo e return inacessível
# -----------------------------
@app.route("/sorteio-tela", methods=["GET", "POST"])
def cadastro_sorteio():
    if request.method == "POST":
        nome = request.form.get("name", "").strip()
        telefone = request.form.get("telefone", "").strip()
        estado = request.form.get("estado", "").strip()
        municipio = request.form.get("municipio", "").strip()
        cargo = request.form.get("cargo", "").strip()

        try:
            conn = connect_data()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO sorteio (nome, telefone, estado, municipio, cargo)
                VALUES (?, ?, ?, ?, ?)
            """, (nome, telefone, estado, municipio, cargo))

            conn.commit()
            return jsonify({"sucesso": True})

        except Exception as e:
            return jsonify({"erro": str(e)}), 500

        finally:
            conn.close()  # só aqui, sem duplicata

    return render_template("sorteio.html")


# -----------------------------
# Buscar participantes
# FIX: @login_required na ordem correta
# -----------------------------
@app.route("/buscar-participantes", methods=["GET"])
@login_required
def buscar_participantes():
    conn = connect_data()
    cursor = conn.cursor()

    participantes = cursor.execute("""
        SELECT nome, telefone, cargo, municipio, estado
        FROM sorteio
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return jsonify([
        {
            "nome": p["nome"],
            "telefone": p["telefone"],
            "cargo": p["cargo"],
            "municipio": p["municipio"],
            "estado": p["estado"]
        }
        for p in participantes
    ])


# -----------------------------
# Telão
# -----------------------------
@app.route("/telao")
def telao():
    return render_template("tela-sorteio.html")


@app.route("/telao/<int:id_sorteio>")
@login_required
def telao_id(id_sorteio):
    return render_template("tela-sorteio.html", id_sorteio=id_sorteio)


# -----------------------------
# Último sorteio
# FIX: @login_required na ordem correta
# -----------------------------
@app.route("/api/ultimo-sorteio")
@login_required
def api_ultimo_sorteio():
    conn = connect_data()
    cursor = conn.cursor()

    row = cursor.execute("""
        SELECT id, dados
        FROM sorteio_resultado
        ORDER BY id DESC
        LIMIT 1
    """).fetchone()

    conn.close()

    if not row:
        return jsonify({"ok": False, "mensagem": "Nenhum sorteio realizado ainda."}), 200

    dados = json.loads(row["dados"])
    dados["id"] = row["id"]

    return jsonify(dados)


# -----------------------------
# Rodar o app
# -----------------------------
if __name__ == "__main__":
    print("🚀 Iniciando servidor...")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)