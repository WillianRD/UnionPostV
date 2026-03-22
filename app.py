from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import sqlite3
import re
import random

app = Flask(__name__)
app.secret_key = 'uma_chave_super_secreta'

DB_FILE = "banco.db"


# -----------------------------
# Banco de dados
# -----------------------------
def connect_data():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = connect_data()
    cursor = conn.cursor()

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


create_tables()


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

def create_table_sorteio():
        conn = connect_data()
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sorteio(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            estado TEXT NOT NULL,
            municipio TEXT NOT NULL,
            cargo TEXT NOT NULL,
            telefone TEXT NOT NULL UNIQUE,
            criado DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
        return "Tabela sorteio criada com sucesso!"
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
                "name": name,
                "estado": estado,
                "municipio": municipio,
                "cargo": cargo,
                "telefone": request.form.get("telefone", "").strip()
            }

            conn.close()
            return render_template("editar.html", participant=participant)

        cursor.execute("""
            UPDATE clientes
            SET name = ?, estado = ?, municipio = ?, cargo = ?, telefone = ?
            WHERE id = ?
        """, (name, estado, municipio, cargo, telefone, id))

        conn.commit()
        conn.close()

        flash("Participante atualizado com sucesso.", "success")
        return redirect(url_for("admin"))

    participant = cursor.execute("""
        SELECT
            id,
            name,
            estado,
            municipio,
            cargo,
            telefone
        FROM clientes
        WHERE id = ?
    """, (id,)).fetchone()

    conn.close()

    if not participant:
        flash("Participante não encontrado.", "danger")
        return redirect(url_for("admin"))

    return render_template("editar.html", participant=participant)

@app.route("/deletar-massa", methods=["POST"]) 

def deletar_massa(): 
    ids = request.form.getlist("ids") 
    if ids: delete_multiple(ids) 
    flash("Registros excluídos") 
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

    create_table_sorteio()

    conn = connect_data()
    cursor = conn.cursor()

    participantes = conn.execute("""
    SELECT * FROM clientes
    WHERE id NOT IN (
        SELECT json_extract(dados, '$.id') FROM sorteio_resultado
    )
""").fetchall()

    # SECRETÁRIOS DE EDUCAÇÃO
    secretarios_educacao = cursor.execute("""
        SELECT COUNT(*) FROM clientes
        WHERE LOWER(cargo) LIKE '%secretário de educação%'
           OR LOWER(cargo) LIKE '%secretario de educacao%'
    """).fetchone()[0]

    # PREFEITOS
    prefeitos = cursor.execute("""
        SELECT COUNT(*) FROM clientes
        WHERE LOWER(cargo) LIKE '%prefeito%'
    """).fetchone()[0]

    # DIRETORES
    diretores = cursor.execute("""
        SELECT COUNT(*) FROM clientes
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
# -----------------------------
@app.route("/pagina-sorteio")
@login_required
def pagina_sorteio():
    conn = connect_data()
    cargos = conn.execute("""
        SELECT DISTINCT cargo
        FROM clientes
        WHERE cargo IS NOT NULL AND cargo != ''
        ORDER BY cargo
    """).fetchall()
    conn.close()

    lista_cargos = [c["cargo"] for c in cargos]
    return render_template("sorteio.html", cargos=lista_cargos)


# -----------------------------
# API - listar participantes
# -----------------------------
@app.route("/api/participantes", methods=["GET"])
@login_required
def api_participantes():
    cargo = request.args.get("cargo", "").strip()

    conn = connect_data()
    cursor = conn.cursor()

    if cargo:
        participantes = cursor.execute("""
            SELECT * FROM clientes
            WHERE cargo LIKE ?
            ORDER BY id DESC
        """, (f"%{cargo}%",)).fetchall()
    else:
        participantes = cursor.execute("""
            SELECT * FROM clientes
            ORDER BY id DESC
        """).fetchall()

    conn.close()

    resultado = []
    for p in participantes:
        resultado.append({
            "id": p["id"],
            "nome": p["name"],
            "estado": p["estado"],
            "municipio": p["municipio"],
            "cargo": p["cargo"],
            "telefone": p["telefone"]
        })

    return jsonify(resultado)


# -----------------------------
# API - sorteio
# -----------------------------
@app.route("/sortear-dme", methods=["POST"])
@login_required
def sortear_dme():
    data = request.get_json(silent=True) or {}

    cargo = data.get("cargo", "").strip()
    quantidade = data.get("quantidade", 1)

    try:
        quantidade = int(quantidade)
    except (TypeError, ValueError):
        return jsonify({"erro": "Quantidade inválida."}), 400

    if quantidade < 1:
        return jsonify({"erro": "A quantidade deve ser maior que zero."}), 400

    conn = connect_data()
    cursor = conn.cursor()

    if cargo:
        participantes = cursor.execute("""
        SELECT * FROM clientes
        WHERE cargo = 'Secretário de Educação'
""").fetchall()
    else:
        participantes = cursor.execute("""
            SELECT * FROM clientes
        WHERE cargo = 'Secretário de Educação'
        """).fetchall()

    conn.close()

    if not participantes:
        return jsonify({"erro": "Nenhum participante encontrado."}), 404

    if quantidade > len(participantes):
        return jsonify({
            "erro": f"A quantidade solicitada ({quantidade}) é maior que o total de participantes ({len(participantes)})."
        }), 400

    sorteados = random.sample(participantes, quantidade)

    resultado = []
    for p in sorteados:
        resultado.append({
            "id": p["id"],
            "nome": p["name"],
            "estado": p["estado"],
            "municipio": p["municipio"],
            "cargo": p["cargo"],
            "telefone": p["telefone"]
        })

    return jsonify({
        "total_participantes": len(participantes),
        "quantidade_sorteada": quantidade,
        "sorteados": resultado
    })
    

import random

@app.route("/sortear", methods=["GET"])
@login_required
def sortear():
    conn = connect_data()
    cursor = conn.cursor()

    participantes = cursor.execute("""
        SELECT
            id,
            name,
            telefone,
            cargo,
            municipio
        FROM sorteio
    """).fetchall()

    conn.close()

    if not participantes:
        return jsonify({"erro": "Nenhum participante encontrado"}), 404

    sorteado = random.choice(participantes)

    return jsonify({
        "id": sorteado["id"],
        "name": sorteado["name"],
        "telefone": sorteado["telefone"],
        "cargo": sorteado["cargo"],
        "municipio": sorteado["municipio"]
    })

@app.route("/tela-sorteio/<int:id>")
def tela_sorteio(id):
    return render_template("tela-sorteio.html")

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

    return jsonify({
        "nome": dados.get("name", ""),
        "cargo": dados.get("cargo", ""),
        "municipio": dados.get("municipio", ""),
        "estado": dados.get("estado", ""),
        "telefone": dados.get("telefone", "")
    })
# -----------------------------
# Rodar o app
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)