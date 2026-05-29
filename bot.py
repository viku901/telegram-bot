import os
import time
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =====================
# ENV (Render / GitHub)
# =====================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEY = os.getenv("API_KEY")

BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

# =====================
# CACHE (anti spam API)
# =====================
CACHE = {
    "data": None,
    "time": 0
}

CACHE_TTL = 120  # 2 minute


# =====================
# LIVE MATCHES (SAFE API CALL)
# =====================
def get_live_matches():
    now = time.time()

    # dacă cache este valid → NU chema API
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
# AI ANALYSIS ENGINE
# =====================
def analyze_match(home, away):
    total = home + away

    if total == 0:
        verdict = "🧱 Defensive start"
        lines = ["O0.5", "O1.5"]
    elif total == 1:
        verdict = "⚖️ Slow tempo"
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

    verdict, lines, gg = analyze_match(hg, ag)

    return f"""
⚽ {home} vs {away}
⏱ {minute}'

🔴 SCORE: {hg} - {ag}

📊 AI BET PRO MAX:
{verdict}

🎯 Over Lines:
{", ".join(lines)}

⚡ GG:
{gg}
"""


# =====================
# STATUS DASHBOARD
# =====================
def check_api_status():
    try:
        r = requests.get(
            "https://v3.football.api-sports.io/status",
            headers=HEADERS,
            timeout=10
        )

        data = r.json()

        if "error" in data:
            return "❌ API ERROR"

        return "🟢 API OK"

    except Exception:
        return "🔴 CONNECTION ERROR"


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    matches = get_live_matches()

    api_status = check_api_status()

    await update.message.reply_text(f"""
📊 STATUS DASHBOARD

{api_status}

⚽ Live matches: {len(matches)}

📡 Cache TTL: {CACHE_TTL}s

⏱ Time: {time.strftime("%H:%M:%S")}
""")


# =====================
# COMMANDS
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 AI BET PRO MAX FULL\n\nComenzi:\n/live - meciuri live\n/status - dashboard API"
    )


async def live(update: Update, context: ContextTypes.DEFAULT_TYPE):
    matches = get_live_matches()

    if not matches:
        await update.message.reply_text("⚠️ Nu sunt meciuri live acum")
        return

    for m in matches[:6]:
        await update.message.reply_text(format_match(m))


# =====================
# MAIN
# =====================
def main():
    if not TELEGRAM_TOKEN or not API_KEY:
        print("Missing ENV variables")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("live", live))
    app.add_handler(CommandHandler("status", status))

    print("BOT PRO MAX RUNNING...")
    app.run_polling()


if __name__ == "__main__":
    main()
