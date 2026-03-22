import sqlite3

def connect_data():
    conn = sqlite3.connect('banco.db')
    conn.row_factory = sqlite3.Row  # ADICIONA ISSO
    return conn
    