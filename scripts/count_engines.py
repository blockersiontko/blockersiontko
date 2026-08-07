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

# kolejność ma znaczenie przy dopasowaniu (pierwsze trafienie wygrywa)
# słowa kluczowe sprawdzane w opisie
ENGINE_DESC_KEYWORDS = {
    "Godot": ["godot", "gdscript", "gd-script"],
    "Unreal": ["unreal"],
    "Unity": ["unity"],
    "Bevy": ["bevy"],
    "PICO-8": ["pico-8", "pico8"],
    "GameMaker": ["gamemaker", "game-maker", "game maker"],
    "RPG Maker": ["rpgmaker", "rpg-maker", "rpg maker"],
    "Defold": ["defold"],
    "Stride": ["stride"],
    "O3DE": ["o3de"],
    "Panda3D": ["panda3d", "panda-3d", "panda 3d"],
    "MonoGame": ["monogame"],
    "LÖVE": ["love2d", "löve", "love-engine", "love engine"],
    "Ren'Py": ["renpy", "ren'py", "ren py"],
    "TIC-80": ["tic-80", "tic80"],
    "SFML": ["sfml"],
    "Phaser": ["phaser", "phaser-engine", "phaserengine"],
}

# nazwy topics (tagów) na GitHubie sprawdzane osobno, bo mają swoją konwencję
ENGINE_TOPIC_KEYWORDS = {
    "Godot": ["godot", "godot-engine", "gdscript"],
    "Unreal": ["unreal", "unreal-engine", "unrealengine", "ue4", "ue5"],
    "Unity": ["unity", "unity3d", "unity-engine"],
    "Bevy": ["bevy", "bevy-engine", "bevyengine"],
    "PICO-8": ["pico-8", "pico8"],
    "GameMaker": ["gamemaker", "gamemaker-studio", "gml", "game-maker"],
    "RPG Maker": ["rpg-maker", "rpgmaker", "rpg-maker-mv", "rpg-maker-mz", "rpg-maker-vx-ace"],
    "Defold": ["defold", "defold-engine"],
    "Stride": ["stride", "stride3d", "stride-engine"],
    "O3DE": ["o3de", "open-3d-engine"],
    "Panda3D": ["panda3d", "panda-3d"],
    "MonoGame": ["monogame", "monogame-framework"],
    "LÖVE": ["love2d", "love-engine", "lua-love"],
    "Ren'Py": ["renpy", "ren-py"],
    "TIC-80": ["tic-80", "tic80"],
    "SFML": ["sfml", "sfml-graphics"],
    "Phaser": ["phaser", "phaser-3", "phaser3", "phaserjs", "phaser-engine"],
}

engine_counts = {}
for repo in repos:
    if repo.get("fork"):
        continue

    description = (repo.get("description") or "").lower()
    language = repo.get("language") or ""
    topics = [t.lower() for t in repo.get("topics", [])]

    matched_engine = None

    # 1. najpierw sprawdzamy opis
    for engine, keywords in ENGINE_DESC_KEYWORDS.items():
        if any(kw in description for kw in keywords):
            matched_engine = engine
            break

    # 2. jeśli brak trafienia w opisie, sprawdzamy topics
    if not matched_engine:
        for engine, keywords in ENGINE_TOPIC_KEYWORDS.items():
            if any(kw in topics for kw in keywords):
                matched_engine = engine
                break

    # 3. jeśli nadal brak trafienia, sprawdzamy język (GDScript -> Godot)
    if not matched_engine and language == "GDScript":
        matched_engine = "Godot"

    if matched_engine:
        engine_counts[matched_engine] = engine_counts.get(matched_engine, 0) + 1

sorted_engines = sorted(engine_counts.items(), key=lambda x: (-x[1], x[0]))

if sorted_engines:
    max_count = sorted_engines[0][1]
    max_name_len = max(len(engine) for engine, _ in sorted_engines)
    BAR_WIDTH = 25
    lines = ["```text"]
    for engine, count in sorted_engines:
        bar_len = round((count / max_count) * BAR_WIDTH)
        bar = "█" * bar_len + "░" * (BAR_WIDTH - bar_len)
        lines.append(f"{engine.ljust(max_name_len)} {bar} {count}")
    lines.append("```")
    table = "\n".join(lines)
else:
    table = "_Brak danych o silnikach._"

with open("README.md", "r", encoding="utf-8") as f:
    content = f.read()

start = "<!--START_ENGINES-->"
end = "<!--END_ENGINES-->"
new_content = content.split(start)[0] + start + "\n" + table + "\n" + end + content.split(end)[1]

with open("README.md", "w", encoding="utf-8") as f:
    f.write(new_content)
