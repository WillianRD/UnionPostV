import sqlite3

def read_data():
        
    con = sqlite3.connect('banco.db')
    cursor = con.cursor()
    
    cursor.execute('SELECT * FROM clientes')
    dados = cursor.fetchall()
    print(dados)
    con.close()
    
    # Converter os dados
    listaDeProduto = [{
        "id": linha[0],
        "nome": linha[1], 
        "municipio": linha[2],
        "cargo": linha[3],
        "telefone": linha[4],
        "estado": linha[5],
        } for linha in dados]
    return listaDeProduto