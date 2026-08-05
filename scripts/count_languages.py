import requests
import os

TOKEN = os.environ.get("COUNT_LANGUAGES")
headers = {"Authorization": f"Bearer {TOKEN}"}
CUSTOM_LANGUAGES = {
    ".🍇": "Emojicode",
    ".emojic": "Emojicode",
}

def get_github_languages(owner, repo):
    r = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/languages",
        headers=headers,
    )

    if r.status_code != 200:
        return {}

    return r.json()


def get_custom_languages(owner, repo, branch):
    r = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}",
        params={"recursive": 1},
        headers=headers,
    )

    data = r.json()
    result = {}

    if "tree" not in data:
        return result

    for item in data["tree"]:
        path = item["path"]

        for ext, language in CUSTOM_LANGUAGES.items():
            if path.endswith(ext):
                result[language] = result.get(language, 0) + 1

    return result

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

    owner = repo["owner"]["login"]
    name = repo["name"]
    branch = repo["default_branch"]

    languages = get_github_languages(owner, name)
    custom = get_custom_languages(owner, name, branch)
    
    for lang in custom:
        if lang not in languages:
            languages[lang] = 1

    for lang in languages:
        lang_counts[lang] = lang_counts.get(lang, 0) + 1

sorted_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)

if sorted_langs:
    max_count = sorted_langs[0][1]
    max_name_len = max(len(lang) for lang, _ in sorted_langs)
    BAR_WIDTH = 25

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
