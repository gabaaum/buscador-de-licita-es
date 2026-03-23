# Portal Multiestadual de Licitações - Deploy

Este projeto é uma aplicação Flask que executa extração de dados (Web Scraping / API reverse engineering) dos portais de transparência de SP, RJ e MG usando **Playwright** e **Requests**.

Devido à dependência do Playwright (que necessita do Chromium), o Deploy deve ser feito via **Docker** em plataformas como Render, Railway, AWS (ECS/EC2) ou em um servidor Linux comum (VPS).

## 🚀 Método 1: Deploy com Docker (Recomendado)

O repositório já contém um `Dockerfile` oficial que baixa a imagem do Python, instala os navegadores embutidos do Playwright (Chromium) e usa o `gunicorn` para rodar o Flask em ambiente de produção.

### Requisitos:
- Docker instalado.
- Conta no [Render](https://render.com) ou [Railway](https://railway.app).

### Passo a Passo no Render.com:
1. Faça o fork/push deste código para o seu GitHub.
2. Crie uma conta no Render e clique em **New > Web Service**.
3. Conecte seu repositório GitHub.
4. No campo **Environment**, escolha **Docker**.
5. Em configurações, aponte a porta para `5000` (se solicitado).
6. Clique em **Create Web Service**. O Render vai ler o Dockerfile, baixar o Chromium e subir sua aplicação automaticamente.

### Como rodar localmente com Docker:
```bash
docker build -t portal-licitacoes .
docker run -d -p 5000:5000 portal-licitacoes
```
Acesse em `http://localhost:5000`.

---

## 💻 Método 2: Deploy em Servidor Ubuntu (VPS)

Se você preferir rodar em um EC2 (AWS) ou Droplet (DigitalOcean) com Ubuntu:

**1. Instale o Python e ferramentas básicas:**
```bash
sudo apt update
sudo apt install python3-pip python3-venv -y
```

**2. Clone o repositório e crie o ambiente virtual:**
```bash
git clone https://seu-repo.git /opt/portal-licitacoes
cd /opt/portal-licitacoes
python3 -m venv venv
source venv/bin/activate
```

**3. Instale as dependências e o Playwright:**
```bash
pip install -r requirements.txt
pip install gunicorn
playwright install chromium
playwright install-deps
```

**4. Inicie a aplicação com Gunicorn no plano de fundo:**
```bash
gunicorn --bind 0.0.0.0:5000 app:app --timeout 120 --workers 3 --daemon
```

*Obs: É recomendado usar o Nginx como proxy reverso para apontar a porta 80 do domínio para o localhost:5000 e instalar certificado SSL.*

## ⚙️ Variáveis de Ambiente (Opcional)
Se precisar modificar o ambiente da aplicação, configure as variáveis abaixo na plataforma de hospedagem:
- `FLASK_ENV` = `production`
- `PLAYWRIGHT_BROWSERS_PATH` = `0` (Opcional, útil no Render para evitar caches de disco conflitantes)
