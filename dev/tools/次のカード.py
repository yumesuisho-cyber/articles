# 次のカード.py
# 朝活オラクルカード記事の「次に引けるカード」を、過去記事から自動で計算する。
#
# 使い方:
#   python3 dev/tools/次のカード.py                  明日から7日分を提案
#   python3 dev/tools/次のカード.py 2026-08-10       その日から7日分を提案
#   python3 dev/tools/次のカード.py 2026-08-10 3     その日から3日分を提案
#   python3 dev/tools/次のカード.py --一覧           全カードの最終使用日と次回使用可能日
#
# ルールの出典: 引き継ぎ/引き継ぎ指示文.md
#   「同じカードは14日以上あける。未使用・長期未使用を優先して選ぶ」
#
# 日付はファイル名（2026-05-04_forest-guardian.md）から、カード名は本文の
# 「**カード名：**」から読む。引き継ぎメモの使用履歴表を手で更新しなくても、
# 記事を書き足すだけで常に最新の状態が計算される。

import re
import sys
import unicodedata
from datetime import date, timedelta
from pathlib import Path

# 同じカードを再び使うまでに、最低これだけあける
インターバル日数 = 14

記事フォルダ = Path(__file__).resolve().parents[2] / "記事" / "朝活"

曜日 = ["月", "火", "水", "木", "金", "土", "日"]


def 表示幅(s):
    """全角文字を2文字ぶんとして数える（表の桁をそろえるため）"""
    return sum(2 if unicodedata.east_asian_width(c) in "FWA" else 1 for c in s)


def 幅そろえ(s, 幅):
    return s + " " * max(0, 幅 - 表示幅(s))


def 日付表示(d):
    return f"{d.isoformat()}（{曜日[d.weekday()]}）"


def 記事を読む():
    """記事フォルダを走査して {カード名: {"日付": [...], "表示": "...", "slug": {...}}} を返す

    まとめる単位はファイル名（slug）ではなく、本文の「**カード名：**」から取った
    英語のカード名。ファイル名は過去に付け間違いがあり、同じカードが2つの名前で
    保存されていることがあるため（例: forest-guardian と guardian-of-the-land が
    どちらも Guardian of the Land）。ファイル名で数えると、同じカードを14日以内に
    2回提案してしまう。
    """
    if not 記事フォルダ.is_dir():
        sys.exit(f"記事フォルダが見つかりません: {記事フォルダ}")

    履歴 = {}
    for f in sorted(記事フォルダ.glob("*.md")):
        m = re.match(r"^(\d{4}-\d{2}-\d{2})_(.+)$", f.stem)
        if not m:
            continue  # README など、記事以外のファイルは飛ばす
        使用日 = date.fromisoformat(m.group(1))
        slug = m.group(2)

        英名, 表示 = カード名を取り出す(f)
        キー = 英名 or slug  # 本文から取れないときだけファイル名で代用する

        情報 = 履歴.setdefault(キー, {"日付": [], "表示": None, "slug": set()})
        情報["日付"].append(使用日)
        情報["slug"].add(slug)
        # 表示名は、いちばん新しい記事のものを採用する
        # （過去記事は訳語がゆれていることがあるため）
        if 表示:
            情報["表示"] = 表示

    if not 履歴:
        sys.exit(f"記事が1本も見つかりませんでした: {記事フォルダ}")
    return 履歴


def カード名を取り出す(ファイル):
    """本文の「**カード名：Pegasus（ペガサス：超越）**」から (英語名, 表示名) を返す"""
    try:
        本文 = ファイル.read_text(encoding="utf-8")
    except OSError:
        return None, None
    m = re.search(r"^\*\*カード名：(.+?)\*\*", 本文, re.MULTILINE)
    if not m:
        return None, None
    生 = m.group(1).strip()
    # 「Pegasus（ペガサス：超越）」→ 英語名 "Pegasus" ／ 表示 "Pegasus（超越）"
    m2 = re.match(r"^(.+?)（(?:.*?：)?(.+?)）$", 生)
    if m2:
        return m2.group(1).strip(), f"{m2.group(1).strip()}（{m2.group(2).strip()}）"
    return 生, 生


def 使えるか(情報, 対象日, 追加の使用日=()):
    """対象日に、そのカードを使えるか（前後どちらにも14日以上あいているか）

    記事は先の日付まで書き置きすることがあるので、過去だけでなく未来も見る。
    """
    for d in list(情報["日付"]) + list(追加の使用日):
        if abs((対象日 - d).days) < インターバル日数:
            return False
    return True


def 最終使用日(情報):
    return max(情報["日付"])


def 提案する(履歴, 開始日, 日数):
    予定 = {}  # カード名 -> [この実行で割り当てた日付]
    行 = []
    for i in range(日数):
        対象日 = 開始日 + timedelta(days=i)
        候補 = [
            (キー, 情報)
            for キー, 情報 in 履歴.items()
            if 使えるか(情報, 対象日, 予定.get(キー, []))
        ]
        if not 候補:
            行.append((対象日, None, None, None))
            continue
        # 未使用・長期未使用を優先 ＝ 最終使用日がいちばん古いものを選ぶ
        キー, 情報 = min(候補, key=lambda x: (最終使用日(x[1]), x[0]))
        予定.setdefault(キー, []).append(対象日)
        あけた日数 = (対象日 - 最終使用日(情報)).days
        行.append((対象日, キー, 情報, あけた日数))
    return 行


def 一覧を出す(履歴):
    print(f"\n🌙 カード一覧（{len(履歴)}種類）\n")
    今日 = date.today()
    幅 = max(表示幅(表示名(キー, 情報)) for キー, 情報 in 履歴.items()) + 2
    print(f"  {幅そろえ('カード', 幅)}{幅そろえ('最終使用日', 16)}{幅そろえ('次に使える日', 16)}回数")
    print(f"  {'-' * (幅 + 40)}")
    for キー, 情報 in sorted(履歴.items(), key=lambda x: 最終使用日(x[1])):
        最終 = 最終使用日(情報)
        次 = 最終 + timedelta(days=インターバル日数)
        印 = "  ← 今すぐ使える" if 次 <= 今日 else ""
        print(
            f"  {幅そろえ(表示名(キー, 情報), 幅)}"
            f"{幅そろえ(最終.isoformat(), 16)}"
            f"{幅そろえ(次.isoformat(), 16)}"
            f"{len(情報['日付'])}回{印}"
        )

    ゆれ = {k: v["slug"] for k, v in 履歴.items() if len(v["slug"]) > 1}
    if ゆれ:
        print("\n  ⚠ 同じカードが複数のファイル名で保存されています（数え間違いのもと）")
        for k, slugs in ゆれ.items():
            print(f"     {k}: {' / '.join(sorted(slugs))}")
        print("     ※ このツールは本文のカード名でまとめているので、集計は正しく出ています")
    print()


def 表示名(キー, 情報):
    return 情報["表示"] or キー


def main():
    引数 = sys.argv[1:]

    履歴 = 記事を読む()
    全日付 = [d for 情報 in 履歴.values() for d in 情報["日付"]]
    print(f"\n記事 {len(全日付)}本（{min(全日付)} 〜 {max(全日付)}）／カード {len(履歴)}種類")

    if 引数 and 引数[0] in ("--一覧", "-l"):
        一覧を出す(履歴)
        return

    # 開始日：指定がなければ「最後に記事がある日の翌日」から
    if 引数:
        try:
            開始日 = date.fromisoformat(引数[0])
        except ValueError:
            sys.exit(f"日付は 2026-08-10 の形で指定してください（受け取った値: {引数[0]}）")
    else:
        開始日 = max(全日付) + timedelta(days=1)

    日数 = 7
    if len(引数) >= 2:
        if not 引数[1].isdigit() or int(引数[1]) < 1:
            sys.exit(f"日数は1以上の整数で指定してください（受け取った値: {引数[1]}）")
        日数 = int(引数[1])

    print(f"\n── {日付表示(開始日)} から {日数}日分の提案 ──\n")

    行 = 提案する(履歴, 開始日, 日数)
    幅 = max(
        (表示幅(表示名(キー, 情報)) for _, キー, 情報, _ in 行 if キー),
        default=20,
    ) + 2
    for 対象日, キー, 情報, あけた日数 in 行:
        if キー is None:
            print(f"  {日付表示(対象日)}  使えるカードがありません（全部14日以内に使用済み）")
            continue
        print(
            f"  {日付表示(対象日)}  {幅そろえ(表示名(キー, 情報), 幅)}"
            f"前回 {最終使用日(情報)}（{あけた日数}日ぶり）"
        )

    print(
        f"\n※ 同じカードは{インターバル日数}日以上あけるルールを満たすものから、"
        "最終使用日がいちばん古い順に選んでいます。"
    )
    print("※ 提案なので、季節や気分で入れ替えて大丈夫です🌙\n")


if __name__ == "__main__":
    main()
