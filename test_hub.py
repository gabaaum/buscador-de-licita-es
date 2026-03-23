import asyncio
from scraper_pagas import LicitacoesPagasScraper
from scraper_sp import LicitacoesPagasScraperSP
from scraper_rj import LicitacoesPagasScraperRJ
from scraper_mg import LicitacoesPagasScraperMG

async def test_scrapers():
    print("--- Testando Esfera Federal ---")
    scraper_fed = LicitacoesPagasScraper(headless=True)
    res_fed = await scraper_fed.scrape("2024-01-01", "2024-01-31", "Ministério da Saúde", "", "")
    print(f"Federal retornou {len(res_fed)} resultados")
    if res_fed:
        print(f"Exemplo: {res_fed[0]}")

    print("\n--- Testando Esfera SP ---")
    scraper_sp = LicitacoesPagasScraperSP(headless=True)
    res_sp = await scraper_sp.scrape("2024-01-01", "2024-01-31", "", "", "")
    print(f"SP retornou {len(res_sp)} resultados")
    if res_sp:
        print(f"Exemplo: {res_sp[0]}")

    print("\n--- Testando Esfera RJ ---")
    scraper_rj = LicitacoesPagasScraperRJ(headless=True)
    res_rj = await scraper_rj.scrape("2024-01-01", "2024-01-31", "", "", "")
    print(f"RJ retornou {len(res_rj)} resultados")
    if res_rj:
        print(f"Exemplo: {res_rj[0]}")

    print("\n--- Testando Esfera MG ---")
    scraper_mg = LicitacoesPagasScraperMG(headless=True)
    res_mg = await scraper_mg.scrape("2024-01-01", "2024-01-31", "", "", "")
    print(f"MG retornou {len(res_mg)} resultados")
    if res_mg:
        print(f"Exemplo: {res_mg[0]}")

if __name__ == "__main__":
    asyncio.run(test_scrapers())
