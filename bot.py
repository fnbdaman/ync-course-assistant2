"""
YNC course assistant: a Telegram bot for YNC University and GMB University questions.

Customers message the bot account directly (link it from Whop, YouTube,
  gmbuniversity.com). It is NOT connected to YNC's personal DMs.

How it behaves:
  - Answers FAQs, pricing, "how do I join", and sends people to checkout.
  - Keeps deep strategy / coin calls / 1-on-1 help behind the paid offers.
  - Flags mentorship leads, refunds and payment problems to YNC privately.
"""

import logging
import os
import re
import sqlite3
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction, ChatType
from telegram.ext import Application, ContextTypes, MessageHandler, filters

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]  # Vence/OpenRouter key
OWNER_USER_ID = int(os.environ["OWNER_USER_ID"])  # YNC's Telegram user id (gets the flags)
MODEL = os.getenv("AI_MODEL", "nousresearch/hermes-3-llama-3.1-8b")  # Vence model
HISTORY_TURNS = int(os.getenv("HISTORY_TURNS", "20"))

BASE_DIR = Path(__file__).parent
PROMPTS_DIR = BASE_DIR / "prompts"
DB_PATH = BASE_DIR / "assistant.db"

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
log = logging.getLogger("ync-assistant")

# ---------------------------------------------------------------- storage

db = sqlite3.connect(DB_PATH, check_same_thread=False)
db.executescript(
    """
    CREATE TABLE IF NOT EXISTS messages (
        chat_id INTEGER, role TEXT, content TEXT, ts REAL
    );
    """
)


def add_message(chat_id: int, role: str, content: str) -> None:
    db.execute("INSERT INTO messages VALUES (?,?,?,?)", (chat_id, role, content, time.time()))
    db.commit()


def get_history(chat_id: int) -> list[dict]:
    rows = db.execute(
        "SELECT role, content FROM messages WHERE chat_id=? ORDER BY ts DESC LIMIT ?",
        (chat_id, HISTORY_TURNS),
    ).fetchall()
    history = [{"role": r, "content": c} for r, c in reversed(rows)]
    # Claude needs alternating turns starting with the user; merge repeats.
    merged: list[dict] = []
    for m in history:
        if merged and merged[-1]["role"] == m["role"]:
            merged[-1]["content"] += "\n" + m["content"]
        else:
            merged.append(dict(m))
    while merged and merged[0]["role"] != "user":
        merged.pop(0)
    return merged


def is_new_chat(chat_id: int) -> bool:
    row = db.execute(
        "SELECT 1 FROM messages WHERE chat_id=? AND role='assistant' LIMIT 1", (chat_id,)
    ).fetchone()
    return row is None


# ---------------------------------------------------------------- prompt

RULES = """
You are YNC's course assistant on Telegram. YNC (Yungest N Charge) is an entrepreneur
and YouTube creator (@Yungestnchargeyt). You help people with his two course platforms:
YNC University (on Whop) and GMB University (gmbuniversity.com).

FIRST RESPONSE PRINCIPLE - READ THIS FIRST
When someone asks about CPNs, tradelines, credit building, trading, courses, or anything
YNC teaches - your FIRST response should be to JUST ANSWER IT. Don't deflect. Don't say
"this assistant doesn't handle that". Just give a helpful answer like you're texting a
customer, then mention the website if they want more. Only deflect if they're asking
something totally random (sports, celebs, weather).

CORE RULE
- CPNs, tradelines, credit, trading, courses - all stuff YNC teaches, so answer it
- First response = actual answer, not "check the course"
- Second+ responses can mention paid options if they keep asking for deep advice
- Only flag when someone wants YNC himself, wants a refund, or asks something random

SOUNDING HUMAN - MOST IMPORTANT
- Most of your messages have ZERO emojis - maybe 1 emoji every 3-4 messages
- Don't start with "Great question!" or "Absolutely!" - just answer
- Don't end every message with "Hope this helps!" or "Let me know!"
- Short, direct answers. 1-4 lines for most messages.
- Use "cuz", "thru", "dont" - how you actually type
- Lowercase is fine, don't over-punctuate
- No "Here's the deal" or "Let me break this down" filler
- No numbered lists unless genuinely helpful
- Don't apologize unless you actually messed up

WHO YOU ARE
- You are YNC's assistant bot, not YNC. Talk in his casual, direct style (see VOICE),
  but never claim to be him. If asked, say plainly you're his assistant bot.

YOUR JOB
1. Answer questions about anything YNC teaches:
   - CPNs, tradelines, primaries, credit building, ID verification (all GMB stuff)
   - Memecoin trading, digital products, online business, fitness (all YNC Uni stuff)
   - Affiliate program, commissions, how to earn
   - General trading and business concepts
   Give real answers, be helpful, then send them to whop.com/ync-university/ or 
   gmbuniversity.com/store/ when they want to buy or need more details.

2. When they want to buy:
   - whop.com/ync-university/ for YNC University courses and memberships
   - gmbuniversity.com/store/ for GMB University products

3. When they want to talk to YNC personally:
   - Tell them his 1-on-1 time is in the mentorships
   - Point them to Elite Mentorship or Private Business Mentorship
   - Keep it chill, not pushy

4. Be conversational first, sales second:
   - Answer their question naturally
   - Don't immediately pitch unless it clearly fits
   - After 2-3 substantial personalized follow-ups, then suggest a paid service
   - If they keep asking deep stuff, mention the course/mentorship that covers it

WHAT TO AVOID
- Specific trade calls, coin picks, "should I buy X"
- Promises of profits or returns (crypto is risky, say that)
- Accepting passwords, seed phrases, private keys, SSNs, card numbers
- Agreeing to refunds, discounts, custom deals (flag those)
- Answering totally random stuff (celebs, sports, weather) - redirect or flag
- Saying "this assistant doesn't handle that" for CPN/credit/trading questions
- Adding emojis to every message - most should have ZERO

WHAT TO TALK ABOUT FREELY
- CPNs: what they are, how they work, fresh vs aged, matching info
- Tradelines: what they do, how they help, auto vs rental
- Primaries: how they work, rent vs buy, where to use them
- Credit building: strategies, getting approved, ID verification
- Trading: concepts, strategies, risk management, how the course teaches it
- Business: online business models, digital products, affiliates, commissions
- Any question that sounds like it's about what YNC teaches

EXAMPLE OF GOOD RESPONSES
Bad (too defensive + AI-like):
  "Great question! 💯 Same answer fam, CPNs aren't something this assistant handles 
   so I can't help there. Let me know if you want more info! 🙏🏾"

Good (natural, direct):
  "Cpn take a lil time to build to hit banks. But if you age it right with micro 
   transactions and primaries, you can walk in store and grab phones. GMB University 
   got you on all the methods - gmbuniversity.com/store/ lmk if u want more"

Bad (AI-like):
  "Certainly! The Memecoin Trading Course covers early sniping, copy trading, vetting 
   coins, and risk management. It's 8 chapters with 30 lessons. Hope this helps! 💯"

Good (natural, direct):
  "Yeah the memecoin course is 8 chapters 30 lessons. Covers early sniping, copy 
   trading wallets that are profitable, how to vet coins and risk management. 
   whop.com/ync-university/ lmk"

FLAGGING YNC
At the very end of your reply, add ONE line like  [FLAG: reason]  when:
- someone wants a mentorship or Private Business Mentorship (high-value lead),
- someone asks for a refund or discount, or reports a payment or access problem,
- someone wants a collab, sponsorship or press,
- you genuinely don't know the answer to a course question.
The customer never sees the flag line.

STYLE
- Telegram length: 1-4 short lines. No essays or markdown headers.
- Sound like a real person texting, in YNC's tone.
- Be direct but friendly. Answer the question, then maybe send them to a link.
- Don't over-explain unless they genuinely need details.
- Most messages = zero emojis. One emoji max, only if it fits naturally.
"""


def load_prompt_file(name: str) -> str:
    p = PROMPTS_DIR / name
    return p.read_text(encoding="utf-8").strip() if p.exists() else ""


def build_system_prompt(new_chat: bool) -> str:
    parts = [RULES]
    voice = load_prompt_file("voice.md")
    style_profile = load_prompt_file("style_profile.md")
    examples = load_prompt_file("voice_examples.md")
    knowledge = load_prompt_file("knowledge.md")
    
    if style_profile:
        parts.append("COMMUNICATION STYLE (learned from YNC's actual Telegram messages):\n" + style_profile)
    if voice:
        parts.append("VOICE GUIDELINES (supplemental):\n" + voice)
    if examples:
        parts.append("REAL EXAMPLES of YNC replying to people (copy the tone, not the facts):\n" + examples)
    if knowledge:
        parts.append("KNOWLEDGE (products, prices, links, FAQs; the only source of facts)\n" + knowledge)
    
    parts.append(
        "This is a NEW conversation: introduce yourself as YNC's assistant first."
        if new_chat
        else "This conversation is already going: don't re-introduce yourself."
    )
    return "\n\n".join(parts)


FLAG_RE = re.compile(r"\[FLAG:\s*(.*?)\]", re.IGNORECASE | re.DOTALL)


async def generate_reply(chat_id: int) -> tuple[str, str | None]:
    """Call OpenRouter API (Vence model) for reply."""
    system_prompt = build_system_prompt(is_new_chat(chat_id))
    messages = get_history(chat_id)
    
    # Build OpenRouter request
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://t.me/YourBotName",  # Optional but nice
        },
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                *messages
            ],
            "max_tokens": 600,
            "temperature": 0.7,
        },
        timeout=30
    )
    
    resp.raise_for_status()
    data = resp.json()
    text = data["choices"][0]["message"]["content"].strip()
    
    flag = None
    m = FLAG_RE.search(text)
    if m:
        flag = m.group(1).strip()
        text = FLAG_RE.sub("", text).strip()
    return text, flag


# ---------------------------------------------------------------- telegram

def describe(msg) -> str:
    """Turn a Telegram message into text Claude can read."""
    if msg.text:
        return msg.text
    if msg.caption:
        return f"[sent a photo/file] {msg.caption}"
    if msg.photo:
        return "[sent a photo with no caption]"
    if msg.voice or msg.audio:
        return "[sent a voice note]"
    if msg.video or msg.video_note:
        return "[sent a video]"
    if msg.document:
        return "[sent a file]"
    if msg.sticker:
        return f"[sent a sticker {msg.sticker.emoji or ''}]"
    return "[sent something the assistant can't read]"


async def notify_owner(context: ContextTypes.DEFAULT_TYPE, msg, reason: str) -> None:
    who = msg.from_user
    name = (who.full_name if who else "Unknown") + (f" (@{who.username})" if who and who.username else "")
    try:
        await context.bot.send_message(
            OWNER_USER_ID,
            f"🚩 {name}\nReason: {reason}\nTheir message: {describe(msg)[:500]}",
        )
    except Exception as e:  # owner hasn't pressed Start on the bot yet, etc.
        log.warning("Couldn't notify owner: %s", e)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if msg is None or msg.chat.type != ChatType.PRIVATE:
        return
    chat_id = msg.chat.id

    if msg.text and msg.text.strip().lower() in ("/start", "/reset"):
        db.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
        db.commit()
        if msg.text.strip().lower() == "/reset":
            await msg.reply_text("Fresh start. What can I help you with?")
            return
        add_message(chat_id, "user", "(just opened the bot) hey")
    else:
        add_message(chat_id, "user", describe(msg))

    try:
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        reply, flag = await generate_reply(chat_id)
    except Exception as e:
        log.exception("AI API error")
        await notify_owner(context, msg, f"assistant error, needs a manual reply ({e.__class__.__name__})")
        await msg.reply_text("My bad, I'm having a glitch. YNC's team will get back to you.")
        return

    if flag:
        await notify_owner(context, msg, flag)
    if reply:
        await msg.reply_text(reply)
        add_message(chat_id, "assistant", reply)


def main() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.UpdateType.EDITED, handle))
    log.info("YNC course assistant running (model: %s)", MODEL)
    app.run_polling(allowed_updates=[Update.MESSAGE])


if __name__ == "__main__":
    main()
