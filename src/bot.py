#!/usr/bin/env python3
"""Shopee Hunter Bot - Professional Version"""

import os
import logging
import sys
import httpx
import json
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Logging
logging.basicConfig(
    format='%(asctime)s | %(levelname)s | %(message)s',
    level=logging.INFO,
    datefmt='%H:%M:%S'
)
log = logging.getLogger(__name__)

# ====================== HEALTH SERVER ======================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")
    def log_message(self, format, *args):
        pass  # Tắt log spam

def run_health_server():
    server = HTTPServer(("0.0.0.0", 8080), HealthHandler)
    log.info("Health server listening on port 8080")
    server.serve_forever()

# ====================== SEARCH FUNCTION ======================
async def search_shopee(keyword: str, limit: int = 5):
    """Tìm kiếm sản phẩm trên Shopee qua SerpAPI"""
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return [{"name": "❌ Chưa cấu hình SERPAPI_KEY", "price": "", "link": ""}]

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                "https://serpapi.com/search",
                params={
                    "engine": "google",
                    "q": f"{keyword} site:shopee.vn",
                    "api_key": api_key,
                    "num": 15,
                    "gl": "vn",
                    "hl": "vi"
                }
            )
            data = response.json()

        products = []
        # Lấy từ shopping results
        for item in data.get("shopping_results", [])[:limit]:
            products.append({
                "name": item.get("title", "Không có tên"),
                "price": item.get("price", "Liên hệ"),
                "link": item.get("link", "#")
            })

        # Nếu không có, lấy từ organic results
        if not products:
            for item in data.get("organic_results", [])[:limit]:
                if "shopee.vn" in item.get("link", ""):
                    products.append({
                        "name": item.get("title", "Không có tên"),
                        "price": "Giá trên Shopee",
                        "link": item.get("link", "#")
                    })

        return products[:limit]

    except Exception as e:
        log.error(f"Search error: {e}")
        return [{"name": f"Lỗi tìm kiếm: {str(e)}", "price": "", "link": ""}]


# ====================== HANDLER ======================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user_id = str(update.effective_user.id)

    # Kiểm tra quyền
    allowed_id = os.getenv("ALLOWED_USER_ID")
    if allowed_id and user_id != allowed_id:
        await update.message.reply_text("❌ Bạn không có quyền sử dụng bot này.")
        return

    if text.startswith('/start'):
        await update.message.reply_text(
            "👋 *Chào bạn!* Tôi là Shopee Hunter Bot\n\n"
            "Gõ từ khóa sản phẩm bạn muốn tìm, ví dụ:\n"
            "`tai nghe bluetooth`\n"
            "`áo thun nam`\n"
            "`kem dưỡng da`",
            parse_mode='Markdown'
        )
        return

    if text.lower() in ['/help', 'help']:
        await update.message.reply_text("💡 Gõ từ khóa sản phẩm bạn muốn tìm...")
        return

    # Tìm kiếm
    await update.message.reply_text(f"🔍 Đang tìm kiếm sản phẩm cho **{text}**...", parse_mode='Markdown')

    products = await search_shopee(text, limit=5)

    if not products or not products[0].get('link'):
        await update.message.reply_text("❌ Không tìm thấy sản phẩm phù hợp. Thử từ khóa khác nhé!")
        return

    # Format kết quả
    response = f"**🔎 Kết quả cho: {text}**\n\n"
    for i, p in enumerate(products, 1):
        response += f"{i}. **{p['name']}**\n"
        response += f"💰 {p['price']}\n"
        response += f"🔗 [Mua ngay]({p['link']})\n\n"

    await update.message.reply_text(response, parse_mode='Markdown', disable_web_page_preview=True)


# ====================== MAIN ======================
def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        log.error("❌ TELEGRAM_TOKEN chưa được thiết lập!")
        return

    # Start health server
    threading.Thread(target=run_health_server, daemon=True).start()

    app = Application.builder().token(token).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    log.info("🚀 Shopee Hunter Bot started successfully!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
