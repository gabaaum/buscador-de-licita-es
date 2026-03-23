import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await Stealth().apply_stealth_async(page)
        
        await page.goto("https://pncp.gov.br/app/editais", wait_until="networkidle")
        await page.wait_for_selector("input#searchbox", timeout=15000)
        
        await page.fill("input#searchbox", "carros")
        await page.press("input#searchbox", "Enter")
        
        print("Aguardando carregamento da rede...")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(5000)
        
        cards = await page.query_selector_all("pncp-item")
        if not cards:
            cards = await page.query_selector_all(".br-card")
            
        if cards:
            html = await cards[0].inner_html()
            print("--- HTML DO CARD ---")
            print(html)
        else:
            print("Nenhum card encontrado.")
            # Let's save the HTML to see what's loaded
            content = await page.content()
            with open("pncp_debug.html", "w") as f:
                f.write(content)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect())
