import sqlite3
import json
import os
from config import DATA_DIR

DB_PATH = "roottrek.db"  # local read-only copy of the website's dev.db (gitignored)


def tiptap_to_text(node) -> str:
    """Recursively pull readable text out of a TipTap JSON node."""
    if node is None:
        return ""
    parts = []
    if isinstance(node, dict):
        if isinstance(node.get("text"), str):
            parts.append(node["text"])
        # some custom blocks (banners, terminal blocks) keep text in attrs
        attrs = node.get("attrs") or {}
        for key in ("text", "title", "code"):
            if isinstance(attrs.get(key), str) and attrs[key]:
                parts.append(attrs[key])
        for child in node.get("content") or []:
            parts.append(tiptap_to_text(child))
        if node.get("type") in ("paragraph", "heading"):
            parts.append("\n")
    elif isinstance(node, list):
        for child in node:
            parts.append(tiptap_to_text(child))
    return " ".join(p for p in parts if p)


def export():
    os.makedirs(DATA_DIR, exist_ok=True)
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)  # mode=ro = read-only
    con.row_factory = sqlite3.Row
    count = 0

    for row in con.execute("SELECT title, slug, content FROM BlogPost WHERE published = 1"):
        body = tiptap_to_text(json.loads(row["content"] or "{}"))
        with open(os.path.join(DATA_DIR, f"blog-{row['slug']}.md"), "w", encoding="utf-8") as f:
            f.write(f"# {row['title']}\n\n{body}")
        count += 1

    for row in con.execute(
        "SELECT title, slug, tagline, background, content FROM Project WHERE published = 1"
    ):
        body = tiptap_to_text(json.loads(row["content"] or "{}"))
        header = f"# {row['title']}\n\n{row['tagline']}\n\n{row['background']}\n\n"
        with open(os.path.join(DATA_DIR, f"project-{row['slug']}.md"), "w", encoding="utf-8") as f:
            f.write(header + body)
        count += 1

    con.close()
    print(f"Exported {count} published posts to {DATA_DIR}/")


if __name__ == "__main__":
    export()