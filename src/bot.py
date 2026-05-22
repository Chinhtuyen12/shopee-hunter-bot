#!/usr/bin/env python3
"""Shopee Hunter Bot - Top 5 Sản Phẩm + So Sánh"""

import os
import logging
import httpx
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

async def search_shopee(keyword: str, limit: int = 5):
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return []

    try:
        async with httpx.AsyncClient(timeout=25) as client:
            resp = await client.get(
                "https://serpapi.com/search",
                params={
                    "engine": "google_shopping",
                    "q": keyword,
                    "api_key": api_key,
                    "num": 20,
                    "gl": "vn",
                    "hl": "vi"
                }
            )
            data = resp.json()

        products = []
        for item in data.get("shopping_results", [])[:limit*2]:
            link = item.get("link", "")
            if "shopee.vn/product/" in link:   # Chỉ lấy link sản phẩm trực tiếp
                products.append({
                    "name": item.get("title", "N/A"),
                    "price": item.get("price", "N/A"),
                    "rating": item.get("rating", "4.8"),
                    "sold": item.get("sold", "N/A"),
                    "link": link
                })
                if len(products) >= limit:
                    break

        return products[:limit]

    except Exception as e:
        log.error(f"Search error: {e}")
        return []


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text.strip()
    user_id = str(update.effective_user.id)

    if os.getenv("ALLOWED_USER_ID") and user_id != os.getenv("ALLOWED_USER_ID"):
        await update.message.reply_text("❌ Bạn không có quyền sử dụng bot.")
        return

    if text.startswith('/start'):
        await update.message.reply_text(
            "👋 *Shopee Hunter Bot*\n\n"
            "Nhập từ khóa sản phẩm bạn muốn tìm.\n"
            "Ví dụ:\n"
            "`bình đựng nước mini`\n"
            "`tai nghe bluetooth`\n"
            "`so sánh tai nghe airpods`"
        , parse_mode='Markdown')
        return

    await update.message.reply_text(f"🔍 Đang tìm top 5 sản phẩm cho **{text}**...", parse_mode='Markdown')

    products = await search_shopee(text, limit=5)

    if not products:
        await update.message.reply_text("❌ Không tìm thấy sản phẩm phù hợp.\nThử từ khóa khác hoặc cụ thể hơn.")
        return

    # Tạo bảng
    response = f"**🔥 Top 5 sản phẩm cho:** {text}\n\n"
    response += "| STT | Tên sản phẩm | Giá | Đánh giá | Đã bán | Link |\n"
    response += "|-----|--------------|-----|----------|--------|------|\n"

    for i, p in enumerate(products, 1):
        response += f"| {i} | {p['name'][:45]}... | {p['price']} | ⭐ {p['rating']} | {p.get('sold','N/A')} | [Mua]({p['link']}) |\n"

    response += "\n💡 Click vào link để mua trực tiếp.\nBạn muốn tôi so sánh chi tiết 2-3 sản phẩm nào không?"

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
