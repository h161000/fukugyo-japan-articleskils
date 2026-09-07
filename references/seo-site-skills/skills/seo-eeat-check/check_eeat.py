#!/usr/bin/env python3
"""
SEO・E-E-A-Tチェックスクリプト

使い方:
    python3 skills/seo-eeat-check/check_eeat.py src/content/articles/<slug>.mdx

エラー/警告を検出して標準出力に列挙する。
exit code:
    0: エラーなし（警告は出てもOK）
    1: エラーあり（push禁止）
"""
import sys
import re
import os

# ----- ホワイトリスト/ブラックリスト -----
WHITELIST_PATTERNS = [
    r"\.go\.jp",
    r"\.lg\.jp",
    r"kokusen\.go\.jp",
    r"houjin-bangou\.nta\.go\.jp",
    r"chiebukuro\.yahoo\.co\.jp",
    r"asahi\.com",
    r"nikkei\.com",
    r"mainichi\.jp",
    r"yomiuri\.co\.jp",
    r"sankei\.com",
    r"nhk\.or\.jp",
    r"nhk\.jp",
]

BLACKLIST_PATTERNS = [
    (r"ameblo\.jp", "Ameba（個人検証ブログの定番、ほぼ競合）"),
    (r"note\.com", "noteの個人検証記事はほぼ競合"),
    (r"hatenablog\.com", "はてなブログ（競合の温床）"),
    (r"livedoor\.blog", "ライブドアブログ（競合）"),
    (r"\.xsrv\.jp", "個人ブログホスティング"),
    (r"\.wp\.com", "WordPress.com 個人ブログ"),
    (r"\.fc2\.com", "FC2ブログ"),
]

# 自社ドメイン（リンクされてもOK）
OWN_DOMAINS = [
    "yakkei.jp",
    "fukugyo-blog.yekouxiuxiong75.workers.dev",
]

# プレスリリース系（リンクは中立）
PR_DOMAINS = [
    "prtimes.jp",
    "atpress.ne.jp",
    "valuepress.com",
    "pr-times.com",
]


# ----- ユーティリティ -----
def color(s, c):
    codes = {"red": "31", "yellow": "33", "green": "32", "cyan": "36", "gray": "90"}
    return f"\033[{codes.get(c, '0')}m{s}\033[0m"


def parse_frontmatter(content):
    """簡易YAMLパース"""
    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).split("\n"):
        kv = re.match(r"^(\w+):\s*(.*)$", line)
        if kv:
            key, val = kv.group(1), kv.group(2).strip()
            val = val.strip('"').strip("'")
            if val.startswith("[") and val.endswith("]"):
                items = re.findall(r'"([^"]*)"', val)
                if not items:
                    items = [v.strip().strip("'") for v in val[1:-1].split(",") if v.strip()]
                val = items
            fm[key] = val
    return fm


def get_body(content):
    """frontmatter / import / コードブロックを除いた本文"""
    body = re.sub(r"^---.*?---\n", "", content, count=1, flags=re.DOTALL)
    body = re.sub(r"^import .*$", "", body, flags=re.MULTILINE)
    return body


# ----- チェック関数 -----
def check_frontmatter(fm):
    errors, warnings = [], []
    # verdict は kensho 型専用（type未指定は従来どおりkensho扱い）。
    # matome/howto/columnはcheck-article.shの#0チェックで逆に「verdictを付けるとFAIL」になるため、
    # ここでも型に応じて要否を切り替える（型システム導入前の実装のまま取り残されていたバグ修正）。
    article_type = fm.get("type", "kensho")
    if article_type == "kensho":
        if "verdict" not in fm:
            errors.append("[1] frontmatter に verdict が未設定")
        elif fm["verdict"] not in ("safe", "unknown", "warning", "danger"):
            errors.append(f"[1] verdict の値が不正: {fm['verdict']}")
    elif "verdict" in fm:
        errors.append(f"[1] type: {article_type} では verdict を付けない（kensho専用）")

    if "category" not in fm or fm["category"] not in ("fukugyo", "toushi"):
        errors.append("[2] category が fukugyo / toushi のいずれかではない")

    if "publishedAt" not in fm:
        errors.append("[3] publishedAt が未設定")

    title = fm.get("title", "")
    # タイトルは検索ワードを多く含めるため長くなる（現行SEO方針）。
    # 上限固定はこの方針と矛盾するため、極端な短さ/長さだけ警告する（落とさない）。
    if not (24 <= len(title) <= 60):
        warnings.append(f"[6] title 文字数が 24〜60 を外れている（現在: {len(title)}）: {title}")

    desc = fm.get("description", "")
    if "？" in desc or "?" in desc:
        errors.append("[7] description に疑問形「？」が含まれている")

    image = fm.get("image", "")
    if not image.startswith("/images/"):
        errors.append(f"[8] image パスが /images/ で始まっていない: {image}")

    return errors, warnings


def check_external_links(body):
    """本文中のすべてのhttp(s) URLを抽出してチェック"""
    errors, warnings = [], []
    urls = re.findall(r"https?://[^\s\)\"<>]+", body)

    for url in urls:
        # 自社ドメインはスキップ
        if any(d in url for d in OWN_DOMAINS):
            continue
        # PRドメインはスキップ
        if any(d in url for d in PR_DOMAINS):
            continue

        # ブラックリスト判定
        for pat, reason in BLACKLIST_PATTERNS:
            if re.search(pat, url):
                errors.append(f"[10] 競合ブログへのリンク検出: {url} ({reason})")
                break
        else:
            # ホワイトリスト判定
            if any(re.search(p, url) for p in WHITELIST_PATTERNS):
                warnings.append(f"[9] ホワイトリスト外部リンク（必要性を要確認）: {url}")
            else:
                warnings.append(f"[11] グレー外部リンク（人間判断）: {url}")

    return errors, warnings


def check_lp_urls(body):
    """LP・特商法・公式サイトっぽいURLが含まれていないか"""
    errors = []
    suspicious = re.findall(r"https?://[^\s\)\"<>]*(?:lp|landing|tokushoho|tokushou|tokutei|special|official|service)[^\s\)\"<>]*", body, re.I)
    for url in suspicious:
        if any(d in url for d in OWN_DOMAINS):
            continue
        # 公的機関(.go.jp/.lg.jp)はE-E-A-T強化で貼ることを必須にしている先なので
        # 「LPっぽいURL」として弾かない（fbssで踏んだ誤検知）。
        if re.search(r"\.go\.jp|\.lg\.jp", url):
            continue
        errors.append(f"[11] LP・特商法・公式サイトっぽいURLを検出: {url}")
    return errors


def check_kikan_mention(body, category):
    """公的機関言及チェック"""
    errors = []
    if category == "toushi":
        if not re.search(r"金融庁|消費者庁|国民生活センター", body):
            errors.append("[12] 投資系記事だが金融庁・消費者庁・国民生活センターのいずれにも言及していない")
    elif category == "fukugyo":
        if not re.search(r"消費者庁|国民生活センター", body):
            errors.append("[13] 副業系記事だが消費者庁・国民生活センターのいずれにも言及していない")
    return errors


def check_profile_link(body):
    # 注意: 当サイト群では著者プロフィール（/profile）はArticleLayout側で
    # 全記事に自動表示される（本文には書かない）。本文中の/profileを必須にすると
    # 全記事が誤爆するため、main()からは呼ばない。互換のため関数は残す。
    if "/profile" not in body:
        return ["[14] 著者プロフィール（/profile）への内部リンクが本文中に存在しない"]
    return []


# 公的相談窓口へ"誘導"する文脈語（相談導線をLINEへ一本化するための禁止判定に使う）
_YUDO_CTX = r"相談|連絡|電話|窓口|問い合わせ|ダイヤル|ホットライン|消費生活|かけ|通報"


def check_kikan_yudo(body):
    """188・#9110 等の公的相談窓口へ"誘導"する本文プロセを禁止する。
    相談導線は全てLINEへ一本化する方針のため（トップ最下部の公的相談先コンポーネントとは別）。
    法人番号など数字の偶然一致を避けるため、文脈語が近接（前後30字）する場合のみ検出する。"""
    errors = []
    # #9110（警察相談専用電話）
    for m in re.finditer(r"#?9110", body):
        ctx = body[max(0, m.start() - 30):min(len(body), m.end() + 30)]
        if re.search(_YUDO_CTX, ctx):
            errors.append("[22] #9110（警察相談）への誘導を検出 → 相談導線はLINEへ一本化（公的窓口はトップ最下部に集約）")
            break
    # 188（消費者ホットライン）
    for m in re.finditer(r"188", body):
        ctx = body[max(0, m.start() - 30):min(len(body), m.end() + 30)]
        if re.search(_YUDO_CTX + r"|消費者", ctx):
            errors.append("[23] 消費者ホットライン188への誘導を検出 → 相談導線はLINEへ一本化（公的窓口はトップ最下部に集約）")
            break
    return errors


def check_first_hand(body):
    """②一次情報：実際に自分の手で調べた痕跡があるか（warnのみ・落とさない）。
    無ければ「こたつ記事化」リスクとして警告する。最初はwarn、こたつ補強後にhard化を検討。"""
    signals = (
        r"実際に(登録|申し込|試|入力|調査|確認|問い合わせ)"
        r"|登録してみ|登録すると|登録した(ところ|あと|後)|申し込んでみ|試してみ"
        r"|フォームに入力|特商法ページ(を|で)?(確認|見|チェック)"
        r"|法人番号(を|で)?(検索|確認|調べ)|問い合わせ(て|た|まし)"
        r"|自分(で|の手で)(調|確認|登録|試)|スクリーンショット|スクショ|実際の画面"
    )
    if not re.search(signals, body):
        return ["[24] ②一次情報の痕跡が見当たらない（実際の登録・調査・確認の描写がない＝こたつ化リスク／warn）"]
    return []


def check_cite_in_blockquote(content):
    """引用ブロックに <cite> が付いているか"""
    errors = []
    lines = content.split("\n")
    in_quote = False
    quote_start = 0
    has_cite = False
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith(">"):
            if not in_quote:
                in_quote = True
                quote_start = i + 1
                has_cite = False
            if "<cite>" in s:
                has_cite = True
        else:
            if in_quote:
                if not has_cite:
                    errors.append(f"[15] 引用ブロック（L{quote_start}付近）に <cite> が付いていない")
                in_quote = False
    return errors


def check_image_alt(content):
    errors = []
    for m in re.finditer(r"!\[([^\]]*)\]\(([^)]+)\)", content):
        alt, src = m.group(1), m.group(2)
        if not alt.strip():
            errors.append(f"[16] 画像 alt が空: {src}")
    return errors


def check_forbidden_words(body):
    errors = []
    # 引用ブロック（> で始まる行）は除外する。特商法の条文やLPの文言、読者から届いた
    # 文面は原文ママで載せるのが原則で、こちらの言葉づかいではないため書き換えられない
    # （[[quote-must-match-screenshot]]）。地の文だけを走査する。
    body = "\n".join(
        ln for ln in body.split("\n") if not ln.strip().startswith(">")
    )
    if re.search(r"(?<![a-zA-Z])LP(?![a-zA-Z])", body):
        errors.append('[17] 「LP」という単語が含まれている → 「広告ページ」「募集ページ」に言い換え')
    if "案件" in body:
        errors.append('[18] 「案件」という単語が含まれている → 「副業」「副業情報」に言い換え')
    if "—" in body:
        errors.append("[19] em-dash（—）が含まれている")
    if "<br" in body:
        errors.append("[20] <br> が含まれている")
    return errors


def check_component_imports(content):
    """未importのコンポーネントを使用していないかチェック"""
    errors = []
    # MDXで使われるコンポーネント一覧
    components = ["AlertBox", "Balloon", "LineButton", "FaqSchema"]
    body = get_body(content)
    for comp in components:
        usage = re.search(rf"<{comp}[\s/>]", body)
        imp = re.search(rf"import\s+{comp}\s+from", content)
        if usage and not imp:
            errors.append(f"[21] <{comp}> が使われているが import されていない → 本文が表示されなくなる致命的バグ")
    return errors


# ----- メイン -----
def main():
    if len(sys.argv) < 2:
        print("Usage: check_eeat.py <article.mdx>")
        sys.exit(1)

    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(1)

    with open(path) as f:
        content = f.read()

    fm = parse_frontmatter(content)
    body = get_body(content)

    all_errors = []
    all_warnings = []

    e, w = check_frontmatter(fm)
    all_errors += e
    all_warnings += w

    e, w = check_external_links(body)
    all_errors += e
    all_warnings += w

    all_errors += check_lp_urls(body)
    all_errors += check_image_alt(content)
    all_errors += check_forbidden_words(body)
    all_errors += check_component_imports(content)

    # --- E-E-A-T 追加チェック ---
    # 公的窓口への誘導（188/#9110）は禁止＝相談導線はLINEへ一本化（hard-fail）
    all_errors += check_kikan_yudo(body)
    # 公的機関の本文言及・引用cite・②一次情報は warn（落とさず可視化する）。
    # ※著者プロフィール(/profile)はレイアウト側で全記事自動表示のため check_profile_link は呼ばない。
    category = fm.get("category", "")
    all_warnings += check_kikan_mention(body, category)
    all_warnings += check_cite_in_blockquote(content)
    all_warnings += check_first_hand(body)

    print("=" * 60)
    print(f"SEO/E-E-A-Tチェック: {os.path.basename(path)}")
    print("=" * 60)

    if all_errors:
        print(color(f"\n❌ エラー {len(all_errors)} 件:", "red"))
        for e in all_errors:
            print("  " + color(e, "red"))

    if all_warnings:
        print(color(f"\n⚠️  警告 {len(all_warnings)} 件:", "yellow"))
        for w in all_warnings:
            print("  " + color(w, "yellow"))

    print()
    if not all_errors and not all_warnings:
        print(color("✓ All checks passed", "green"))
    elif not all_errors:
        print(color("✓ エラーなし（警告のみ・人間判断）", "green"))

    print()
    print(color("=== 人間判断項目（手動チェック必須）===", "cyan"))
    print("  H1: LP引用の内容がスクショと一致するか")
    print("  H2: 装飾なし段落が3連続していないか")
    print("  H3: 吹き出し→本文の意味重複がないか")
    print()

    sys.exit(1 if all_errors else 0)


if __name__ == "__main__":
    main()
