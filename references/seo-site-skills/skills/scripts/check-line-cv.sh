#!/usr/bin/env bash
# check-line-cv.sh — LINE登録(CV)を下げる書き方を機械判定する「見張り」。
# check-article.sh を補完する CV 専用ゲート。1つでもFAILがあれば exit 1。
# 判定パターンは全て管理人さんのメモリ(実戦で磨いた grep)由来＝誤検知を最小化。
#   FAIL(弾く): 審判者口調 / 催促NG煽り / 自己弁護フィラー   ← 高精度・0許容
#   WARN(目視): ブーメラン(先に金求めない=安全) / 赤字結論なし ← 曖昧なので落とさず喚起
# 使い方: bash scripts/check-line-cv.sh src/content/articles/<slug>.mdx
set -uo pipefail
F="${1:-}"
[ -n "$F" ] && [ -f "$F" ] || { echo "使い方: bash scripts/check-line-cv.sh <記事.mdx>"; exit 1; }

fail=0
ok(){   echo "  ✅ $1"; }
ng(){   echo "  ❌ $1"; fail=1; }
warn(){ echo "  ⚠️ $1"; }

echo "=== LINE CVチェック: ${F} ==="

# 1. 審判者口調・自己中心の気持ち報告（FAIL・0許容）
#    出典: memory/no-judge-voice-reader-subject.md の実戦grep（そのまま採用）
JUDGE='と私は思います|してほしいと思います|確かめてほしいと思います|警戒したい|引っかかりました|受け止めてほしい|疑ってほしい|判断してほしい|一度立ち止まって|ほしいところ'
hits=$(grep -nE "$JUDGE" "$F" || true)
if [ -n "$hits" ]; then
  ng "審判者口調/気持ち報告（主語を読者に・営業の直球で言い切る）"
  echo "$hits" | sed 's/^/        /' | head
else
  ok "審判者口調なし"
fi

# 2. 催促NGの不安煽り（FAIL・0許容）
#    出典: memory/fbss-no-line-nudge.md, yamato-persona-nudge-drift.md
#    NG=「見落とす/埋もれる/追加しただけだと気づかない」等の不安を理由にしたLINE催促。
#    ※「気軽にメッセージ送ってください」等のポジティブ招待は検知しない
#    ※「見落としやすいお金の話」等のLINE文脈でない"見落とし/埋もれ"は誤爆させない
#      → 2a=文脈不問の明確な催促句 / 2b=見落と・埋もれはLINE文脈が同一行にある時だけ
NUDGE_HARD='追加しただけ|気づかないかも|気づけないかも|返信できないかも'
NUDGE_CTX='(見落と|埋もれ).*(LINE|ライン|友だち|友達|友か|追加|登録|メッセージ|一言|連絡)|(LINE|ライン|友だち|友達|追加|登録|メッセージ|一言|連絡).*(見落と|埋もれ)'
hits=$(grep -nE "${NUDGE_HARD}|${NUDGE_CTX}" "$F" || true)
if [ -n "$hits" ]; then
  ng "催促NGの不安煽り（"見落とす/埋もれる"で登録を急かさない・ポジ招待に置換）"
  echo "$hits" | sed 's/^/        /' | head
else
  ok "催促NGの不安煽りなし"
fi

# 3. 自己弁護フィラー（FAIL・0許容）
#    出典: memory/voice-is-sales-talk-not-essay.md（言うほど嘘くさい）
FILLER='無理な勧誘はしません|無理な勧誘はしない|お金は一切もらいません|お金は一切いただきません|一切お金はいただきません|お金は一切かかりません'
# 「…」で引用された第三者の主張(運営の説明等)は自己弁護でないため除外
hits=$(grep -nE "$FILLER" "$F" | grep -vE '「[^」]*(無理な勧誘|お金は一切|一切お金)' || true)
if [ -n "$hits" ]; then
  ng "自己弁護フィラー（"無理な勧誘はしません"等は言うほど嘘くさい・削除）"
  echo "$hits" | sed 's/^/        /' | head
else
  ok "自己弁護フィラーなし"
fi

# 3.5 提出物の指定・成果物の約束（FAIL・0許容）
#    出典: memory/cta-dont-prescribe-what-to-send.md
#    LINEで対応する人と記事を書く人は別。記事側で「◯◯を送ってください」と提出物を決めたり
#    「△△にしてお返しします」と成果物を約束すると、対応者は前提を知らないまま受けて話が噛み合わない。
#    CTAで出していいのは「行き先」と「一緒に整理できる/次にやることを決められる」までで、
#    読者の提出物と、返す成果物は決めない。正しい型＝不安→立場2つ→差別化の一言→行き先＋気軽に相談。
#    ※「一言でいいのでお悩みや相談内容を送ってください」等の一般的な呼びかけは検知しない
#      （具体物の名詞に限定。2026-08-10に全203記事で実測し誤検知ゼロを確認）
ITEM='金額|料金|価格|プラン名|日付|日にち|書面|契約書|領収書|明細|資料|画面|スクショ|スクリーンショット|文面|口座|社名|会社名|写真|条件|人数|URL'
ASK='(送って|教えて)(ください|くださいね|もらえれば|きてください|いただければ)'
hits=$(grep -nE "(${ITEM})[^。]{0,12}${ASK}" "$F" || true)
if [ -n "$hits" ]; then
  ng "CTAで提出物を指定している（LINE担当は別人＝辻褄が合わない。立場2つ＋間口を広げる形にする）"
  echo "$hits" | sed 's/^/        /' | head
else
  ok "提出物の指定なし"
fi

PROMISE='(文章|文面|言い方|断り方|手順|やり方|読み方|見分け方|次にやること|どこから動けば|どう伝えれば)[^。]{0,16}お返し|(分けて|整理して|作って|まとめて|にして)お返し'
hits=$(grep -nE "$PROMISE" "$F" || true)
if [ -n "$hits" ]; then
  ng "CTAで成果物を約束している（対応者がその前提を知らない。"一緒に考える"までに留める）"
  echo "$hits" | sed 's/^/        /' | head
else
  ok "成果物の約束なし"
fi

# 4. ブーメラン: 先に金を求めない=安全（WARN・目視）
#    出典: memory/no-safety-claim-money-upfront.md
#    ※給付金/当選金の受取詐欺の手口批判は例外OK→落とさずWARNで目視喚起
BOOM='先にお金を求め|お金を先に求め|先に費用を求め|前払いを求めてこない|前払いを要求してこない'
hits=$(grep -nE "$BOOM" "$F" || true)
if [ -n "$hits" ]; then
  warn "ブーメラン疑い（"先に金を求めない=安全"は自分もLINE広告に費用がかかる・要目視）"
  echo "$hits" | sed 's/^/        /' | head
else
  ok "ブーメランなし"
fi

# 5. 赤字結論ボックスの有無（WARN・目視）
#    出典: memory/fbss-cvr-winning-template.md ②冒頭の赤字大文字結論
if grep -q 'e53e3e' "$F"; then
  ok "赤字結論ボックスあり（#e53e3e）"
else
  warn "赤字結論ボックス(#e53e3e)なし → 冒頭に判断を赤字で1行（勝ち型テンプレ②）"
fi

echo "----------------------------------------"
if [ "$fail" -eq 0 ]; then echo "✅ LINE CVチェック通過。"; else echo "❌ CV違反あり（FAIL）。直すまで納品しないこと。"; fi
exit $fail
