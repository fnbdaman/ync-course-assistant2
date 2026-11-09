# YNC course assistant (Telegram bot)

Answers questions about YNC University and GMB University, sends people to the right
course or membership, and privately pings you about mentorship leads, refunds and
payment problems. It's its own bot account and is not connected to your personal DMs.

Powered by OpenRouter (Vence AI) - more permissive for credit/trading topics.

## 1. Make the bot (2 min)
1. In Telegram, message **@BotFather** → `/newbot` → name it something like "YNC University Help".
2. Copy the token it gives you.
3. Message **@userinfobot** to get your own user id (a number).
4. Open your new bot and press **Start** so it can send you flags.

## 2. Fill in your info
- `prompts/knowledge.md`: links, prices, what's included, refund policy.
  **Fill in every TODO.** The bot won't make up links or prices.
- `prompts/voice.md`: how you talk on your channel.
Edits take effect on the next message. No restart needed.

## 3. Get OpenRouter (Vence AI) API key
1. Go to `openrouter.ai`
2. Sign up / log in
3. Add credit (start with $5-10)
4. Go to "Keys" → Create key
5. Copy the key

## 4. Run it
On your computer, to test:
```
cp .env.example .env      # fill in token, API key, your user id
pip install -r requirements.txt
python bot.py
```
Then message your bot. Send `/reset` anytime to start a chat over.

To keep it on 24/7, use **Railway** (railway.app):
1. Put this folder in a GitHub repo (don't upload `.env`).
2. Railway → New Project → Deploy from GitHub → pick the repo.
3. Variables tab → add TELEGRAM_BOT_TOKEN, OPENROUTER_API_KEY, OWNER_USER_ID.
4. Settings → Start command: `python bot.py`.

## 5. Point people to it
Put the bot link (t.me/YourBotName) in your Whop page, YouTube descriptions,
gmbuniversity.com, and your Telegram bio ("questions about the courses → DM my assistant").

## Cost
You pay OpenRouter per message. Short replies on Llama models run about $0.005-$0.02 each.
Model used: nousresearch/hermes-3-llama-3.1-8b (uncensored, permissive for financial topics)
# ync-course-assistant2
