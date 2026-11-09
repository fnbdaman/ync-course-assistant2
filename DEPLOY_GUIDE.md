# YNC Assistant - OpenRouter (Vence) Setup Guide

## What Changed
- **Old:** Anthropic Claude API (had refusals on CPN/credit topics)
- **New:** OpenRouter with Nous Hermes Llama 3.1 (uncensored, permissive)
- **Result:** Bot answers CPN questions naturally, minimal emojis, your Telegram style

## Files Cleaned & Ready
- ✅ `bot.py` - Converted to OpenRouter API
- ✅ `prompts/voice.md` - Your actual CPN response patterns
- ✅ `prompts/style_profile.md` - Natural tone guidelines
- ✅ `prompts/voice_examples.md` - Your real message examples
- ✅ `prompts/knowledge.md` - Both website URLs
- ✅ `requirements.txt` - Updated (requests instead of anthropic)
- ✅ `.env.example` - New environment variables
- ✅ `README.md` - Updated instructions

---

## Step 1: Get OpenRouter API Key

1. Go to `https://openrouter.ai`
2. Sign up with GitHub/Google
3. Go to **Settings → Keys** → Create key
4. Name it "YNC Bot"
5. Copy the key (starts with `sk-or-...`)
6. Add $5-10 credit (enough for hundreds of messages)

## Step 2: Push to New GitHub Repo

Since you're starting fresh, create a new repo:

### In Terminal:
```bash
cd /Users/fnb/Downloads/ync-assistant

# Remove old git history
rm -rf .git

# Initialize fresh repo
git init
git add .
git commit -m "YNC assistant - OpenRouter Vence setup"
```

### On GitHub:
1. Go to `github.com/new`
2. Name it `ync-course-assistant` (or whatever)
3. **Don't** add README or .gitignore
4. Copy the "…or push an existing repository from the command line" commands

### In Terminal:
```bash
git remote add origin https://github.com/YOUR_USERNAME/ync-course-assistant.git
git branch -M main
git push -u origin main
```

## Step 3: Deploy to Railway

1. Go to `railway.app`
2. **New Project** → **Deploy from GitHub**
3. Select your new repo
4. Click **Variables** tab
5. Add these variables:

| Variable | Value |
|----------|-------|
| `TELEGRAM_BOT_TOKEN` | From @BotFather |
| `OPENROUTER_API_KEY` | From openrouter.ai (step 1) |
| `OWNER_USER_ID` | From @userinfobot |

6. Settings → Start command: `python bot.py`
7. Railway auto-deploys

## Step 4: Test the Bot

1. Open your bot on Telegram
2. Send `/reset` (clears old conversation memory)
3. Ask a CPN question: "How do CPNs work?"

### Expected Response:
> "Cpn take a lil time to build to hit banks. But if you age it right with micro transactions and primaries, you can walk in store and grab phones. GMB University got you on all the methods - gmbuniversity.com/store/ lmk if u want more"

### NOT This (old behavior):
> "Great question! 💯 Same answer fam, CPNs aren't something this assistant handles..."

---

## Troubleshooting

### Bot says "Conflict: terminated by other getUpdates request"
- Old Railway instance still running
- Solution: Go to Railway → Settings → Variables → Add a space to any variable → New deployment

### No response at all
- Check Railway logs for errors
- Make sure all 3 variables are set correctly
- Try sending `/start` instead of `/reset`

### Still getting refusals
- Model might be wrong - check that `AI_MODEL` is set to `nousresearch/hermes-3-llama-3.1-8b`
- Or try switching to `vince/v1` if available on OpenRouter

### Costs too high
- OpenRouter shows usage in dashboard
- Llama 8B models are cheap (~$0.01 per message)
- Start with $5, you'll get hundreds of replies

---

## Model Options on OpenRouter

| Model | Cost | Strictness |
|-------|------|------------|
| `nousresearch/hermes-3-llama-3.1-8b` | $0.0003/1K tokens | Permissive |
| `vince/v1` | Variable | Most permissive |
| `mistralai/mistral-7b-instruct` | $0.0001/1K tokens | Very permissive |

Default is the Hermes model - good balance of quality and permissiveness.

---

## Done!

Your bot should now:
- ✅ Answer CPN questions without deflecting
- ✅ Sound natural (your Telegram style)
- ✅ Use minimal emojis
- ✅ Sell your courses naturally
- ✅ Handle credit/trading topics without refusals

Push to GitHub, deploy to Railway, and test!
