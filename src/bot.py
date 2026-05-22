#!/usr/bin/env python3
"""Shopee Hunter Bot - Detailed Review Analysis"""

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
        async with httpx.AsyncClient(timeout=25) as client:
            resp = await client.get(
                "https://serpapi.com/search",
                params={
                    "engine": "google_shopping",
                    "q": keyword,
                    "api_key": api_key,
                    "num": 20,
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
                    "rating": item.get("rating", "4.8"),
                    "reviews": item.get("reviews", "N/A"),        # Số lượng đánh giá
                    "link": item.get("link", "#")
                })
        return products
    except Exception as e:
        log.error(f"Search error: {e}")
        return []


async def ai_detailed_review_analysis(products: list, query: str):
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )

        prompt = f"""
Bạn là chuyên gia phân tích đánh giá sản phẩm Shopee.
Từ khóa tìm kiếm: "{query}"

Danh sách sản phẩm:
{json.dumps(products, ensure_ascii=False, indent=2)}

Hãy tạo phản hồi chuyên nghiệp bằng tiếng Việt với cấu trúc sau:

**1. Bảng so sánh chi tiết**
Dùng Markdown table với các cột: 
STT | Tên sản phẩm | Giá | Đánh giá | Số review | Link

**2. Phân tích đánh giá chi tiết**
- Sản phẩm nào có đánh giá tốt nhất?
- Điểm mạnh / điểm yếu chính của từng sản phẩm
- Gợi ý sản phẩm phù hợp nhất theo nhu cầu chung

**3. Khuyến nghị cuối cùng**
- Nên mua sản phẩm nào?
- Mức giá hợp lý hiện tại

Viết ngắn gọn, khách quan, có emoji.
"""

        response = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gemini-2.0-flash"),
            messages=[
                {"role": "system", "content": "Bạn là chuyên gia phân tích review và tư vấn mua sắm Shopee rất chi tiết."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1800,
            temperature=0.7
        )
        return response.choices[0].message.content

    except Exception as e:
        log.error(f"AI Error: {e}")
        # Fallback
        response = f"**📊 Bảng so sánh cho:** {query}\n\n"
        response += "| STT | Tên sản phẩm | Giá | Đánh giá | Số review | Link |\n"
        response += "|-----|--------------|-----|----------|-----------|------|\n"
        for i, p in enumerate(products, 1):
            response += f"| {i} | {p.get('name')[:45]}... | {p.get('price')} | ⭐ {p.get('rating')} | {p.get('reviews')} | [Mua]({p.get('link')}) |\n"
        return response


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
            "Tôi hỗ trợ so sánh chi tiết với:\n"
            "• Bảng so sánh đầy đủ\n"
            "• Đánh giá sao & số review\n"
            "• Phân tích AI sâu\n\n"
            "Thử gõ: `so sánh tai nghe airpods pro`"
        , parse_mode='Markdown')
        return

    await update.message.reply_text("🤖 Đang phân tích đánh giá chi tiết...")

    products = await search_shopee(text, limit=6)

    if not products:
        await update.message.reply_text("❌ Không tìm thấy sản phẩm phù hợp.")
        return

    analysis = await ai_detailed_review_analysis(products, text)
    await update.message.reply_text(analysis, parse_mode='Markdown', disable_web_page_preview=True)


def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        log.error("TELEGRAM_TOKEN not set")
        return

    app = Application.builder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    log.info("🚀 Shopee Hunter Bot - Detailed Review Analysis started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
