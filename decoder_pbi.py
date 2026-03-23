import json
import requests
import re

def extract_resource_key(html):
    match = re.search(r"resourceKey\s*:\s*['\"]([^'\"]+)['\"]", html)
    if match:
        return match.group(1)
    return None

def fetch_table():
    # Carregar o payload da tabela que pegamos
    with open('pbi_table_request.json', 'r') as f:
        payload = json.load(f)

    # Obter os metadados do PowerBI no portal
    print("Obtendo resourceKey do HTML do portal SP...")
    html_resp = requests.get("https://www.transparencia.sp.gov.br/Home/ExecutaLicita", verify=False)
    resource_key = extract_resource_key(html_resp.text)
    
    if not resource_key:
        print("Aviso: resourceKey não encontrado no HTML principal, tentando fallback (o PBI embed tem outro flow).")
        # Vamos rodar no mock ou tentar o PowerBI config nativo se necessário

    # Fazer a requisição
    url = "https://wabi-brazil-south-b-primary-api.analysis.windows.net/public/reports/querydata?synchronous=true"
    
    headers = {
        "Content-Type": "application/json",
        "X-PowerBI-ResourceKey": "b13df184-e3f8-45e0-b9df-7d4db3b9b47f" # Chave real extraida da interface
    }
    
    # Aqui precisamos de um recurso de autorização ou tenant
    # Como não temos tudo ainda no mock, vamos rodar uma requisição de teste
    try:
        resp = requests.post(url, headers=headers, json=payload, verify=False)
        print(f"Status Code: {resp.status_code}")
        if resp.status_code == 200:
            with open("table_resp.json", "w") as f:
                json.dump(resp.json(), f)
            print("Resposta salva em table_resp.json")
            return resp.json()
        else:
            print("Erro:", resp.text)
    except Exception as e:
        print("Erro na requisição:", e)
        
    return None

def parse_pbi_response(data):
    if not data:
        return
        
    results = data.get("results", [])
    if not results:
        print("Sem dados")
        return
        
    ds = results[0].get("result", {}).get("data", {}).get("dsr", {}).get("DS", [])
    if not ds:
        print("Sem Data Shapes")
        return
        
    first_ds = ds[0]
    value_dicts = first_ds.get("ValueDicts", {})
    
    # Decodificar os dicionários
    dict_map = {}
    for k, v in value_dicts.items():
        if isinstance(v, list):
            dict_map[k] = v
    
    ph = first_ds.get("PH", [])
    if not ph:
        return
        
    dm0 = ph[0].get("DM0", [])
    
    # Lógica de decodificação das linhas (C)
    # A estrutura DM0 tem um array por linha ou nós hierárquicos
    print(f"\nEncontradas {len(dm0)} linhas brutas (DM0).")
    
    parsed_rows = []
    
    # Manter estado para valores repetidos (Flag R)
    last_row_state = {}
    
    for item in dm0:
        c_array = item.get("C", [])
        
        # PowerBI usa flag R para indicar repetição. Se R existir, os campos de `C` contêm bitmask
        r_flag = item.get("R")
        
        # Construir linha real baseada nos índices dos dicionários
        current_row = []
        for i, val in enumerate(c_array):
            # Tentar resolver usando dicionário se val for um índice inteiro (exemplo muito simplificado)
            resolved_val = val
            # Em um caso real, cruzaríamos com os metadados do select para saber a tipagem
            
            # TODO: Lógica refinada baseada no select real
            current_row.append(resolved_val)
            
        parsed_rows.append(current_row)

    print("\nAmostra de Linhas Extraídas:")
    for r in parsed_rows[:5]:
        print(r)

if __name__ == "__main__":
    resp_data = fetch_table()
    if resp_data:
        parse_pbi_response(resp_data)

