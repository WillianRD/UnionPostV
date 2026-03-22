import sqlite3
from Controller import connect_data
from datetime import datetime
from zoneinfo import ZoneInfo
from werkzeug.security import generate_password_hash



# ----------------- TIMEZONE -----------------
def formatar_data(data_str):
    if not data_str:
        return None

    data_utc = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
    data_utc = data_utc.replace(tzinfo=ZoneInfo("UTC"))

    data_br = data_utc.astimezone(ZoneInfo("America/Sao_Paulo"))

    return data_br.strftime("%d/%m/%Y %H:%M:%S")


def processar_dados(dados):
    resultado = []
    for d in dados:
        d = dict(d)
        if "criado_em" in d:
            d["criado_em"] = formatar_data(d["criado_em"])
        resultado.append(d)
    return resultado


# ----------------- CLIENTES -----------------
def create_table_clientes():
    conn = connect_data()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            estado TEXT NOT NULL,
            municipio TEXT NOT NULL,
            cargo TEXT NOT NULL,
            telefone TEXT NOT NULL UNIQUE,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

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
                       criado DATETIME DEFAULT CURRENT_TIMESTAMP)"""
                       )
        print("Tabela sorteio criada com sucesso!")
        conn.commit()
        conn.close()

def insert_data(name, estado, municipio, cargo, telefone):
    try:
        conn = connect_data()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO clientes (name, estado, municipio, cargo, telefone)
            VALUES (?, ?, ?, ?, ?)
        """, (name, estado, municipio, cargo, telefone))

        conn.commit()
        conn.close()

        return True

    except sqlite3.IntegrityError:
        return False


def get_all_participants():
    conn = connect_data()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, estado, municipio, cargo, telefone, criado_em
        FROM clientes
        ORDER BY criado_em DESC
    """)

    dados = cursor.fetchall()
    conn.close()

    return processar_dados(dados)


def get_by_cargo(cargo):
    conn = connect_data()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, estado, municipio, cargo, telefone, criado_em
        FROM clientes
        WHERE UPPER(cargo) = UPPER(?)
        ORDER BY criado_em DESC
    """, (cargo,))

    dados = cursor.fetchall()
    conn.close()

    return processar_dados(dados)


def get_participants(cargo=None):
    return get_by_cargo(cargo) if cargo else get_all_participants()


def get_cargos():
    conn = connect_data()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT cargo
        FROM clientes
        ORDER BY cargo
    """)

    cargos = cursor.fetchall()
    conn.close()

    return [c[0] for c in cargos]


def get_by_id(id):
    conn = connect_data()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM clientes WHERE id = ?", (id,))
    dado = cursor.fetchone()

    conn.close()

    if dado:
        d = dict(dado)
        d["criado_em"] = formatar_data(d["criado_em"])
        return d

    return None


def update_participant(id, name, municipio, cargo, telefone, estado):
    conn = connect_data()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE clientes
        SET name=?, municipio=?, cargo=?, telefone=?, estado=?
        WHERE id=?
    """, (name, municipio, cargo, telefone, estado, id))

    conn.commit()
    conn.close()


def delete_multiple(ids):
    conn = connect_data()
    cursor = conn.cursor()

    query = f"DELETE FROM clientes WHERE id IN ({','.join(['?']*len(ids))})"
    cursor.execute(query, ids)

    conn.commit()
    conn.close()


def delete_participant(id):
    conn = connect_data()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM clientes WHERE id = ?", (id,))

    conn.commit()
    conn.close()


# ----------------- USERS -----------------
def create_users_table():
    conn = connect_data()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def create_admin():
    conn = connect_data()
    cursor = conn.cursor()

    password_hash = generate_password_hash("fran123")

    cursor.execute("""
        INSERT OR IGNORE INTO users(username, password)
        VALUES (?, ?)
    """, ("FranciscoAdm", password_hash))

    conn.commit()
    conn.close()

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def get_today_participants():
    conn = connect_data()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    tz = ZoneInfo("America/Sao_Paulo")

    # início do dia no Brasil
    inicio_br = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)

    # fim do dia
    fim_br = inicio_br + timedelta(days=1)

    # converter para UTC
    inicio_utc = inicio_br.astimezone(ZoneInfo("UTC"))
    fim_utc = fim_br.astimezone(ZoneInfo("UTC"))

    cursor.execute("""
        SELECT id, name, estado, municipio, cargo, telefone, criado_em
        FROM clientes
        WHERE criado_em BETWEEN ? AND ?
        ORDER BY criado_em DESC
    """, (
        inicio_utc.strftime("%Y-%m-%d %H:%M:%S"),
        fim_utc.strftime("%Y-%m-%d %H:%M:%S")
    ))

    dados = cursor.fetchall()
    conn.close()

    return processar_dados(dados)

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def get_week_participants():
    conn = connect_data()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    tz = ZoneInfo("America/Sao_Paulo")

    agora_br = datetime.now(tz)
    inicio_br = agora_br - timedelta(days=7)

    # converter para UTC
    inicio_utc = inicio_br.astimezone(ZoneInfo("UTC"))
    fim_utc = agora_br.astimezone(ZoneInfo("UTC"))

    cursor.execute("""
        SELECT id, name, estado, municipio, cargo, telefone, criado_em
        FROM clientes
        WHERE criado_em BETWEEN ? AND ?
        ORDER BY criado_em DESC
    """, (
        inicio_utc.strftime("%Y-%m-%d %H:%M:%S"),
        fim_utc.strftime("%Y-%m-%d %H:%M:%S")
    ))

    dados = cursor.fetchall()
    conn.close()

    return processar_dados(dados)

def get_month_participants():
    conn = connect_data()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    tz = ZoneInfo("America/Sao_Paulo")

    agora_br = datetime.now(tz)

    # primeiro dia do mês
    inicio_br = agora_br.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # início do próximo mês
    if agora_br.month == 12:
        proximo_mes = agora_br.replace(year=agora_br.year + 1, month=1, day=1)
    else:
        proximo_mes = agora_br.replace(month=agora_br.month + 1, day=1)

    fim_br = proximo_mes.replace(hour=0, minute=0, second=0, microsecond=0)

    # converter para UTC
    inicio_utc = inicio_br.astimezone(ZoneInfo("UTC"))
    fim_utc = fim_br.astimezone(ZoneInfo("UTC"))

    cursor.execute("""
        SELECT id, name, estado, municipio, cargo, telefone, criado_em
        FROM clientes
        WHERE criado_em BETWEEN ? AND ?
        ORDER BY criado_em DESC
    """, (
        inicio_utc.strftime("%Y-%m-%d %H:%M:%S"),
        fim_utc.strftime("%Y-%m-%d %H:%M:%S")
    ))

    dados = cursor.fetchall()
    conn.close()

    return processar_dados(dados)