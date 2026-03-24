from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from scraper import LicitacoesScraper
from scraper_pagas import LicitacoesPagasScraper
from datetime import datetime, timedelta
import pandas as pd
import os
import requests as sync_req
import openpyxl
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'minha_chave_super_secreta_123')

# Dicionario de admin fallback offline!
USERS = {
    "admin": "admin",
    "gabriel": "123456"
}

def is_logged_in():
    return 'user' in session

def verificar_credenciais_sheety(username, password):
    url = "https://api.sheety.co/35f7dca5d0a749d89507e33c6442aedc/saudaAi/usuarios"
    try:
        resp = sync_req.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            usuarios = data.get('usuarios', [])
            
            for u in usuarios:
                u_nome = str(u.get('email', '')).strip()
                u_senha = str(u.get('senha', '')).strip()
                
                if u_nome == username and u_senha == password:
                    return True
            return False
        else:
            print(f"Erro ao acessar API do Sheety para usuários: {resp.status_code}")
            if username == "admin" and password == "admin":
                return True
            return False
    except Exception as e:
        print(f"Exceção na validação Sheety: {e}")
        if username == "admin" and password == "admin":
            return True
        return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Pega a credencial seja via name="email" ou "username" do frontend
        username = request.form.get('email') or request.form.get('username')
        password = request.form.get('password')
        
        # Testando primeiramente o backend hardcoded antigo
        if username in USERS and USERS[username] == password:
            session['user'] = username
            return redirect(url_for('escolha'))
            
        # Caso não seja o admin, tenta validar no Sheety (novo recurso)
        if verificar_credenciais_sheety(username, password):
            session['user'] = username
            return redirect(url_for('escolha'))
            
        return render_template('login.html', error="Usuário/E-mail ou senha inválidos")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/escolha')
def escolha():
    if not is_logged_in():
        return redirect(url_for('login'))
    return render_template('escolha.html')

@app.route('/')
def home():
    if not is_logged_in():
        return redirect(url_for('login'))
    return redirect(url_for('escolha'))

@app.route('/abertas')
def abertas():
    if not is_logged_in():
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/pagas')
def pagas():
    if not is_logged_in():
        return redirect(url_for('login'))
    return render_template('licitacoes_pagas.html')

@app.route('/api/search', methods=['POST'])
def search():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    term = data.get('term', '')
    
    # Processa datas
    data_inicial = data.get('dataInicial')
    data_final = data.get('dataFinal')
    
    if not data_inicial:
        # Padrão: ultimo mes
        data_inicial = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not data_final:
        data_final = datetime.now().strftime('%Y-%m-%d')

    try:
        scraper = LicitacoesScraper(headless=True)
        results = scraper.scrape(term, data_inicial, data_final)
        
        # Gera o Excel de abertas
        df = pd.DataFrame(results)
        df.to_excel('leads_gerados.xlsx', index=False)

        return jsonify(results)
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(error_msg)
        return jsonify({"error": "Erro interno no servidor de extração", "traceback": error_msg}), 500

@app.route('/api/search_pagas', methods=['POST'])
def search_pagas():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    estado = data.get('estado', 'SP')
    orgao = data.get('orgao', '')
    municipio = data.get('municipio', '')
    cnpj = data.get('cnpj', '')
    
    data_inicial = data.get('dataInicial')
    data_final = data.get('dataFinal')
    
    if not data_inicial:
        data_inicial = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    if not data_final:
        data_final = datetime.now().strftime('%Y-%m-%d')

    try:
        scraper = LicitacoesPagasScraper(headless=True)
        results = scraper.scrape(data_inicial, data_final, orgao, estado, municipio, cnpj)
            
        # Gera o Excel
        df = pd.DataFrame(results)
        df.to_excel('leads_licitacoes_pagas.xlsx', index=False)

        return jsonify(results)
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(error_msg)
        return jsonify({"error": "Erro interno no servidor de extração", "traceback": error_msg}), 500

@app.route('/api/download', methods=['GET'])
def download_excel():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    from flask import send_file
    try:
        return send_file('leads_gerados.xlsx', as_attachment=True, download_name='leads_licitacoes.xlsx')
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route('/api/download_pagas', methods=['GET'])
def download_excel_pagas():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    from flask import send_file
    try:
        return send_file('leads_licitacoes_pagas.xlsx', as_attachment=True, download_name='licitacoes_pagas.xlsx')
    except Exception as e:
        return jsonify({"error": str(e)}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
