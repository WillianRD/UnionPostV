from flask import Flask, render_template, request, redirect, url_for, flash
from Controller import insert_data, read_data
from models import createTable, get_all_participants
import re
import pandas as pd
import re
from models import insertDados
from flask import request
from models import get_by_cargo
from models import get_cargos
import requests

app = Flask(__name__)
createTable()

@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        estado = request.form.get('estado', '').strip()
        municipio = request.form.get('municipio', '').strip()
        cargo = request.form.get('cargo', '').strip()

        # Remove tudo que não for número do telefone
        telefone = re.sub(r'\D', '', request.form.get('telefone', ''))

        erros = []

        # --- Validação do nome ---
        if not name or len(name) < 1:
            erros.append("O nome deve ter pelo menos 1 caracteres.")

        # --- Validação do telefone (10 ou 11 dígitos) ---
        if not re.match(r'^\d{10,11}$', telefone):
            erros.append("O telefone deve conter apenas números e ter 10 ou 11 dígitos (ex: 11987654321).")

        # Se houver erros, exibe na tela
        if erros:
            for e in erros:
                flash(e)
            return render_template('index.html', nome=name, telefone=request.form.get('telefone'))

        # Se estiver tudo certo, insere no banco
        insert_data(name, municipio, cargo, telefone, estado)
        return redirect(url_for('sucesso', nome=name, telefone=telefone))

    return render_template('index.html')


@app.route("/sucesso")
def sucesso():
    nome = request.args.get('nome', '')
    telefone = request.args.get('telefone', '')

    return render_template(
        "sucesso.html",
        nome=nome,
        telefone=telefone
    )

#@app.route("/admin")
#def admin():

   # participantes = get_all_participants()

   # return render_template(
    #    "admin.html",
    #    participantes=participantes,
   #     total=len(participantes)
   # )

@app.route("/admin")
def admin():

    cargo = request.args.get("cargo")

    if cargo:
        participantes = get_by_cargo(cargo)
    else:
        participantes = read_data()

    prefeitos = sum(1 for p in participantes if p["cargo"].upper() == "PREFEITO")
    secretarios = sum(1 for p in participantes if p["cargo"].upper() == "SECRETÁRIO")
    vice = sum(1 for p in participantes if p["cargo"].upper() == "VICE")

    return render_template(
        "admin.html",
        participantes=participantes,
        prefeitos=prefeitos,
        secretarios=secretarios,
        vice=vice
    )

@app.route("/importar", methods=["POST"])
def importar():

    arquivo = request.files["arquivo"]

    df = pd.read_excel(arquivo)

    df.columns = df.columns.str.strip().str.lower()

    for _, linha in df.iterrows():

        nome = str(linha["name"]).strip().upper()
        estado = str(linha["estado"]).strip().upper()
        municipio = str(linha["municipio"]).strip().upper()
        cargo = str(linha["cargo"]).strip().upper()
        

        telefone = re.sub(r"\D", "", str(linha["telefone"]))

        try:
            insert_data(id, nome, municipio, cargo, telefone, estado)
        except Exception as e:
            print("Erro ao inserir:", e)


    return redirect("/admin")

import requests

def municipios_por_estado(uf):

    url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios"

    r = requests.get(url)
    dados = r.json()

    municipios = [m["nome"] for m in dados]

    return municipios


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
