import json

with open(r"c:\Users\ARNAV ADITYA\Desktop\civix 2.0\visual_prompts_180.json", 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total entries: {len(data)}")

keywords = ['mugshot', 'portrait', 'face', 'person', 'suspect', 'accused', 'photo', 'avatar', 'man', 'woman', 'driver', 'headshot']

matches = []
for item in data:
    prompt = item.get('prompt', '').lower()
    title = item.get('title', '').lower()
    if any(kw in prompt or kw in title for kw in keywords):
        matches.append(item)

print(f"Matches for person/face/photo keywords: {len(matches)}")
for m in matches:
    print(f"[{m['evidence_id']}] Title: {m['title']}\n  Prompt: {m['prompt']}\n")
