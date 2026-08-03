# 原稿チェック_余白と改行.py
# note原稿（md）の折り返し行末に半角スペース2つ（強制改行）が入っているかを検証する。
# 使い方: python3 原稿チェック_余白と改行.py 原稿ファイル.md
# 欠落があれば行番号つきで表示して終了コード1、欠落0なら「OK」を表示して終了コード0。
# ルールの出典: CLAUDE.md 文体エンジン「余白と改行（全記事共通の原稿ルール）」

import re
import sys


def is_prose(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    # 見出し・箇条書き・番号リスト・区切り線・■小見出し・引用・表は対象外
    if re.match(r"^(#{1,6}\s|[-*+]\s|\d+\.\s|■|---+$|>|\|)", s):
        return False
    # メタ情報行（「**区分：**」など）とHTMLコメント行は対象外
    if re.match(r"^\*\*.+[：:]\*\*", s) or s.startswith("<!--") or s.endswith("-->"):
        return False
    return True


def check(path: str) -> int:
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")

    ok = 0
    missing = []
    in_code = False
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        # 段落の途中の行（この行も次の行も地の文）＝折り返し行
        if is_prose(line) and is_prose(nxt):
            if line.endswith("  "):
                ok += 1
            else:
                missing.append((i + 1, line))

    if missing:
        print(f"[NG] 強制改行の欠落: {len(missing)}行（検出済みOK: {ok}行）")
        for num, line in missing:
            tail = line[-20:] if len(line) > 20 else line
            print(f"  {num}行目: …{tail}")
        print("→ 折り返し行の行末に半角スペース2つを入れてください")
        return 1

    print(f"[OK] 折り返し行 {ok}行すべてに強制改行あり。欠落0")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python3 原稿チェック_余白と改行.py 原稿ファイル.md")
        sys.exit(2)
    sys.exit(max(check(p) for p in sys.argv[1:]))
