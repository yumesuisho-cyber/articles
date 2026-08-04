# 次のカード.py
# 朝活オラクルカード記事の「次に引けるカード」を、テンプレのマスターリストと
# 過去記事から自動で計算する。
#
# 使い方:
#   python3 dev/tools/次のカード.py                  続きの日から7日分を提案
#   python3 dev/tools/次のカード.py 2026-08-10       その日から7日分を提案
#   python3 dev/tools/次のカード.py 2026-08-10 3     その日から3日分を提案
#   python3 dev/tools/次のカード.py --一覧           全52枚の最終使用日と次回使用可能日
#
# ルールの出典:
#   引き継ぎ/引き継ぎ指示文.md
#     「同じカードは14日以上あける。未使用・長期未使用を優先して選ぶ」
#   ルール/朝活オラクルカード記事_完全運用テンプレート_v3.5.md
#     「全52枚カードマスターリスト」＝カード名とテーマの正
#
# カード名とテーマはマスターリストを正とする（記事本文からは取らない）。
# 過去記事は旧テーマのまま据え置く方針なので、記事から拾うと
# 「Mystic Meadow＝聖域」のような古いテーマを表示してしまうため。
# 使用日は記事のファイル名から読むので、記事を書き足すだけで最新になる。

import re
import sys
import unicodedata
from datetime import date, timedelta
from pathlib import Path

# 同じカードを再び使うまでに、最低これだけあける
インターバル日数 = 14

リポジトリ = Path(__file__).resolve().parents[2]
記事フォルダ = リポジトリ / "記事" / "朝活"
テンプレ = リポジトリ / "ルール" / "朝活オラクルカード記事_完全運用テンプレート_v3.5.md"

曜日 = ["月", "火", "水", "木", "金", "土", "日"]


def 表示幅(s):
    """全角文字を2文字ぶんとして数える（表の桁をそろえるため）"""
    return sum(2 if unicodedata.east_asian_width(c) in "FWA" else 1 for c in s)


def 幅そろえ(s, 幅):
    return s + " " * max(0, 幅 - 表示幅(s))


def 日付表示(d):
    return f"{d.isoformat()}（{曜日[d.weekday()]}）"


def 照合キー(名前):
    """単数形・複数形・大文字小文字の違いを吸収する

    記事は「Guardian of the Land」、マスターリストは公式の複数形
    「Guardians of the Land」で書かれているため。
    """
    語 = re.sub(r"[^a-z\s]", "", 名前.lower()).split()
    return " ".join(w[:-1] if len(w) > 3 and w.endswith("s") else w for w in 語)


def マスターリストを読む():
    """テンプレの「全52枚カードマスターリスト」から {照合キー: (英名, テーマ)} を作る"""
    if not テンプレ.is_file():
        sys.exit(f"テンプレートが見つかりません: {テンプレ}")
    本文 = テンプレ.read_text(encoding="utf-8")

    m = re.search(r"全52枚カードマスターリスト(.+?)\n\\?-{3,}", 本文, re.DOTALL)
    if not m:
        sys.exit("テンプレートの中に「全52枚カードマスターリスト」が見つかりませんでした")

    カード = {}
    順番 = []
    for 行 in m.group(1).splitlines():
        # 「1\. Air Spirit（知識）」の形（Markdownのエスケープつき）
        mm = re.match(r"^\s*\d+\\?\.\s*(.+?)（(.+?)）\s*$", 行)
        if not mm:
            continue
        英名, テーマ = mm.group(1).strip(), mm.group(2).strip()
        カード[照合キー(英名)] = (英名, テーマ)
        順番.append(照合キー(英名))
    if not カード:
        sys.exit("マスターリストからカードを1枚も読み取れませんでした")
    return カード, 順番


def 記事を読む(マスター):
    """記事フォルダを走査して {照合キー: [使用日, ...]} を返す"""
    if not 記事フォルダ.is_dir():
        sys.exit(f"記事フォルダが見つかりません: {記事フォルダ}")

    使用履歴 = {}
    照合できず = []
    for f in sorted(記事フォルダ.glob("*.md")):
        m = re.match(r"^(\d{4}-\d{2}-\d{2})_(.+)$", f.stem)
        if not m:
            continue  # README など、記事以外のファイルは飛ばす
        使用日 = date.fromisoformat(m.group(1))

        英名 = 記事のカード名(f) or m.group(2).replace("-", " ")
        キー = 照合キー(英名)
        if キー not in マスター:
            照合できず.append((f.name, 英名))
            continue
        使用履歴.setdefault(キー, []).append(使用日)

    if not 使用履歴:
        sys.exit(f"記事が1本も見つかりませんでした: {記事フォルダ}")
    return 使用履歴, 照合できず


def 記事のカード名(ファイル):
    """本文の「**カード名：Pegasus（ペガサス：超越）**」から英語名を取り出す"""
    try:
        本文 = ファイル.read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.search(r"^\*\*カード名：(.+?)\*\*", 本文, re.MULTILINE)
    if not m:
        return None
    生 = m.group(1).strip()
    m2 = re.match(r"^(.+?)（", 生)
    return (m2.group(1) if m2 else 生).strip()


def 表示名(マスター, キー):
    英名, テーマ = マスター[キー]
    return f"{英名}（{テーマ}）"


def 使えるか(使用日一覧, 対象日, 追加=()):
    """対象日に使えるか（前後どちらにも14日以上あいているか）

    記事は先の日付まで書き置きするので、過去だけでなく未来の使用日も見る。
    """
    for d in list(使用日一覧) + list(追加):
        if abs((対象日 - d).days) < インターバル日数:
            return False
    return True


def 並び順(キー, 使用履歴):
    """記録に使用のないカードを最優先、次に最終使用日が古い順"""
    日付 = 使用履歴.get(キー)
    if not 日付:
        return (0, date.min, キー)  # 記録上まだ使っていない
    return (1, max(日付), キー)


def 提案する(マスター, 順番, 使用履歴, 開始日, 日数):
    予定 = {}
    行 = []
    for i in range(日数):
        対象日 = 開始日 + timedelta(days=i)
        候補 = [
            キー
            for キー in 順番
            if 使えるか(使用履歴.get(キー, []), 対象日, 予定.get(キー, []))
        ]
        if not 候補:
            行.append((対象日, None, None))
            continue
        キー = min(候補, key=lambda k: 並び順(k, 使用履歴))
        予定.setdefault(キー, []).append(対象日)
        日付 = 使用履歴.get(キー)
        補足 = (
            "★ 記録に使用なし（最優先）"
            if not 日付
            else f"前回 {max(日付)}（{(対象日 - max(日付)).days}日ぶり）"
        )
        行.append((対象日, キー, 補足))
    return 行


def 一覧を出す(マスター, 順番, 使用履歴):
    今日 = date.today()
    print(f"\n🌙 カード一覧（マスターリスト {len(順番)}枚）\n")
    幅 = max(表示幅(表示名(マスター, k)) for k in 順番) + 2
    print(f"  {幅そろえ('カード', 幅)}{幅そろえ('最終使用日', 16)}{幅そろえ('次に使える日', 16)}回数")
    print(f"  {'-' * (幅 + 42)}")
    for キー in sorted(順番, key=lambda k: 並び順(k, 使用履歴)):
        日付 = 使用履歴.get(キー)
        if not 日付:
            print(f"  {幅そろえ(表示名(マスター, キー), 幅)}{幅そろえ('― 記録なし ―', 16)}{幅そろえ('いつでも', 16)}0回  ★最優先")
            continue
        最終 = max(日付)
        次 = 最終 + timedelta(days=インターバル日数)
        印 = "  ← 今すぐ使える" if 次 <= 今日 else ""
        print(
            f"  {幅そろえ(表示名(マスター, キー), 幅)}"
            f"{幅そろえ(最終.isoformat(), 16)}"
            f"{幅そろえ(次.isoformat(), 16)}"
            f"{len(日付)}回{印}"
        )
    print()


def main():
    引数 = sys.argv[1:]

    マスター, 順番 = マスターリストを読む()
    使用履歴, 照合できず = 記事を読む(マスター)

    全日付 = [d for v in 使用履歴.values() for d in v]
    未使用 = [k for k in 順番 if k not in 使用履歴]
    print(f"\n記事 {len(全日付)}本（{min(全日付)} 〜 {max(全日付)}）／マスターリスト {len(順番)}枚")
    if 未使用:
        print(
            f"この{len(全日付)}本の中で使用のないカード {len(未使用)}枚: "
            + "、".join(表示名(マスター, k) for k in 未使用)
        )
        print("（この期間より前の記事はリポジトリにないため、それ以前の使用は判定できません）")
    if 照合できず:
        print("\n⚠ マスターリストに載っていないカード名の記事があります")
        for ファイル名, 英名 in 照合できず:
            print(f"   {ファイル名}: {英名}")

    if 引数 and 引数[0] in ("--一覧", "-l"):
        一覧を出す(マスター, 順番, 使用履歴)
        return

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

    行 = 提案する(マスター, 順番, 使用履歴, 開始日, 日数)
    幅 = max((表示幅(表示名(マスター, k)) for _, k, _ in 行 if k), default=20) + 2
    for 対象日, キー, 補足 in 行:
        if キー is None:
            print(f"  {日付表示(対象日)}  使えるカードがありません（全部14日以内に使用済み）")
            continue
        print(f"  {日付表示(対象日)}  {幅そろえ(表示名(マスター, キー), 幅)}{補足}")

    print(
        f"\n※ カード名とテーマはマスターリスト（テンプレv3.5）の正式版です。"
        f"\n※ 同じカードは{インターバル日数}日以上あけるルールを満たすものから、"
        "記録に使用なし → 最終使用日が古い順に選んでいます。"
    )
    print("※ 提案なので、季節や気分で入れ替えて大丈夫です🌙\n")


if __name__ == "__main__":
    main()
