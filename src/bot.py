#!/usr/bin/env python3
"""Shopee Hunter Bot - AI Comparison + Bảng So Sánh"""

import os
import logging
import httpx
import json
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

async def search_shopee(keyword: str, limit: int = 6):
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return []

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                "https://serpapi.com/search",
                params={
                    "engine": "google_shopping",
                    "q": keyword,
                    "api_key": api_key,
                    "num": 15,
                    "gl": "vn",
                    "hl": "vi"
                }
            )
            data = resp.json()

        products = []
        for item in data.get("shopping_results", [])[:limit]:
            if "shopee.vn" in item.get("link", "").lower():
                products.append({
                    "name": item.get("title", "N/A"),
                    "price": item.get("price", "N/A"),
                    "link": item.get("link", "#")
                })
        return products
    except:
        return []


async def ai_analyze_and_compare(products: list, query: str):
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )

        prompt = f"""
Bạn là chuyên gia tư vấn mua sắm Shopee.
Từ khóa: "{query}"

Danh sách sản phẩm:
{json.dumps(products, ensure_ascii=False, indent=2)}

Hãy phân tích và trả lời bằng **tiếng Việt**, theo cấu trúc sau:

1. **Bảng so sánh** (dùng Markdown table)
2. **Sản phẩm tốt nhất** + lý do
3. **Gợi ý giá tốt** (nên mua ở mức giá nào)
4. **Khuyến nghị cuối cùng** cho người dùng

Viết ngắn gọn, dễ hiểu, có emoji.
"""

        response = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gemini-2.0-flash"),
            messages=[
                {"role": "system", "content": "Bạn là chuyên gia so sánh sản phẩm Shopee khách quan và thông minh."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        return response.choices[0].message.content

    except Exception as e:
        log.error(f"AI Error: {e}")
        # Fallback table
        response = "**Bảng so sánh nhanh:**\n\n"
        response += "| STT | Tên sản phẩm | Giá | Link |\n"
        response += "|-----|--------------|-----|------|\n"
        for i, p in enumerate(products, 1):
            response += f"| {i} | {p.get('name')[:50]}... | {p.get('price')} | [Mua]({p.get('link')}) |\n"
        return response + "\n❌ Không thể phân tích chi tiết do lỗi AI."


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
            "Tôi có thể giúp bạn:\n"
            "• Tìm sản phẩm\n"
            "• So sánh nhiều sản phẩm\n"
            "• Gợi ý giá tốt nhất\n\n"
            "Ví dụ:\n"
            "`tai nghe bluetooth`\n"
            "`so sánh airpods và galaxy buds`"
        , parse_mode='Markdown')
        return

    await update.message.reply_text("🤖 Đang phân tích và so sánh...")

    products = await search_shopee(text, limit=6)

    if not products:
        await update.message.reply_text("❌ Không tìm thấy sản phẩm phù hợp.")
        return

    analysis = await ai_analyze_and_compare(products, text)
    await update.message.reply_text(analysis, parse_mode='Markdown', disable_web_page_preview=True)


def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        log.error("TELEGRAM_TOKEN not set")
        return

    app = Application.builder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    log.info("🚀 Shopee Hunter Bot - AI Comparison started!")
    app.run_pol
