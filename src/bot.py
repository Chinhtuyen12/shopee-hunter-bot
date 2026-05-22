#!/usr/bin/env python3
"""Shopee Hunter Bot - Tối ưu tìm kiếm mạnh"""

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
        return [{"name": "❌ Chưa set SERPAPI_KEY", "price": "", "link": ""}]

    search_queries = [
        f"{keyword} shopee",
        f"{keyword} site:shopee.vn",
        keyword,
        f"mua {keyword}"
    ]

    products = []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            for q in search_queries:
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

                # Ưu tiên link sản phẩm trực tiếp
                for item in data.get("shopping_results", []):
                    link = item.get("link", "")
                    if "shopee.vn/product/" in link or "shopee.vn/" in link:
                        products.append({
                            "name": item.get("title", "N/A"),
                            "price": item.get("price", "N/A"),
                            "rating": item.get("rating", "4.8"),
                            "link": link
                        })
                        if len(products) >= limit:
                            break

                if len(products) < limit:
                    for item in data.get("organic_results", []):
                        link = item.get("link", "")
                        if "shopee.vn" in link and len(link) > 50:  # link dài thường là link sản phẩm
                            products.append({
                                "name": item.get("title", "N/A"),
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
        await update.message.reply_text("👋 Nhập từ khóa sản phẩm bạn muốn tìm (ví dụ: bình đựng nước mini, tai nghe bluetooth...)")
        return

    await update.message.reply_text(f"🔍 Đang tìm top sản phẩm cho **{text}**...", parse_mode='Markdown')

    products = await search_shopee(text, limit=5)

    if not products:
        await update.message.reply_text("❌ Vẫn không tìm thấy. Thử từ khóa đơn giản hơn (ví dụ: `tai nghe`, `bình nước`, `áo thun`)")
        return

    response = f"**🔎 Top sản phẩm cho:** {text}\n\n"
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
