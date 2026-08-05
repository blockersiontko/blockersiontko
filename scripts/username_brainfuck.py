with open("README.md", "r", encoding="utf-8") as f:
    content = f.read()

start = "<!--USERNAME:START-->"
end = "<!--USERNAME:END-->"

new_content = (
    content.split(start)[0]
    + start
    + "\n"
    + "# "
    + brainfuck_output
    + "\n"
    + end
    + content.split(end)[1]
)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(new_content)
