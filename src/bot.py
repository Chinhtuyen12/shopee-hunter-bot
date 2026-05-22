#!/usr/bin/env python3
"""Shopee Hunter Bot - Simple Version using SerpAPI"""

import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import httpx
import json

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

async def search_shopee_serpapi(keyword: str, limit: int = 5):
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return [{"name": "Chưa cấu hình SERPAPI_KEY", "price": "", "link": ""}]

    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": f"{keyword} site:shopee.vn",
        "api_key": api_key,
        "num": limit * 2
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url, params=params)
        data = response.json()

    products = []
    for result in data.get("shopping_results", [])[:limit]:
        products.append({
            "name": result.get("title", "N/A"),
            "price": result.get("price", "N/A"),
            "link": result.get("link", "#")
        })
    return products


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    text = update.message.text.strip()

    if text.startswith('/start'):
        await update.message.reply_text("👋 Gõ từ khóa sản phẩm bạn muốn tìm trên Shopee...")
        return

    await update.message.reply_text(f"🔍 Đang tìm trên Shopee: **{text}**...", parse_mode='Markdown')

    products = await search_shopee_serpapi(text, limit=5)

    if not products:
        await update.message.reply_text("❌ Không tìm thấy sản phẩm.")
        return

    response = f"**Kết quả Shopee cho: {text}**\n\n"
    for i, p in enumerate(products, 1):
        response += f"{i}. **{p['name']}**\n💰 {p['price']}\n🔗 {p['link']}\n\n"

    await update.message.reply_text(response, parse_mode='Markdown', disable_web_page_preview=True)


def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        log.error("TELEGRAM_TOKEN not set")
        return

    app = Application.builder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    log.info("🚀 Shopee Hunter Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
