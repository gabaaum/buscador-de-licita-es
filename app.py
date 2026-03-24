import os
import asyncio
from datetime import timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from pdf_analyzer import processar_edital
from supabase_client import supabase
from scraper import ComprasScraper

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super_secret_key")
app.permanent_session_lifetime = timedelta(days=7)

def login_required(view_func):
    def wrapper(*args, **kwargs):
        if not session.get("access_token"):
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper

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
    if not session.get("access_token"):
        return redirect(url_for("login"))
    return redirect(url_for("escolha"))

@app.route("/escolha")
@login_required
def escolha():
    return render_template("escolha.html")

@app.route("/pncp_contratos")
@login_required
def pncp_contratos():
    return render_template("pncp_contratos.html")

@app.route("/abertas")
@login_required
def abertas():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
            if res and res.session and res.session.access_token:
                session.permanent = True
                session["access_token"] = res.session.access_token
                session["user_id"] = res.user.id if res.user else None
                session["usuario"] = email
                return redirect(url_for("escolha"))
            else:
                flash("Credenciais inválidas", "error")
        except Exception as e:
            flash("Erro ao autenticar: " + str(e), "error")
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")
        try:
            res = supabase.auth.sign_up({"email": email, "password": senha})
            if res and res.user:
                flash("Cadastro realizado. Confira seu e-mail para confirmação.", "success")
                return redirect(url_for("login"))
            else:
                flash("Não foi possível cadastrar.", "error")
        except Exception as e:
            flash("Erro ao cadastrar: " + str(e), "error")
    return render_template("signup.html")

@app.route("/logout")
def logout():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    session.clear()
    return redirect(url_for("login"))

@app.route("/api/search", methods=["POST"])
@login_required
def search():
    
    data = request.json
    term = data.get("term")
    numero_licitacao = data.get("numeroLicitacao")
    data_inicial = data.get("dataInicial")
    data_final = data.get("dataFinal")
    
    if not term and not numero_licitacao:
        return jsonify({"error": "Termo de busca ou Número de Licitação não fornecidos."}), 400
    
    try:
        # Run scraper in a synchronous wrapper
        results = run_scraper(term, data_inicial, data_final)
        if numero_licitacao:
            numero_lower = numero_licitacao.lower()
            results = [r for r in results if r.get("numero", "").lower().find(numero_lower) != -1]
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/get-resumo", methods=["POST"])
@login_required
def get_resumo():
    
    data = request.json
    url_edital = data.get("url")
    
    if not url_edital:
        return jsonify({"sucesso": False, "mensagem": "URL não fornecida."}), 400
        
    resultado = processar_edital(url_edital)
    return jsonify(resultado)

from scraper_pncp_contratos import PNCPContratosScraper

def run_scraper_pncp(term, uf, data_inicial, data_final, numero_licitacao=None):
    scraper = PNCPContratosScraper()
    return scraper.scrape(term, uf, data_inicial, data_final, numero_licitacao)

@app.route("/api/search_pncp", methods=["POST"])
@login_required
def search_pncp():
    
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

if __name__ == "__main__":
    app.run(debug=True, port=5000)
