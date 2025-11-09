
import sqlite3

def insert_data(nome,marketplace, npedido, telefone):
    con = sqlite3.connect('banco.db')
    cursor = con.cursor()
    
    sql = '''INSERT INTO clientes
        (name, marketplace,npedido, telefone)
        VALUES (?,?,?,?)'''
    cursor.execute(sql, (nome, marketplace, npedido, telefone))
    con.commit()
    cursor.close()
