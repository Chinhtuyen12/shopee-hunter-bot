#!/usr/bin/env python3
"""Shopee Hunter Bot"""

import asyncio
import json
import logging
import os
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

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

# Logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("shopee-hunter-bot")

# System Prompt
SYSTEM_PROMPT = """
Bạn là **Shopee Hunter Bot** - chuyên gia săn hàng Shopee thông minh và đáng tin cậy.

Khi người dùng gửi từ khóa:
- Tìm Top 5 sản phẩm có lượt bán cao + rating tốt nhất
- So sánh giá, khuyến mãi, shop giữa các sản phẩm
- Đưa ra khuyến nghị rõ ràng sản phẩm đáng mua nhất
- Viết ngắn gọn, dễ hiểu, dùng emoji
"""

# Health Check Server
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

# Handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text.strip()
    user_id = update.effective_user.id

    # Kiểm tra quyền
    allowed_id = os.getenv("ALLOWED_USER_ID")
    if allowed_id and str(user_id) != str(allowed_id):
        await update.message.reply_text("❌ Bạn không có quyền sử dụng bot này.")
        return

    if text.startswith('/start'):
        await update.message.reply_text(
            "👋 Chào bạn! Tôi là *Shopee Hunter Bot*\n\n"
            "Gõ từ khóa bạn muốn tìm, ví dụ:\n"
            "`tai nghe bluetooth`\n"
            "`quần jeans nam`\n"
            "`kem dưỡng trắng da`\n\n"
            "Tôi sẽ tìm Top 5 sản phẩm tốt nhất cho bạn!",
            parse_mode='Markdown'
        )

    elif text.lower() in ['/help', 'help']:
        await update.message.reply_text("💡 Gõ từ khóa sản phẩm bạn muốn tìm...")

    else:
        keyword = text.strip()
        await update.message.reply_text(f"🔍 Đang tìm kiếm top sản phẩm cho **{keyword}**...", parse_mode='Markdown')
        
        products = await search_shopee(keyword, limit=5)
        
        if not products or "Lỗi" in products[0].get("name", ""):
            await update.message.reply_text("❌ Không tìm thấy sản phẩm nào. Thử từ khóa khác nhé!")
            return

        # Phân tích bằng LLM
        analysis = await analyze_shopee_products(products, keyword)
        await update.message.reply_text(analysis, parse_mode='Markdown', disable_web_page_preview=True)


async def analyze_shopee_products(products: list, keyword: str):
    """Dùng Gemini phân tích kết quả"""
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )

        prompt = f"""
Từ khóa tìm kiếm: {keyword}

Danh sách sản phẩm:
{json.dumps(products, ensure_ascii=False, indent=2)}

Hãy phân tích và trả lời theo định dạng đẹp, dễ đọc:
- Top 5 sản phẩm (số thứ tự + tên + giá + rating + lượt bán)
- So sánh ngắn gọn giữa các sản phẩm
- Khuyến nghị sản phẩm tốt nhất và lý do
- Chèn link mua cho từng sản phẩm
"""

        response = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gemini-2.0-flash"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content

    except Exception as e:
        log.error(f"LLM Error: {e}")
        # Fallback response
        fallback = "⚠️ Có lỗi khi phân tích sản phẩm.\n\nDanh sách sản phẩm thô:\n"
        for i, p in enumerate(products, 1):
            fallback += f"{i}. {p.get('name')}\n   💰 {p.get('price')} | ⭐ {p.get('rating')}\n   🔗 {p.get('link')}\n\n"
        return fallback


def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise SystemExit("❌ TELEGRAM_TOKEN not set in environment variables")

    # Start health server
    threading.Thread(target=run_health_server, daemon=True).start()

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", handle_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    log.info("🚀 Shopee Hunter Bot started successfully!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
