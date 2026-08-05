# 公開手順（GitHub Pages）

**✅ 公開済み（2026-08-06）**

- サイト: https://yumesuisho-cyber.github.io/yume-site/
- ゲーム: https://yumesuisho-cyber.github.io/yume-site/labs/yoru-wo-kiyomeru.html
- リポジトリ: github.com/yumesuisho-cyber/yume-site（Public）
- OGP設定済み。noteの自己紹介記事（④の先頭）からリンク済み
- 更新方法: ローカルの yume-site-upload を直して、GitHubに再アップロード（上書き）

以下は公開時に使った手順の記録。

---

## 大前提（これだけは守る）

**記事のリポジトリ（articles）は絶対に公開しない。**
あそこには下書き・有料記事の原稿・引き継ぎメモが入っている。
公開用には、まっさらなリポジトリを**別に**作る。

---

## 手順1: 公開用リポジトリを作る

1. github.com にログイン（アカウント: yumesuisho-cyber）
2. 右上の「+」→「New repository」
3. 名前は `yume-site` （英数字なら何でもよい。URLの一部になる）
4. **Public** を選ぶ（Pagesで公開するにはPublicにする必要がある）
5. 「Add a README file」にチェックを入れて作成

## 手順2: ファイルを入れる

公開するのは**完成品だけ**。設計書やメモは入れない。

```
yume-site/
├── index.html          ← 公式サイト本体
├── illust/             ← サイトとゲームの画像ぜんぶ
│   ├── hero.png
│   ├── about.png
│   ├── work.png
│   ├── ogp.png
│   ├── favicon.png
│   ├── card-1〜4.png
│   ├── luna-sprite.png
│   └── luna-title.png
└── labs/
    └── yoru-wo-kiyomeru.html   ← ゲーム
```

入れ方はどちらでもよい:

- **かんたんな方**: リポジトリのページで「Add file」→「Upload files」に、
  フォルダごとドラッグ＆ドロップ →「Commit changes」
- **ローカルのClaude Codeに頼む方**: 「claude-練習の完成品を yume-site リポジトリに
  プッシュして。設計書やメモは入れないで」と指示する

※ゲームのHTML内の画像パスは `../illust/...` になっている必要がある
（labs/ の中から一つ上の illust/ を見るため）。表示が壊れていたら
ローカルのClaude Codeに「labs内のゲームから画像が読めるようパスを直して」と頼む。

## 手順3: Pagesをオンにする

1. リポジトリの「Settings」→ 左メニューの「Pages」
2. 「Source」を「Deploy from a branch」に
3. Branch を `main`、フォルダを `/ (root)` にして「Save」
4. 数分待つと、上部に緑色でURLが出る:
   `https://yumesuisho-cyber.github.io/yume-site/`

これで公開完了。ゲームは `https://yumesuisho-cyber.github.io/yume-site/labs/yoru-wo-kiyomeru.html`

## 手順4: 公開後にやること（3つ）

1. **スマホの実機で開く**（サイトの崩れと、ゲームの指操作をここで最終確認）
2. **OGP画像のURLを直す**: index.html の `og:image` は、公開後は
   `https://yumesuisho-cyber.github.io/yume-site/illust/ogp.png` という
   完全なURLにする必要がある（相対パスだとSNSに画像が出ない）。
   ローカルのClaude Codeに「og:imageを公開URLに直して」と頼めばよい
3. **noteやXでリンクを貼る前に**、X の Card Validator 等でOGPが出るか確認
   （出なくても、貼り直せば反映されることが多い。焦らない）

## 更新するとき

ファイルを直して、同じ場所にアップロードし直すだけ（上書きされる）。
反映まで数分かかることがある。

## 覚えておくこと

- 公開＝**世界中の誰でも見られる**状態。載せるものは「noteに書けるもの」と同じ基準で
- お問い合わせフォームは見た目だけ（送信先未設定）。本当に受け取りたくなったら
  その時に仕組みを足す（フォームサービス連携。急がない）
- Pagesは無料。アクセス数を気にする必要はない
