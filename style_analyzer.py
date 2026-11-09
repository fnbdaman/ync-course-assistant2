#!/usr/bin/env python3
"""Telegram Style Analyzer - Extracts speaking patterns from Telegram exports."""

import json
import re
from collections import Counter
from pathlib import Path


def load_telegram_export(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_yunc_messages(data: dict) -> list[dict]:
    """Extract messages from Yungest N Charge (user7080090889)"""
    yunc_messages = []
    yunc_id = "user7080090889"
    
    for chat in data.get("chats", {}).get("list", []):
        if chat.get("type") in ["bot_chat", "private_group", "public_group"]:
            continue
            
        for msg in chat.get("messages", []):
            if msg.get("from_id") != yunc_id or msg.get("type") != "message":
                continue
                
            text = msg.get("text", "")
            if isinstance(text, list):
                text = " ".join(item.get("text", "") if isinstance(item, dict) else str(item) for item in text)
            
            text = text.strip()
            if not text or text.startswith("/"):
                continue
                
            yunc_messages.append({
                "chat_name": chat.get("name", "Unknown"),
                "text": text,
                "date": msg.get("date", ""),
            })
    
    return yunc_messages


def extract_common_phrases(messages: list[dict]) -> Counter:
    text = " ".join(m["text"] for m in messages).lower()
    patterns = [
        r"\bro\b", r"\bbro\b", r"\byo\b", r"\bfam\b", r"\bgang\b",
        r"\bbet\b", r"\bfacts\b", r"\blmk\b", r"\bgot you\b",
        r"\byessir\b", r"\bone\s*sec\b", r"\bgimme\s*sec\b", r"\bwym\b",
        r"\bcuz\b", r"\bdont\b", r"\bthru\b", r"\bperfect\b",
    ]
    found = Counter()
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if len(matches) >= 2:
            found[pattern] = len(matches)
    return found


def analyze_response_lengths(messages: list[dict]) -> dict:
    lengths = [len(m["text"].split()) for m in messages]
    return {
        "avg": sum(lengths) / len(lengths) if lengths else 0,
        "min": min(lengths) if lengths else 0,
        "max": max(lengths) if lengths else 0,
        "short_msgs": sum(1 for l in lengths if l <= 5),
        "long_msgs": sum(1 for l in lengths if l > 15),
    }


def generate_style_profile(messages: list[dict]) -> str:
    phrases = extract_common_phrases(messages)
    stats = analyze_response_lengths(messages)
    
    # Get examples
    short_msgs = [m["text"] for m in messages if len(m["text"].split()) <= 5][:5]
    long_msgs = [m["text"] for m in messages if len(m["text"].split()) > 15][:3]
    greetings = [m["text"] for m in messages if m["text"].lower().startswith(("yo", "hey", "sup"))][:5]
    lmk_msgs = [m["text"] for m in messages if m["text"].lower().startswith("lmk")][:3]
    
    profile = f"""# YNC Communication Style Profile

Generated from {len(messages)} messages in Telegram exports

## CORE STYLE RULES

### Response Length Patterns
- Average response: {stats['avg']:.1f} words
- Short messages (1-5 words): {stats['short_msgs']} examples
- Longer explanations (15+ words): {stats['long_msgs']} examples

### Short Direct Responses (1-5 words)
- "Yes brother"
- "Got it"
- "Yessir"
- "One sec bro"
- "Gang"

### Real Examples of Your Short Responses:
"""
    for msg in short_msgs:
        profile += f'- "{msg}"\n'
    
    profile += "\n### Longer Explanations (When Needed)\n"
    for msg in long_msgs:
        profile += f'- "{msg}"\n'
    
    profile += f"""\n## GREETING STYLE
"""
    for msg in greetings:
        profile += f'- "{msg}"\n'
    
    profile += f"""\n## COMMON PHRASES YOU USE
"""
    for phrase, count in phrases.most_common(10):
        profile += f'- {phrase}: {count}x\n'
    
    profile += f"""\n## FOLLOW-UP / CALL-TO-ACTION STYLE
- Use "lmk" to invite further questions
- Example LMK responses:
"""
    for msg in lmk_msgs:
        profile += f'- "{msg}"\n'
    
    profile += """\n## HANDLING OBJECTIONS / COMPLAINTS
1. Acknowledge first ("yes brother", "got you")
2. Explain situation directly, no defensiveness
3. Offer solution or next step
4. Keep it chill and straightforward

## PRACTICAL RULES FOR THE BOT

1. **Keep it short**: 1-4 lines for most messages
2. **Be direct**: Answer what they ask without over-explaining
3. **Lowercase is fine**: Don't over-punctuate
4. **Use natural contractions**: "cuz", "dont" - how you actually write
5. **Stay friendly but casual**: "bro", "fam", "gang" when it fits
6. **When selling**: Explain value clearly, send link, say "lmk"
7. **Handling complaints**: "yes brother" + explain + offer solution
8. **No hype**: Straightforward about what they get
9. **Call-to-action**: "lmk" or "hit me up" - not pushy
10. **Be you**: Match your actual text style

## THINGS TO AVOID
- Long paragraphs
- Overly formal language
- Multiple emojis per message
- Numbered lists unless genuinely helpful
- Being pushy about sales
- Repeating the same phrase too much

"""
    return profile


def generate_voice_examples(messages: list[dict]) -> str:
    short_msgs = [m["text"] for m in messages if len(m["text"].split()) <= 5][:5]
    greetings = [m["text"] for m in messages if m["text"].lower().startswith(("yo", "hey"))][:5]
    lmk_msgs = [m["text"] for m in messages if "lmk" in m["text"].lower()][:5]
    explanation_msgs = [m["text"] for m in messages if len(m["text"].split()) > 15][:5]
    
    examples = """# Real YNC Response Examples
# Use these for tone/style - not to copy facts verbatim

## Greetings
"""
    for msg in greetings:
        examples += f'- "{msg}"\n'
    
    examples += "\n## Quick Responses\n"
    for msg in short_msgs:
        examples += f'- "{msg}"\n'
    
    examples += "\n## Follow-up / Call-to-Action\n"
    for msg in lmk_msgs:
        examples += f'- "{msg}"\n'
    
    examples += "\n## Explanations (When They Need Details)\n"
    for msg in explanation_msgs:
        examples += f'- "{msg}"\n'
    
    return examples


def main():
    export_path = Path("/Users/fnb/Downloads/Telegram Desktop/DataExport_2026-11-09 (1)/result.json")
    
    if not export_path.exists():
        print(f"Export not found at {export_path}")
        return
    
    print("Loading Telegram export...")
    data = load_telegram_export(export_path)
    
    print("Extracting YNC messages...")
    messages = extract_yunc_messages(data)
    print(f"Found {len(messages)} messages from YNC")
    
    if not messages:
        print("No messages found")
        return
    
    print("\nAnalyzing patterns...")
    
    prompts_dir = Path("/Users/fnb/Downloads/ync-assistant/prompts")
    prompts_dir.mkdir(exist_ok=True)
    
    # Write files
    profile = generate_style_profile(messages)
    (prompts_dir / "style_profile.md").write_text(profile, encoding="utf-8")
    print(f"\u2713 Created {prompts_dir}/style_profile.md")
    
    examples = generate_voice_examples(messages)
    (prompts_dir / "voice_examples.md").write_text(examples, encoding="utf-8")
    print(f"\u2713 Created {prompts_dir}/voice_examples.md")
    
    # Summary
    stats = analyze_response_lengths(messages)
    phrases = extract_common_phrases(messages)
    
    print("\n=== ANALYSIS SUMMARY ===")
    print(f"Messages analyzed: {len(messages)}")
    print(f"Avg response length: {stats['avg']:.1f} words")
    print(f"\nTop phrases you use:")
    for phrase, count in phrases.most_common(5):
        print(f"  - {phrase}: {count}x")


if __name__ == "__main__":
    main()
