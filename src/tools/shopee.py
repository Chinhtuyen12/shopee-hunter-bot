import asyncio
import os
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def search_shopee(keyword: str, limit: int = 5):
    endpoint = os.getenv("BROWSER_PLAYWRIGHT_ENDPOINT")
    
    if not endpoint:
        return [{"name": "❌ Chưa cấu hình Browserless. Vui lòng kiểm tra Variables.", "price": "", "rating": "", "sold": "", "link": ""}]

    try:
        async with async_playwright() as p:
            # Kết nối với Browserless
            browser = await p.chromium.connect(endpoint)
            page = await browser.new_page()
            
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })

            url = f"https://shopee.vn/search?keyword={keyword.replace(' ', '%20')}"
            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(5000)   # Chờ load sản phẩm

            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')

            products = []
            items = soup.select('div[data-sqe="item"]')[:10]

            for item in items:
                try:
                    name_elem = item.select_one('div[data-sqe="name"] div')
                    price_elem = item.select_one('div[data-sqe="price"] span')
                    link_tag = item.select_one('a')

                    name = name_elem.text.strip() if name_elem else "Không có tên"
                    price = price_elem.text.strip() if price_elem else "N/A"
                    link = "https://shopee.vn" + link_tag['href'] if link_tag else ""

                    rating = item.select_one('span[class*="rating"]')
                    sold = item.select_one('div[class*="sold"]')

                    if name and link:
                        products.append({
                            "name": name[:75],
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
        return [{"name": f"❌ Lỗi kết nối Browserless: {str(e)}", "price": "", "rating": "", "sold": "", "link": ""}]
