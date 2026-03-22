import sqlite3

def insert_data(name, municipio, cargo, telefone, estado):
    try:
        with sqlite3.connect("banco.db") as con:
            cursor = con.cursor()
            cursor.execute(
                "INSERT INTO clientes (name, municipio, cargo, telefone, estado) VALUES (?, ?, ?, ?, ?)",
                (name, municipio, cargo, telefone, estado)
            )
            con.commit()
            return True

    except sqlite3.IntegrityError:
        return False