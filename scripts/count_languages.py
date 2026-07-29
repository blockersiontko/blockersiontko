import requests
import os

TOKEN = os.environ.get("COUNT_LANGUAGES")
headers = {"Authorization": f"Bearer {TOKEN}"}

repos = []
page = 1
while True:
    r = requests.get(
        "https://api.github.com/user/repos",
        params={"per_page": 100, "page": page, "affiliation": "owner"},
        headers=headers,
    )
    data = r.json()
    if not data:
        break
    repos.extend(data)
    page += 1

lang_counts = {}
for repo in repos:
    if repo.get("fork"):
        continue
    lang = repo.get("language")
    if lang:
        lang_counts[lang] = lang_counts.get(lang, 0) + 1

sorted_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)

if sorted_langs:
    max_count = sorted_langs[0][1]
    max_name_len = max(len(lang) for lang, _ in sorted_langs)
    BAR_WIDTH = 20

    lines = ["```text"]
    for lang, count in sorted_langs:
        bar_len = round((count / max_count) * BAR_WIDTH)
        bar = "█" * bar_len + "░" * (BAR_WIDTH - bar_len)
        lines.append(f"{lang.ljust(max_name_len)} {bar} {count}")
    lines.append("```")
    table = "\n".join(lines)
else:
    table = "_Brak danych o językach._"

with open("README.md", "r", encoding="utf-8") as f:
    content = f.read()

start = "<!--START_LANGS-->"
end = "<!--END_LANGS-->"
new_content = content.split(start)[0] + start + "\n" + table + "\n" + end + content.split(end)[1]

with open("README.md", "w", encoding="utf-8") as f:
    f.write(new_content)
