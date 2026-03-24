import re
import requests
import io
import PyPDF2

def get_pdf_url_from_pncp(url_edital):
    # Se já for um link de arquivo .pdf, retorna direto
    if url_edital.lower().endswith('.pdf') or 'arquivos' in url_edital.lower():
        return url_edital
        
    # Se for uma página do PNCP, precisamos tentar buscar a API de arquivos deles
    # O link do frontend é algo como: https://pncp.gov.br/app/editais/00685483000105/2026/7
    # A API para arquivos é: https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos
    try:
        match = re.search(r'editais/(\d+)/(\d+)/(\d+)', url_edital)
        if match:
            cnpj = match.group(1)
            ano = match.group(2)
            seq = match.group(3)
            
            api_url = f"https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos"
            headers = {'Accept': 'application/json'}
            resp = requests.get(api_url, headers=headers, timeout=15)
            
            if resp.status_code == 200:
                arquivos = resp.json()
                for arquivo in arquivos:
                    # Preferência para editais
                    titulo = arquivo.get("tituloDocumento", "").lower()
                    tipo = arquivo.get("tipoDocumentoId")
                    if "edital" in titulo or tipo == 1: # 1 geralmente é edital no PNCP
                         link_arquivo = arquivo.get("url")
                         if link_arquivo:
                             return link_arquivo
                         return f"https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos/{arquivo.get('sequencial')}"
                
                # Se não achar especificamente um edital, retorna o primeiro arquivo válido
                for arquivo in arquivos:
                    link_arquivo = arquivo.get("url")
                    if link_arquivo:
                        return link_arquivo
                    return f"https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos/{arquivo.get('sequencial')}"

    except Exception as e:
        print(f"Erro ao tentar resolver link do PNCP: {e}")
        
    return url_edital

def processar_edital(url_edital):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Primeiro, tentar obter o link real do PDF caso seja uma página HTML do PNCP
        url_pdf = get_pdf_url_from_pncp(url_edital)
        print(f"URL Original: {url_edital} | URL PDF Resolvida: {url_pdf}")
        
        response = requests.get(url_pdf, headers=headers, timeout=20)
        
        if response.status_code != 200:
            return {"sucesso": False, "mensagem": f"Erro ao baixar edital. Código {response.status_code}", "pode_baixar": True, "url_resolvida": url_pdf}

        if not response.content.startswith(b'%PDF'):
            return {"sucesso": False, "mensagem": "O documento oficial encontrado não está em formato PDF. Resumo indisponível para este formato.", "pode_baixar": True, "url_resolvida": url_pdf}

        pdf_file = io.BytesIO(response.content)
        reader = PyPDF2.PdfReader(pdf_file)
        
        texto_completo = ""
        num_pages = min(len(reader.pages), 50)
        
        for i in range(num_pages):
            try:
                page = reader.pages[i]
                t = page.extract_text()
                if t:
                    texto_completo += t + "\n"
            except Exception as e:
                print(f"Erro ao extrair texto da pagina {i}: {e}")

        # Se o texto extraído for muito curto (menos de 50 caracteres), consideramos que o PyPDF2 falhou em ler (ex: arquivo de imagem escaneada)
        # MAS vamos tentar ainda assim buscar algumas regex básicas se houver algum texto.
        if len(texto_completo.strip()) < 50:
             return {"sucesso": False, "mensagem": "O edital foi escaneado como imagem e não contém texto pesquisável (OCR necessário). Resumo indisponível para este formato.", "pode_baixar": True, "url_resolvida": url_pdf}

        resumo = {
            "valor_estimado": "Não encontrado na leitura",
            "objeto": "Não encontrado na leitura",
            "exigencias": [],
            "data_sessao": "Não encontrado na leitura"
        }

        texto_lower = texto_completo.lower()

        match_valor = re.search(r'valor\s+(?:global\s+|total\s+)?estimado\s+(?:em|de)?\s*(r\$\s*[\d\.,]+)', texto_lower)
        if match_valor:
            resumo["valor_estimado"] = match_valor.group(1).upper()
        else:
             match_valor2 = re.search(r'r\$\s*[\d\.,]{3,}', texto_lower)
             if match_valor2:
                 resumo["valor_estimado"] = match_valor2.group(0).upper() + " (aprox.)"

        match_objeto = re.search(r'(?:objeto|do objeto)[^\n]*\n(.*?)(?:\n\n|\n[A-Z0-9])', texto_completo, re.IGNORECASE | re.DOTALL)
        if match_objeto:
             obj_str = match_objeto.group(1).replace('\n', ' ').strip()
             if len(obj_str) > 10:
                resumo["objeto"] = obj_str[:300] + "..." if len(obj_str) > 300 else obj_str

        exigencias_encontradas = []
        if re.search(r'atestado(?:s)? de capacidade t[eé]cnica', texto_lower):
            exigencias_encontradas.append("Atestado de capacidade técnica")
        if re.search(r'patrim[oô]nio l[ií]quido', texto_lower):
            exigencias_encontradas.append("Comprovação de patrimônio líquido")
        if re.search(r'vistoria', texto_lower) or re.search(r'visita t[eé]cnica', texto_lower):
            exigencias_encontradas.append("Visita técnica ou vistoria prévia")
        if re.search(r'garantia de proposta', texto_lower):
            exigencias_encontradas.append("Garantia de proposta")
        if re.search(r'balan[çc]o patrimonial', texto_lower):
            exigencias_encontradas.append("Balanço patrimonial atualizado")
            
        if exigencias_encontradas:
             resumo["exigencias"] = exigencias_encontradas
        else:
             resumo["exigencias"] = ["Nenhuma exigência especial detectada"]

        match_data = re.search(r'(?:abertura(?: da sess[aã]o)?|data(?: e hora)?|sess[aã]o p[uú]blica)\s*:?\s*(\d{2}/\d{2}/\d{4}(?:\s*(?:[aà]s|-)\s*\d{2}:\d{2})?)', texto_lower)
        if match_data:
            resumo["data_sessao"] = match_data.group(1)

        return {
            "sucesso": True,
            "resumo": resumo,
            "pode_baixar": True,
            "url_resolvida": url_pdf
        }

    except Exception as e:
        print(f"Erro ao processar PDF: {e}")
        return {"sucesso": False, "mensagem": "Erro interno ao processar o arquivo. Clique abaixo para baixar o arquivo completo.", "pode_baixar": True, "url_resolvida": url_edital}
