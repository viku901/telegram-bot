import os
import time
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =====================
# ENV VARIABLES (Render)
# =====================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEY = os.getenv("API_KEY")

BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

# =====================
# CACHE (anti API spam)
# =====================
CACHE = {
    "data": None,
    "time": 0
}

CACHE_TTL = 120  # 2 minute


# =====================
# GET LIVE MATCHES (SAFE)
# =====================
def get_live_matches():
    now = time.time()

    if CACHE["data"] and now - CACHE["time"] < CACHE_TTL:
        return CACHE["data"]

    try:
        url = f"{BASE_URL}/fixtures?live=all"
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json().get("response", [])

        CACHE["data"] = data
        CACHE["time"] = now

        return data

    except Exception:
        return []


# =====================
# AI SIMPLE ANALYSIS
# =====================
def analyze(home, away):
    total = home + away

    if total == 0:
        verdict = "🧱 Defensive start"
        lines = ["O0.5", "O1.5"]
    elif total == 1:
        verdict = "⚖️ Slow match"
        lines = ["O1.5", "O2.5"]
    elif total == 2:
        verdict = "📊 Balanced game"
        lines = ["O2.5", "O3.5"]
    elif total == 3:
        verdict = "⚡ Open match"
        lines = ["O3.5", "O4.5"]
    else:
        verdict = "🔥 Very open match"
        lines = ["O4.5", "O5.5"]

    gg = "🔥 GG YES" if home > 0 and away > 0 else "❌ GG NO"

    return verdict, lines, gg


# =====================
# FORMAT MESSAGE
# =====================
def format_match(m):
    home = m["teams"]["home"]["name"]
    away = m["teams"]["away"]["name"]

    hg = m["goals"]["home"]
    ag = m["goals"]["away"]

    minute = m["fixture"]["status"]["elapsed"] or 0

    verdict, lines, gg = analyze(hg, ag)

    return f"""
⚽ {home} vs {away}
⏱ {minute}'

🔴 SCORE: {hg} - {ag}

📊 AI BET:
{verdict}

🎯 Lines:
{", ".join(lines)}

⚡ GG:
{gg}
"""


# =====================
# COMMANDS
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 AI BET BOT LIVE\n\nComenzi:\n/live - meciuri live"
    )


async def live(update: Update, context: ContextTypes.DEFAULT_TYPE):
    matches = get_live_matches()

    if not matches:
        await update.message.reply_text("⚠️ Nu sunt meciuri live acum")
        return

    for m in matches[:6]:
        await update.message.reply_text(format_match(m))


# =====================
# MAIN (RENDER READY)
# =====================
def main():
    if not TELEGRAM_TOKEN or not API_KEY:
        print("Missing ENV variables!")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("live", live))

    print("Bot running on Render...")
    app.run_polling()


if __name__ == "__main__":
    main()
