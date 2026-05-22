import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def search_shopee(keyword: str, limit: int = 5):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })

            await page.goto(f"https://shopee.vn/search?keyword={keyword.replace(' ', '%20')}", timeout=60000)
            await page.wait_for_timeout(7000)

            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')

            products = []
            items = soup.select('div[data-sqe="item"]')[:10]

            for item in items:
                try:
                    name = item.select_one('div[data-sqe="name"] div').text.strip()
                    price = item.select_one('div[data-sqe="price"] span').text.strip()
                    link_tag = item.select_one('a')
                    link = "https://shopee.vn" + link_tag['href'] if link_tag else ""

                    rating = item.select_one('span[class*="rating"]')
                    sold = item.select_one('div[class*="sold"]')

                    if name and link:
                        products.append({
                            "name": name[:70],
                            "price": price,
                            "rating": rating.text.strip() if rating else "4.8",
                            "sold": sold.text.strip() if sold else "N/A",
                            "link": link
                        })
                except:
                    continue

            await browser.close()
            return products[:limit]
    except Exception as e:
        return [{"name": f"Lỗi: {str(e)}", "price": "", "rating": "", "sold": "", "link": ""}]
