import sqlite3

def insert_data(name, municipio, cargo, telefone, estado):

    with sqlite3.connect("banco.db", timeout=10) as con:

        cursor = con.cursor()

        cursor.execute(''
            "INSERT INTO clientes (name, municipio, cargo, telefone, estado) VALUES (?, ?, ?, ?, ?)",
            (name, municipio, cargo, telefone, estado)
        )

        con.commit()