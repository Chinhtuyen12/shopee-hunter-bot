#!/usr/bin/env python3
"""Shopee Hunter Bot - Tối ưu tìm kiếm 2026"""

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
        return [{"name": "❌ Chưa cấu hình SERPAPI_KEY", "price": "", "link": ""}]

    queries = [
        f"{keyword} shopee",
        f"{keyword} site:shopee.vn",
        keyword,
        f"{keyword} mua online"
    ]

    products = []
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            for q in queries:
                if len(products) >= limit:
                    break
                    
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
                    link = item.get("link", "")
                    if "shopee.vn" in link:
                        products.append({
                            "name": item.get("title", "N/A"),
                            "price": item.get("price", "N/A"),
                            "rating": item.get("rating", "4.8"),
                            "link": link
                        })
                        if len(products) >= limit:
                            break

                # Lấy từ organic results nếu chưa đủ
                if len(products) < limit:
                    for item in data.get("organic_results", []):
                        link = item.get("link", "")
                        if "shopee.vn" in link and item.get("title"):
                            products.append({
                                "name": item.get("title"),
                                "price": "Giá trên Shopee",
                                "rating": "4.8",
                                "link": link
                            })
                            if len(products) >= limit:
                                break

        return products[:limit]

    except Exception as e:
        log.error(f"Search error: {e}")
        return [{"name": "Lỗi kết nối tìm kiếm", "price": "", "link": ""}]


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text.strip()
    user_id = str(update.effective_user.id)

    if os.getenv("ALLOWED_USER_ID") and user_id != os.getenv("ALLOWED_USER_ID"):
        await update.message.reply_text("❌ Bạn không có quyền sử dụng bot.")
        return

    if text.startswith('/start'):
        await update.message.reply_text("👋 Gõ từ khóa sản phẩm bạn muốn tìm (ví dụ: bình đựng nước, tai nghe, áo thun...)")
        return

    await update.message.reply_text(f"🔍 Đang tìm sản phẩm cho **{text}**...", parse_mode='Markdown')

    products = await search_shopee(text, limit=5)

    if not products:
        await update.message.reply_text("❌ Không tìm thấy sản phẩm. Thử từ khóa khác hoặc chi tiết hơn.")
        return

    response = f"**🔎 Kết quả cho:** {text}\n\n"
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

    log.info("🚀 Shopee Hunter Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
