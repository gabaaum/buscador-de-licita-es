from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import requests
from scraper import ComprasScraper
import asyncio
from pdf_analyzer import processar_edital

app = Flask(__name__)
app.secret_key = "super_secret_key"  # Em produção, use uma variável de ambiente

SHEETY_URL = "https://api.sheety.co/35f7dca5d0a749d89507e33c6442aedc/saudaAi/usuarios"

def validar_usuario(email, senha):
    try:
        response = requests.get(SHEETY_URL)
        if response.status_code == 200:
            data = response.json()
            usuarios = data.get("usuarios", [])
            for user in usuarios:
                if user.get("email") == email and str(user.get("senha")) == str(senha):
                    return True
    except Exception as e:
        print(f"Erro ao acessar API do Sheety: {e}")
    return False

def run_scraper(term, data_inicial, data_final):
    scraper = ComprasScraper(headless=True)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        results = loop.run_until_complete(scraper.scrape(term, data_inicial, data_final))
    finally:
        loop.close()
    return results

@app.route("/")
def index():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("escolha"))

@app.route("/escolha")
def escolha():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return render_template("escolha.html")

@app.route("/pncp_contratos")
def pncp_contratos():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return render_template("pncp_contratos.html")

@app.route("/abertas")
def abertas():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/pagas")
def pagas():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return render_template("licitacoes_pagas.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")
        
        if validar_usuario(email, senha):
            session["usuario"] = email
            return redirect(url_for("escolha"))
        else:
            flash("Usuário ou senha inválidos", "error")
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("login"))

@app.route("/api/search", methods=["POST"])
def search():
    if "usuario" not in session:
        return jsonify({"error": "Não autorizado"}), 401
    
    data = request.json
    term = data.get("term")
    data_inicial = data.get("dataInicial")
    data_final = data.get("dataFinal")
    
    if not term:
        return jsonify({"error": "Termo de busca não fornecido."}), 400
        
    try:
        # Run scraper in a synchronous wrapper
        results = run_scraper(term, data_inicial, data_final)
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/get-resumo", methods=["POST"])
def get_resumo():
    if "usuario" not in session:
        return jsonify({"error": "Não autorizado"}), 401
    
    data = request.json
    url_edital = data.get("url")
    
    if not url_edital:
        return jsonify({"sucesso": False, "mensagem": "URL não fornecida."}), 400
        
    resultado = processar_edital(url_edital)
    return jsonify(resultado)

from scraper_pagas import LicitacoesPagasScraper
from scraper_sp import LicitacoesPagasScraperSP
from scraper_rj import LicitacoesPagasScraperRJ
from scraper_mg import LicitacoesPagasScraperMG
from scraper_pncp_contratos import PNCPContratosScraper

def run_scraper_pncp(term, uf, data_inicial, data_final, numero_licitacao=None):
    scraper = PNCPContratosScraper()
    return scraper.scrape(term, uf, data_inicial, data_final, numero_licitacao)

@app.route("/api/search_pncp", methods=["POST"])
def search_pncp():
    if "usuario" not in session:
        return jsonify({"error": "Não autorizado"}), 401
    
    data = request.json
    term = data.get("term", "")
    numero_licitacao = data.get("numeroLicitacao", "")
    uf = data.get("uf", "SP")
    data_inicial = data.get("dataInicial")
    data_final = data.get("dataFinal")
    
    if not term and not numero_licitacao:
        return jsonify({"error": "Termo de busca ou Número de Licitação não fornecidos."}), 400
        
    try:
        results = run_scraper_pncp(term, uf, data_inicial, data_final, numero_licitacao)
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run_scraper_pagas(estado, data_inicial, data_final, orgao, municipio, cnpj):
    if estado == 'sp':
        scraper = LicitacoesPagasScraperSP(headless=True)
    elif estado == 'rj':
        scraper = LicitacoesPagasScraperRJ(headless=True)
    elif estado == 'mg':
        scraper = LicitacoesPagasScraperMG(headless=True)
    else:
        scraper = LicitacoesPagasScraper(headless=True)
        
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        results = loop.run_until_complete(scraper.scrape(data_inicial, data_final, orgao, municipio, cnpj))
    finally:
        loop.close()
    return results

@app.route("/api/search_pagas", methods=["POST"])
def search_pagas():
    if "usuario" not in session:
        return jsonify({"error": "Não autorizado"}), 401
    
    data = request.json
    estado = data.get("estado", "federal")
    data_inicial = data.get("dataInicial")
    data_final = data.get("dataFinal")
    orgao = data.get("orgao")
    municipio = data.get("municipio")
    cnpj = data.get("cnpj")
    
    try:
        results = run_scraper_pagas(estado, data_inicial, data_final, orgao, municipio, cnpj)
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
