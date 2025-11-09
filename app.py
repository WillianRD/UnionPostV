from flask import Flask, render_template, request, redirect, url_for, flash
from Controller import insert_data
from models import createTable
import re

app = Flask(__name__)
app.secret_key = "chave_secreta"  # necessária pro flash funcionar
createTable()

@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        nomeCliente = request.form.get('name', '').strip()
        tipoDeMarketplace = request.form.get('categoria', '').strip()
        npedido = request.form.get('idpedido', '').strip()

        # Remove tudo que não for número do telefone
        telefone = re.sub(r'\D', '', request.form.get('telefone', ''))

        erros = []

        # --- Validação do nome ---
        if not nomeCliente or len(nomeCliente) < 1:
            erros.append("O nome deve ter pelo menos 1 caracteres.")

        # --- Validação do telefone (10 ou 11 dígitos) ---
        if not re.match(r'^\d{10,11}$', telefone):
            erros.append("O telefone deve conter apenas números e ter 10 ou 11 dígitos (ex: 11987654321).")

        # Se houver erros, exibe na tela
        if erros:
            for e in erros:
                flash(e)
            return render_template('index.html', nome=nomeCliente, telefone=request.form.get('telefone'))

        # Se estiver tudo certo, insere no banco
        insert_data(nomeCliente, tipoDeMarketplace, npedido, telefone)
        return redirect(url_for('sucesso', nome=nomeCliente))

    return render_template('index.html')


@app.route("/sucesso")
def sucesso():
    nome = request.args.get('nome', '')
    return render_template("sucesso.html", nome=nome)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
