import requests
from datetime import datetime
import datetime as dt_module
import locale

# Configuração para formatar moeda
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    pass

class PNCPContratosScraper:
    def __init__(self):
        self.base_url = "https://pncp.gov.br/api/consulta/v1"
        self.headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def format_currency(self, value):
        if value is None:
            return "R$ 0,00"
        try:
            return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return "R$ 0,00"

    def format_date(self, date_str):
        if not date_str:
            return "N/A"
        try:
            # Assumindo formato ISO como "2023-10-15T00:00:00"
            dt_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt_obj.strftime("%d/%m/%Y")
        except:
            return date_str[:10] if len(date_str) >= 10 else date_str

    def _get_contracts(self, term, data_inicial, data_final, uf, page=1):
        # A API de contratos exige obrigatoriamente dataInicial e dataFinal e o período não pode ser maior que 365 dias
        params = {
            "q": term,
            "pagina": page,
            "tamanhoPagina": 50,
        }
        
        if not data_inicial:
            # Default para os últimos 360 dias
            data_inicial = (datetime.now() - dt_module.timedelta(days=360)).strftime("%Y-%m-%d")
        if not data_final:
            data_final = datetime.now().strftime("%Y-%m-%d")
            
        params["dataInicial"] = data_inicial.replace("-", "")
        params["dataFinal"] = data_final.replace("-", "")

        url = f"{self.base_url}/contratos"
        
        print(f"Fazendo request PNCP: {url} com params: {params}")
        
        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=20)
            if response.status_code == 200:
                print(f"Retornou {len(response.json().get('data', []))} resultados na página {page}")
                return response.json()
            else:
                print(f"Erro API PNCP: HTTP {response.status_code} - {response.text}")
                return {"data": []}
        except Exception as e:
            print(f"Exception chamando PNCP: {e}")
            return {"data": []}

    def scrape(self, term, uf, data_inicial, data_final, numero_licitacao=None):
        print(f"Iniciando busca PNCP Contratos: termo='{term}', uf='{uf}', data_inicial={data_inicial}, data_final={data_final}, numero_licitacao={numero_licitacao}")
        results = []
        
        page = 1
        has_more = True
        max_pages = 5
        
        while has_more and page <= max_pages:
            data = self._get_contracts(term, data_inicial, data_final, uf, page)
            items = data.get("data", [])
            
            if not items:
                break
                
            for item in items:
                # Filtrar pelo número do contrato/edital se fornecido
                num_contrato_str = item.get("numeroContratoEmpenho", "")
                if numero_licitacao and numero_licitacao not in num_contrato_str:
                    continue
                    
                unidade_uf = item.get("unidadeOrgao", {}).get("ufSigla", "")
                if uf and uf != "Todos" and unidade_uf != uf:
                    continue
                    
                orgao = item.get("orgaoEntidade", {}).get("razaoSocial", "Órgão Não Identificado")
                
                # A API de contratos retorna fornecedores de forma diferente
                empresa_nome = item.get("nomeRazaoSocialFornecedor")
                empresa_cnpj = item.get("niFornecedor")
                
                # Fallback para caso o fornecedor venha dentro de um objeto (como em outras rotas do PNCP)
                if not empresa_nome:
                    fornecedor = item.get("fornecedor", {})
                    empresa_nome = fornecedor.get("razaoSocial", "Empresa Não Identificada")
                    empresa_cnpj = fornecedor.get("ni", "")
                
                if not empresa_nome and "Empresa Não" in empresa_nome:
                    empresa_nome = "Empresa Não Identificada"
                    
                empresa = f"{empresa_nome} (CNPJ/CPF: {empresa_cnpj})" if empresa_cnpj and empresa_nome != "Empresa Não Identificada" else (empresa_nome or "Empresa Não Identificada")
                
                valor_global = item.get("valorGlobal", 0)
                valor_parcela = item.get("valorParcela", 0)
                valor_acumulado = item.get("valorAcumulado", valor_parcela)
                
                results.append({
                    "numero_contrato": item.get("numeroContratoEmpenho", "N/A"),
                    "orgao": orgao,
                    "empresa": empresa,
                    "objeto": item.get("objetoContrato", "N/A"),
                    "valor_homologado": self.format_currency(valor_global),
                    "valor_homologado_raw": valor_global,
                    "valor_empenhado": self.format_currency(valor_acumulado),
                    "data_assinatura": self.format_date(item.get("dataAssinatura"))
                })
                
            total_pages = data.get("totalPaginas", 1)
            if page >= total_pages:
                has_more = False
            else:
                page += 1

        print(f"Busca finalizada. Encontrados {len(results)} contratos após filtro de UF.")
        return results

if __name__ == "__main__":
    # Teste
    scraper = PNCPContratosScraper()
    res = scraper.scrape("computadores", "SP", None, None)
    for r in res[:2]:
        print(r)
