#!/usr/bin/env python3
"""Shopee Hunter Bot - Final Simple Version"""

import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Import tool trực tiếp
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shopee_tool import search_shopee

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    text = update.message.text.strip()

    if text.startswith('/start'):
        await update.message.reply_text("👋 Gõ từ khóa sản phẩm bạn muốn tìm...")
        return

    await update.message.reply_text(f"🔍 Đang tìm top sản phẩm cho: **{text}**...", parse_mode='Markdown')

    try:
        products = await search_shopee(text, limit=5)
        if not products:
            await update.message.reply_text("❌ Không tìm thấy sản phẩm.")
            return

        response = f"**Kết quả cho: {text}**\n\n"
        for i, p in enumerate(products, 1):
            response += f"{i}. **{p.get('name', 'N/A')}**\n"
            response += f"💰 {p.get('price', 'N/A')} | ⭐ {p.get('rating', 'N/A')}\n"
            response += f"🔗 {p.get('link', '#')}\n\n"

        await update.message.reply_text(response, parse_mode='Markdown', disable_web_page_preview=True)
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        log.error("TELEGRAM_TOKEN not found")
        return

    app = Application.builder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    log.info("🚀 Shopee Hunter Bot started successfully!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
