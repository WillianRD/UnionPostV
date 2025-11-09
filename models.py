import sqlite3

def connectDb():
    con = sqlite3.connect('banco.db')
    cursor = con.cursor()
    cursor.close()
    return 'Banco criado', True

def createTable():
    con = sqlite3.connect('banco.db')
    cursor = con.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes(
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            name TEXT NOT NULL,
            marketplace TEXT NOT NULL,
            idpedido TEXT NOT NULL,
            telefone TEXT NOT NULL
        )
    ''')
    con.commit()
    cursor.close()
    con.close()

def updateDados(name, marketplace, npedido, telefone):
    con = sqlite3.connect('banco.db')
    cursor = con.cursor()
    
    sql = '''INSERT INTO clientes
        (name, marketplace, npedido, telefone)
        VALUES (?,?,?,?,?,?)'''
    
    cursor.execute(sql, (name, marketplace, npedido, telefone))
    con.commit()
    cursor.close()
    con.close()
    
def ReadDados():
    con = sqlite3.connect('banco.db')
    cursor = con.cursor()
    
    cursor.execute('SELECT * FROM clientes')
    dados = cursor.fetchall()
    con.close()
    
    # Converter os dados
    listaDeProduto = [{
        "nome": linha[1], 
        "marketplace": linha[2],
        "npedido": linha[3],
        "telefone": linha[4],
    } for linha in dados]
    
    return listaDeProduto