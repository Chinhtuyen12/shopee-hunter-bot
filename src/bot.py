#!/usr/bin/env python3
"""Shopee Hunter Bot - Ultra Simple"""

import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Import trực tiếp
import sys
sys.path.insert(0, "/app")
from src.tools.shopee import search_shopee

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.startswith('/start'):
        await update.message.reply_text("👋 Gõ từ khóa sản phẩm bạn muốn tìm...")
        return

    await update.message.reply_text(f"🔍 Đang tìm: {text}...")

    try:
        products = await search_shopee(text, limit=3)
        if not products:
            await update.message.reply_text("❌ Không tìm thấy sản phẩm.")
            return

        msg = f"**Kết quả cho: {text}**\n\n"
        for i, p in enumerate(products, 1):
            msg += f"{i}. **{p.get('name')}**\n💰 {p.get('price')} | ⭐ {p.get('rating')}\n🔗 {p.get('link')}\n\n"
        await update.message.reply_text(msg, parse_mode='Markdown', disable_web_page_preview=True)
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        log.error("No TELEGRAM_TOKEN")
        return

    app = Application.builder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    log.info("🚀 Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
