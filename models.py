import sqlite3
from Controller import connect_data

def createTable():

    conn = connect_data()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            estado TEXT NOT NULL,
            municipio TEXT NOT NULL,
            cargo TEXT NOT NULL,
            telefone TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def insertDados(name,estado, municipio, cargo, telefone):

    conn = connect_data()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO clientes (name, estado, municipio, cargo, telefone)
        VALUES (?, ?, ?, ?, ?)
    """, (name, estado, municipio, cargo, telefone))

    conn.commit()
    conn.close()


def get_all_participants():

    conn = connect_data()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name,estado, municipio, cargo, telefone
        FROM clientes
        ORDER BY id DESC
    """)

    dados = cursor.fetchall()

    conn.close()

    return dados

def get_by_cargo(cargo):

    con = sqlite3.connect('banco.db')
    cursor = con.cursor()

    cursor.execute("""
        SELECT id, name, estado, unicipio, cargo, telefone
        FROM clientes
        WHERE UPPER(cargo) = UPPER(?)
        ORDER BY id DESC
    """, (cargo,))

    dados = cursor.fetchall()
    con.close()

    participantes = [{
        "id": d[0],
        "nome": d[1],
        "estado": d[2],
        "municipio": d[3],
        "cargo": d[4],
        "telefone": d[5]
    } for d in dados]

    return participantes

def get_cargos():

    con = sqlite3.connect('banco.db')
    cursor = con.cursor()

    cursor.execute("""
        SELECT DISTINCT cargo
        FROM clientes
        ORDER BY cargo
    """)

    cargos = cursor.fetchall()

    con.close()

    return [c[0] for c in cargos]

    return dados