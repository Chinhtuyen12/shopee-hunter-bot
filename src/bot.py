#!/usr/bin/env python3
"""Shopee Hunter Bot - Selenium Version"""

import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

async def search_shopee_selenium(keyword: str, limit: int = 5):
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        import time

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        driver = webdriver.Chrome(options=options)
        driver.get(f"https://shopee.vn/search?keyword={keyword.replace(' ', '%20')}")

        await asyncio.sleep(6)  # Chờ load

        products = []
        items = driver.find_elements(By.CSS_SELECTOR, 'div[data-sqe="item"]')[:10]

        for item in items:
            try:
                name = item.find_element(By.CSS_SELECTOR, 'div[data-sqe="name"] div').text.strip()
                price = item.find_element(By.CSS_SELECTOR, 'div[data-sqe="price"] span').text.strip()
                link_tag = item.find_element(By.TAG_NAME, 'a')
                link = link_tag.get_attribute('href')

                if name and link:
                    full_link = "https://shopee.vn" + link if not link.startswith("http") else link
                    products.append({
                        "name": name[:70],
                        "price": price,
                        "link": full_link
                    })
                    if len(products) >= limit:
                        break
            except:
                continue

        driver.quit()
        return products[:limit]

    except Exception as e:
        log.error(f"Selenium error: {e}")
        return [{"name": f"Lỗi Selenium: {str(e)}", "price": "", "link": ""}]


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text.strip()
    user_id = str(update.effective_user.id)

    if os.getenv("ALLOWED_USER_ID") and user_id != os.getenv("ALLOWED_USER_ID"):
        await update.message.reply_text("❌ Bạn không có quyền sử dụng bot.")
        return

    if text.startswith('/start'):
        await update.message.reply_text("👋 Nhập từ khóa sản phẩm bạn muốn tìm...")
        return

    await update.message.reply_text(f"🔍 Đang tìm top 5 sản phẩm cho **{text}**...", parse_mode='Markdown')

    products = await search_shopee_selenium(text, limit=5)

    if not products:
        await update.message.reply_text("❌ Không tìm thấy sản phẩm. Thử từ khóa khác.")
        return

    response = f"**🔎 Top 5 sản phẩm cho:** {text}\n\n"
    for i, p in enumerate(products, 1):
        response += f"{i}. **{p['name']}**\n"
        response += f"💰 {p['price']}\n"
        response += f"🔗 [Mua ngay]({p['link']})\n\n"

    await update.message.reply_text(response, parse_mode='Markdown', disable_web_page_preview=True)


def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        log.error("TELEGRAM_TOKEN not set")
        return

    app = Application.builder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    log.info("🚀 Shopee Hunter Bot with Selenium started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
