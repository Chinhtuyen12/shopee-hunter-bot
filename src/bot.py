#!/usr/bin/env python3
"""Shopee Hunter Bot"""

import asyncio
import json
import logging
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# === FIX IMPORT PATH ===
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# =======================

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Import tool
from tools.shopee import search_shopee

SYSTEM_PROMPT = """
Bạn là **Shopee Hunter Bot** - chuyên gia săn hàng Shopee thông minh.

Khi người dùng gửi từ khóa:
- Tìm Top 5 sản phẩm có lượt bán cao + rating tốt
- So sánh giá, shop, khuyến mãi
- Đưa khuyến nghị rõ ràng
- Trả lời ngắn gọn, dễ đọc, có emoji
"""

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")
    def log_message(self, fmt, *args):
        pass

def run_health_server():
    server = HTTPServer(("0.0.0.0", 8080), HealthHandler)
    log.info("Health server listening on :8080")
    server.serve_forever()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text.strip()
    user_id = update.effective_user.id

    allowed_id = os.getenv("ALLOWED_USER_ID")
    if allowed_id and str(user_id) != str(allowed_id):
        await update.message.reply_text("❌ Bạn không có quyền sử dụng bot này.")
        return

    if text.startswith('/start'):
        await update.message.reply_text(
            "👋 Chào bạn! Tôi là *Shopee Hunter Bot*\n\n"
            "Gõ từ khóa bạn muốn tìm kiếm, ví dụ:\n"
            "`tai nghe bluetooth`\n"
            "`quần jeans nam`\n"
            "`kem dưỡng da`",
            parse_mode='Markdown'
        )
    else:
        keyword = text.strip()
        await update.message.reply_text(f"🔍 Đang tìm top sản phẩm cho **{keyword}**...", parse_mode='Markdown')
        
        products = await search_shopee(keyword, limit=5)
        
        if not products or "Lỗi" in products[0].get("name", ""):
            await update.message.reply_text("❌ Không tìm thấy sản phẩm. Thử từ khóa khác nhé!")
            return

        analysis = await analyze_shopee_products(products, keyword)
        await update.message.reply_text(analysis, parse_mode='Markdown', disable_web_page_preview=True)


async def analyze_shopee_products(products: list, keyword: str):
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )

        prompt = f"""
Từ khóa: {keyword}

Danh sách sản phẩm:
{json.dumps(products, ensure_ascii=False, indent=2)}

Phân tích và trả lời đẹp:
- Top 5 sản phẩm
- So sánh ngắn gọn
- Khuyến nghị sản phẩm tốt nhất
"""

        response = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gemini-2.0-flash"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content

    except Exception as e:
        log.error(f"LLM Error: {e}")
        fallback = "Danh sách sản phẩm:\n"
        for i, p in enumerate(products, 1):
            fallback += f"{i}. {p.get('name')}\n   💰 {p.get('price')} | ⭐ {p.get('rating')}\n   🔗 {p.get('link')}\n\n"
        return fallback


def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_TOKEN not set")

    threading.Thread(target=run_health_server, daemon=True).start()

    app = Application.builder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("start", handle_message))

    log.info("🚀 Shopee Hunter Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
