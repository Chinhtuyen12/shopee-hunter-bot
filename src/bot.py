#!/usr/bin/env python3
"""Shopee Hunter Bot - Simplified Version"""

import asyncio
import json
import logging
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Fix import path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.shopee import search_shopee

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

SYSTEM_PROMPT = "Bạn là Shopee Hunter Bot. Tìm sản phẩm tốt nhất trên Shopee."

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

def run_health_server():
    server = HTTPServer(("0.0.0.0", 8080), HealthHandler)
    log.info("Health server running on port 8080")
    server.serve_forever()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = str(update.effective_user.id)
    
    if user_id != os.getenv("ALLOWED_USER_ID"):
        await update.message.reply_text("❌ Bạn không có quyền dùng bot.")
        return

    if text.startswith('/start'):
        await update.message.reply_text("👋 Gõ từ khóa sản phẩm bạn muốn tìm...")
        return

    await update.message.reply_text(f"🔍 Đang tìm: {text}...")

    products = await search_shopee(text, limit=5)
    
    if not products:
        await update.message.reply_text("❌ Không tìm thấy sản phẩm.")
        return

    # Simple response
    response = f"🔎 Kết quả cho **{text}**:\n\n"
    for i, p in enumerate(products, 1):
        response += f"{i}. **{p.get('name')}**\n"
        response += f"💰 {p.get('price')} | ⭐ {p.get('rating')}\n"
        response += f"🔗 {p.get('link')}\n\n"

    await update.message.reply_text(response, parse_mode='Markdown', disable_web_page_preview=True)


def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        log.error("TELEGRAM_TOKEN not set")
        return

    threading.Thread(target=run_health_server, daemon=True).start()

    app = Application.builder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    log.info("🚀 Shopee Hunter Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
