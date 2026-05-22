#!/usr/bin/env python3
"""Shopee Hunter Bot - Tối ưu tìm kiếm"""

import os
import logging
import httpx
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

async def search_shopee(keyword: str, limit: int = 6):
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return [{"name": "❌ Chưa set SERPAPI_KEY", "price": "", "link": ""}]

    products = []
    queries = [
        f"{keyword} shopee",
        f"{keyword} site:shopee.vn",
        keyword
    ]

    try:
        async with httpx.AsyncClient(timeout=25) as client:
            for q in queries:
                resp = await client.get(
                    "https://serpapi.com/search",
                    params={
                        "engine": "google",
                        "q": q,
                        "api_key": api_key,
                        "num": 20,
                        "gl": "vn",
                        "hl": "vi"
                    }
                )
                data = resp.json()

                # Lấy từ shopping_results
                for item in data.get("shopping_results", []):
                    if "shopee.vn" in item.get("link", "").lower():
                        products.append({
                            "name": item.get("title", "N/A"),
                            "price": item.get("price", "N/A"),
                            "rating": item.get("rating", "4.8"),
                            "sold": item.get("sold", "N/A"),
                            "link": item.get("link", "#")
                        })
                    if len(products) >= limit:
                        break

                if len(products) >= limit:
                    break

        return products[:limit]

    except Exception as e:
        log.error(f"Search error: {e}")
        return [{"name": "Lỗi tìm kiếm, thử lại sau", "price": "", "link": ""}]


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text.strip()
    user_id = str(update.effective_user.id)

    if os.getenv("ALLOWED_USER_ID") and user_id != os.getenv("ALLOWED_USER_ID"):
        await update.message.reply_text("❌ Bạn không có quyền sử dụng bot.")
        return

    if text.startswith('/start'):
        await update.message.reply_text("👋 Gõ từ khóa sản phẩm bạn muốn tìm...")
        return

    await update.message.reply_text(f"🔍 Đang tìm sản phẩm cho **{text}**...", parse_mode='Markdown')

    products = await search_shopee(text, limit=5)

    if not products or len(products) == 0:
        await update.message.reply_text("❌ Không tìm thấy sản phẩm phù hợp.\n\nThử từ khóa khác hoặc chi tiết hơn (ví dụ: `tai nghe bluetooth` thay vì `tai nghe`)")
        return

    response = f"**🔎 Kết quả tìm kiếm:** {text}\n\n"
    for i, p in enumerate(products, 1):
        response += f"{i}. **{p['name']}**\n"
        response += f"💰 {p['price']} | ⭐ {p.get('rating', 'N/A')}\n"
        response += f"🔗 [Mua ngay]({p['link']})\n\n"

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
