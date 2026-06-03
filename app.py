import streamlit as st
import base64
import httpx
from PIL import Image
import io
import json
import asyncio
import os


# Função de análise de dano (mock de IA)
def analisar_dano_ia(imagens):
    """Analisa as imagens usando OpenAI Vision/Responses.

    Requisitos (variáveis de ambiente):
    - OPENAI_API_KEY
    - OPENAI_VISION_MODEL (opcional, default: gpt-4.1-mini)
    """

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_VISION_MODEL", "gpt-4.1-mini")

    if not api_key:
        # fallback seguro: mock básico
        if len(imagens) >= 3:
            peca = "Para-choque"
            gravidade = "Leve"
            acao_sugerida = "Reparo Rápido"
        else:
            peca = "Parabrisa"
            gravidade = "Moderada"
            acao_sugerida = "Avaliação Técnica"
        return {
            "status": "sucesso",
            "peca": peca,
            "gravidade": gravidade,
            "acao_sugerida": acao_sugerida,
        }

    # Converte uploads para base64 (data URLs)
    # Observação: OpenAI aceita image_url do tipo data:image/...;base64,...
    image_urls = []
    for f in imagens[:5]:
        raw = f.getvalue()
        b64 = base64.b64encode(raw).decode("utf-8")
        image_urls.append(f"data:image/jpeg;base64,{b64}")

    prompt = (
        "Você é um assistente de triagem de sinistros automotivos da seguradora GBL. "
        "Analise as imagens e retorne UM JSON válido com exatamente as chaves: "
        "status, peca, gravidade, acao_sugerida. "
        "- status deve ser 'sucesso'. "
        "- peca: escolha uma peça provável entre: Para-choque, Para-brisa, Capô, Porta, Lanterna, Farol, Paralama, Retrovisor, Outros. "
        "- gravidade: escolha entre 'Leve', 'Moderada', 'Grave'. "
        "- acao_sugerida: frase curta e objetiva para o segurado (ex.: 'Reparo Rápido', 'Oficina Especializada', 'Agendar Vistoria'). "
        "Não inclua comentários fora do JSON." 
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # API Responses (novo): https://platform.openai.com/docs/api-reference/responses
    payload = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    *[
                        {
                            "type": "image_url",
                            "image_url": {"url": url},
                        }
                        for url in image_urls
                    ],
                ],
            }
        ],
        "response_format": {"type": "json_object"},
    }

    resp = httpx.post(
        "https://api.openai.com/v1/responses",
        headers=headers,
        json=payload,
        timeout=30,
    )

    resp.raise_for_status()
    data = resp.json()

    # extrai o JSON do output
    # Estrutura típica: data['output'][0]['content'][0]['text'] ou similares.
    # Vamos tentar localizar o primeiro texto.
    text = None
    try:
        for out in data.get("output", []):
            for c in out.get("content", []):
                if c.get("type") == "output_text" and c.get("text"):
                    text = c["text"]
                    break
            if text:
                break
    except Exception:
        text = None

    if not text:
        # fallback: tenta direto no campo
        text = json.dumps(data)

    parsed = json.loads(text)
    parsed["status"] = "sucesso"
    return parsed


# Função de envio para n8n
def enviar_para_n8n(data):
    # URL do webhook do n8n
    webhook_url = "https://aplication-n8n.ho923p.easypanel.host/webhook/seguros"
    
    try:
        response = httpx.post(webhook_url, json=data, timeout=10)
        if response.status_code != 200:
            st.error(
                "❌ Falha ao chamar o webhook do n8n. "
                f"HTTP {response.status_code}: {response.text[:500]}"
            )
        return response.status_code == 200
    except Exception as e:
        st.error(f"Erro de conexão com o n8n: {str(e)}")
        return False

# Configuração da interface
st.set_page_config(
    page_title="Portal de Sinistros GBL",
    page_icon="🚗",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Paleta de cores institucional GBL
color_primary = "#003366"  # Azul Escuro
color_secondary = "#FFFFFF"  # Branco
color_tertiary = "#F0F0F0"  # Cinza Claro

# Estilo CSS personalizado
st.markdown(
    f"""
    <style>
    .main {{
        background-color: {color_secondary};
        color: #333;
    }}
    .stButton>button {{
        background-color: {color_primary};
        color: {color_secondary};
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
    }}
    .stButton>button:hover {{
        background-color: #002244;
    }}
    .stFileUploader>div>div {{
        border-color: {color_primary};
    }}
    .stTextInput>div>div>input {{
        border-color: {color_primary};
    }}
    .stSelectbox>div>div>select {{
        border-color: {color_primary};
    }}
    h1, h2, h3 {{
        color: {color_primary};
    }}
    .stAlert {{
        background-color: {color_tertiary};
        border-left: 4px solid {color_primary};
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# Título da aplicação
st.title("🚗 Portal de Sinistros GBL")
st.markdown("### Relate o sinistro de seu veículo de forma rápida e segura")

# Formulário de identificação
st.subheader("Identificação")
col1, col2, col3 = st.columns(3)

with col1:
    nome = st.text_input("Nome Completo", placeholder="Digite seu nome completo")

with col2:
    apolice = st.text_input("Número da Apólice", placeholder="Ex: GBL-2024-00123")

with col3:
    placa = st.text_input("Placa do Veículo", placeholder="Ex: ABC-1234")

# Seleção de cobertura
cobertura = st.selectbox(
    "Tipo de Cobertura",
    ["Seguro Total", "Terceiros", "Danos Materiais", "Roubo e Furto"],
    help="Selecione o tipo de cobertura contratada"
)

# Descrição do sinistro
st.subheader("Descrição do Ocorrido")
descricao = st.text_area(
    "Descreva o que aconteceu",
    placeholder="Ex: Colisão traseira em semáforo, sem envolvimento de outros veículos. Veículo parado. Nenhum ferido.",
    height=100
)

# Upload de imagens
st.subheader("Fotos do Dano")
uploaded_files = st.file_uploader(
    "Arraste e solte ou clique para carregar imagens (máx. 5)",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    help="Carregue fotos claras do dano, de diferentes ângulos"
)

# Preview das imagens carregadas
if uploaded_files:
    st.markdown("**Pré-visualização das imagens:**")
    cols = st.columns(min(len(uploaded_files), 5))
    for idx, uploaded_file in enumerate(uploaded_files[:5]):
        with cols[idx]:
            image = Image.open(uploaded_file)
            st.image(image, caption=f"Foto {idx+1}", use_column_width=True)

# Botão de envio
if st.button("Enviar Sinistro", type="primary"):
    # Validação de campos obrigatórios
    if not nome or not apolice or not placa:
        st.error("Por favor, preencha todos os campos de identificação.")
    elif not uploaded_files:
        st.error("Por favor, carregue pelo menos uma foto do dano.")
    else:
        # Simulação de análise de IA
        with st.spinner("Analisando as imagens..."):
            resultado_ia = analisar_dano_ia(uploaded_files)
        
        # Envio para n8n
        with st.spinner("Enviando dados para processamento..."):
            sucesso_envio = enviar_para_n8n({
                "nome": nome,
                "apolice": apolice,
                "placa": placa,
                "cobertura": cobertura,
                "descricao": descricao,
                "imagens": [base64.b64encode(file.getvalue()).decode('utf-8') for file in uploaded_files],
                "analise_ia": resultado_ia
            })
        
        # Exibição do resultado
        if sucesso_envio:
            st.success("✅ Sinistro enviado com sucesso!")
            st.markdown("### 📊 Resultado da Análise de IA")
            st.json(resultado_ia)
            st.markdown(f"""
            <div style="background-color: {color_tertiary}; padding: 15px; border-radius: 8px; border-left: 4px solid {color_primary};">
                <strong>Recomendação:</strong> {resultado_ia['acao_sugerida']}<br>
                <strong>Peça danificada:</strong> {resultado_ia['peca']}<br>
                <strong>Gravidade:</strong> {resultado_ia['gravidade']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("❌ Ocorreu um erro ao enviar os dados. Tente novamente.")

# Rodapé
st.markdown("---")
st.markdown("<p style='text-align: center; color: #666;'>Portal de Sinistros GBL - Segurança e eficiência em cada passo</p>", unsafe_allow_html=True)
