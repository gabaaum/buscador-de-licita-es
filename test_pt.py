import requests

def test_api():
    url = "https://portaldatransparencia.gov.br/licitacoes/resultado"
    params = {
        "paginacaoSimples": "true",
        "tamanhoPagina": "15",
        "offset": "0",
        "direcaoOrdenacao": "desc",
        "colunaOrdenacao": "dataPublicacao",
        "colunasSelecionadas": "numeroLicitacao,dataPublicacao,orgaoSuperior,orgao,objeto,situacao,valorEstimadoLicitacao"
    }
    # It might return json or HTML.
    # Let's try /paginacao as well
    
    url_pag = "https://portaldatransparencia.gov.br/licitacoes/resultado/paginacao"
    try:
        r = requests.get(url_pag, params=params, headers={"Accept": "application/json"})
        print(r.status_code)
        print(r.text[:500])
    except Exception as e:
        print(e)

if __name__ == "__main__":
    test_api()