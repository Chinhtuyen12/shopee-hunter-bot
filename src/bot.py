#!/usr/bin/env python3
"""Shopee Hunter Bot."""

from __future__ import annotations

import asyncio
import logging
import threading
import search_shopee
from .tools.shopee
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from .config import Config
from .agents import Agent

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("tara-bot")


# ── In-memory sessions ───────────────────────────────────────────────

sessions: dict[int, Agent] = {}


def get_agent(user_id: int) -> Agent:
    """Get or create an agent session for a user."""
    if user_id not in sessions:
        sessions[user_id] = Agent()
    return sessions[user_id]


# ── Authorization ────────────────────────────────────────────────────

def is_allowed(user_id: int) -> bool:
    allowed = Config.allowed_user_id
    if not allowed:
        return True  # no restriction set
    return str(user_id) in allowed.split(",")


def authorize(update: Update) -> bool:
    uid = update.effective_user.id if update.effective_user else 0
    if not is_allowed(uid):
        log.warning(f"Blocked unauthorized access: {uid}")
        return False
    return True


# ── Handlers ─────────────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text.strip()
    user_id = update.effective_user.id

    # Kiểm tra user được phép
    if str(user_id) != str(Config.ALLOWED_USER_ID):
        await update.message.reply_text("❌ Bạn không có quyền sử dụng bot này.")
        return

    # Xử lý lệnh
    if text.startswith('/start'):
        await update.message.reply_text(
            "👋 Chào bạn! Tôi là *Shopee Hunter Bot*\n\n"
            "Gõ từ khóa bạn muốn tìm, ví dụ:\n"
            "`tai nghe bluetooth`\n"
            "`quần jeans nam`\n"
            "`kem dưỡng da`\n\n"
            "Tôi sẽ tìm Top 5 sản phẩm tốt nhất cho bạn!",
            parse_mode='Markdown'
        )

    elif text.lower() in ['/help', 'help']:
        await update.message.reply_text("Gõ từ khóa sản phẩm bạn muốn tìm...")

    else:
        # Xử lý tìm kiếm sản phẩm
        keyword = text.strip()
        await update.message.reply_text(f"🔍 Đang tìm kiếm top sản phẩm cho **{keyword}**...", parse_mode='Markdown')
        
        # Gọi tool Shopee
        products = await search_shopee(keyword, limit=5)
        
        if not products or "Lỗi" in products[0]["name"]:
            await update.message.reply_text("❌ Không tìm thấy sản phẩm nào. Thử từ khóa khác nhé!")
            return

        # Gửi cho LLM phân tích
        analysis = await analyze_shopee_products(products, keyword)
        await update.message.reply_text(analysis, parse_mode='Markdown', disable_web_page_preview=True)

async def reset(update: Update, _context) -> None:
    """Reset conversation history."""
    if not authorize(update):
        return
    uid = update.effective_user.id
    if uid in sessions:
        del sessions[uid]
    await update.message.reply_text("🔄 Đã reset conversation.")


async def uptime(update: Update, _context) -> None:
    """Show a simple health check — useful for monitoring."""
    if not authorize(update):
        return
    await update.message.reply_text(
        f"✅ Tara Bot đang chạy | "
        f"{len(sessions)} active session(s)"
    )


# ── Health check HTTP server (for Fly.io) ─────────────────────────────

class HealthHandler(BaseHTTPRequestHandler):
    """Minimal health endpoint so Fly.io doesn't kill the machine."""

    def do_GET(self) -> None:
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, fmt, *args) -> None:
        pass  # silence log spam


def run_health_server() -> None:
    server = HTTPServer(("0.0.0.0", 8080), HealthHandler)
    log.info("Health server listening on :8080")
    server.serve_forever()


# ── Main ─────────────────────────────────────────────────────────────

def main() -> None:
    token = Config.telegram_token
    if not token:
        raise SystemExit("TELEGRAM_TOKEN not set")

    # Start health server in background thread for Fly.io
    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("uptime", uptime))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    log.info("🚀 Tara Bot started")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

async def analyze_shopee_products(products: list, keyword: str):
    """Dùng LLM phân tích và format kết quả"""
    prompt = f"""
    Từ khóa: {keyword}
    Top 5 sản phẩm tìm được:
    {json.dumps(products, ensure_ascii=False, indent=2)}

    Hãy phân tích và trả lời theo định dạng đẹp:
    - Top 5 sản phẩm (có số thứ tự)
    - So sánh ngắn gọn (giá, rating, lượt bán)
    - Khuyến nghị sản phẩm tốt nhất
    - Chèn link mua (dùng link gốc trước)
    """

    # Gọi LLM (dùng hệ thống có sẵn của bot)
    response = await llm_client.chat.completions.create(
        model=Config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1200
    )
    
    return response.choices[0].message.content

if __name__ == "__main__":
    main()
