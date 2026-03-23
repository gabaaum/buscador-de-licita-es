import requests
import json
import re

def get_report_info():
    """
    Função mock que pega os dados iniciais do HTML embed do PowerBI.
    Na realidade teríamos que acessar o embed_url ou pegar do response principal.
    Mas para nossa POC, vamos pegar um payload mockado ou os recursos se possível.
    """
    return {
        "reportId": "b6f0013b-e854-47b2-8edb-c3fdb3620db4", 
        "resourceKey": "b13df184-e3f8-45e0-b9df-7d4db3b9b47f" # Chave real pode precisar vir da inicialização
    }

def main():
    print("Criando POC para extração PBI...")
    # Lendo o arquivo json interceptado para testar o parser
    try:
        with open('pbi_response.json', 'r') as f:
            data = json.load(f)
            
            # Navegar no DS (Data Shapes)
            results = data.get("results", [])
            if not results:
                print("Nenhum resultado encontrado no JSON")
                return
                
            res_data = results[0].get("result", {}).get("data", {})
            dsr = res_data.get("dsr", {})
            ds = dsr.get("DS", [])
            
            if not ds:
                print("Nenhum Data Shape encontrado")
                return
                
            first_ds = ds[0]
            value_dicts = first_ds.get("ValueDicts", {})
            ph = first_ds.get("PH", [])
            
            print(f"ValueDicts: {list(value_dicts.keys())}")
            
            if ph:
                dm0 = ph[0].get("DM0", [])
                print(f"DM0 Records: {len(dm0)}")
                # Aprofundar a extração aqui...
                
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == '__main__':
    main()
