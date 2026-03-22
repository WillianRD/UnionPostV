
import sqlite3

def create_table():
    con = sqlite3.connect('banco.db')
    cursor = con.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        estado TEXT NOT NULL,
        municipio TEXT NOT NULL,
        cargo TEXT NOT NULL,
        telefone TEXT NOT NULL
    )
    """)

    con.commit()
    con.close()

create_table()