#!/usr/bin/env bash
# check-article.sh — 記事がスキルの機械チェックを満たすか自動判定する納品ゲート。
# frontmatterの type (kensho/matome/howto/column・省略時kensho) で基準を切り替える。
# 1つでも違反があれば exit 1（＝納品/コミットさせない）。
# 使い方（サイトのルートで）: bash scripts/check-article.sh src/content/articles/<slug>.mdx
set -uo pipefail
F="${1:-}"
[ -n "$F" ] && [ -f "$F" ] || { echo "使い方: bash scripts/check-article.sh <記事.mdx>"; exit 1; }

fail=0
ok(){ echo "  ✅ $1"; }
ng(){ echo "  ❌ $1"; fail=1; }
warn(){ echo "  ⚠️ $1"; }

# 型の判定（frontmatter 1ブロック目の type: 行。無ければ kensho）
TYPE=$(awk '/^---$/{c++;next} c==1 && /^type:/{gsub(/['"'"'"]/,"",$2); print $2; exit}' "$F")
[ -z "$TYPE" ] && TYPE="kensho"

# 型別基準（design: docs/superpowers/specs/2026-06-12-article-types-kaiyu-design.md）
# 2026-08-11 kensho の基準を見直し（構成の同型化を止めるため）。
#   経緯: 2026-08-04 に fukugyo-hotline の競合(fukugyojapan.com)を実測して逆算した基準
#   （字数7,000 / 表8 / 公的リンク6 / H3）を大元へ入れた。結果、全12サイトが
#   「表を8個入れる場所」「公的リンクを6本貼る場所」を確保するために章立てを逆算しはじめ、
#   どのサイトも同じ骨格（結論→中身→料金→特商法→口コミ→確認リスト→まとめ）に収束した。
#   → 表と公的リンクの本数ゲートは外す。H3は粒度の担保として残す（管理人さん判断）。
#   → 字数は「最低5,000字以上」の床のみ。上限は設けない（案件ごとに書ける量が違うため）。
#   ⚠️ 競合実測から逆算した厳しい基準が要るサイトは、そのサイトの check-article.sh 側で
#      個別に上書きすること（例: fukugyo-hotline は 7,000/表8/公的リンク6 を自前で維持）。
#      大元に入れると全サイトの章立てが揃ってしまう。
case "$TYPE" in
  kensho) MIN_CHARS=5000; MIN_IMG=10; MIN_BAL=8; MIN_LINE=3; H2IMG=strict; MIN_TBL=0; H3MODE=strict; MIN_GOV=0 ;;
  matome) MIN_CHARS=4000; MIN_IMG=5;  MIN_BAL=3; MIN_LINE=1; H2IMG=warn;   MIN_TBL=3; H3MODE=warn;   MIN_GOV=0 ;;
  howto)  MIN_CHARS=3000; MIN_IMG=3;  MIN_BAL=3; MIN_LINE=1; H2IMG=warn;   MIN_TBL=2; H3MODE=warn;   MIN_GOV=0 ;;
  column) MIN_CHARS=1500; MIN_IMG=1;  MIN_BAL=0; MIN_LINE=0; H2IMG=warn;   MIN_TBL=0; H3MODE=off;    MIN_GOV=0 ;;
  *) echo "❌ 未知の type: ${TYPE}（kensho/matome/howto/column のいずれか）"; exit 1 ;;
esac
echo "=== 記事チェック: ${F} [型: ${TYPE}] ==="

# 0. verdict は kensho 専用
if [ "$TYPE" != "kensho" ]; then
  if awk '/^---$/{c++;next} c==1 && /^verdict:/{found=1} END{exit !found}' "$F"; then
    ng "verdict は kensho 専用（type: $TYPE では付けない）"
  else
    ok "verdict なし（$TYPE はverdict不要）"
  fi
fi

# 0.5 systemTag（LINE登録時にチャットシステムへ渡す分類）
if [ "$TYPE" = "kensho" ]; then
  if awk '/^---$/{c++;next} c==1 && /^systemTag:/{found=1} END{exit !found}' "$F"; then
    ok "systemTag あり"
  else
    ng "systemTag が無い（src/lib/systemTags.ts の17種から選ぶ）"
  fi
fi

# 1. textlint
if npx --no-install textlint "$F" >/tmp/ca_tl.txt 2>&1; then ok "textlint"; else ng "textlint 違反"; grep -E 'error' /tmp/ca_tl.txt | sed 's/^/        /' | head; fi

# 2. 画像
imgs=$(grep -c '!\[' "$F")
[ "$imgs" -ge "$MIN_IMG" ] && ok "画像 ${imgs}枚 (>=${MIN_IMG})" || ng "画像 ${imgs}枚 → ${MIN_IMG}枚未満"

# 3. 吹き出し（基準0ならスキップ）
if [ "$MIN_BAL" -gt 0 ]; then
  b=$(grep -c '<Balloon' "$F"); [ "$b" -ge "$MIN_BAL" ] && ok "吹き出し ${b} (>=${MIN_BAL})" || ng "吹き出し ${b} → ${MIN_BAL}未満"
fi

# 4. LINE誘導（基準0ならスキップ）
if [ "$MIN_LINE" -gt 0 ]; then
  l=$(grep -c '<LineButton' "$F"); [ "$l" -ge "$MIN_LINE" ] && ok "LINE誘導 ${l} (>=${MIN_LINE})" || ng "LINE誘導 ${l} → ${MIN_LINE}未満"
fi

# 5. テキストリンクが青か（Markdownリンク混入＝色指定なし＝NG）
mdlink=$(grep -nE '\]\(https?://' "$F" | grep -v '!\[' || true)
if [ -n "$mdlink" ]; then ng "Markdownリンク混入（<a style=\"color:#0000EE\"> にすること）"; echo "$mdlink" | sed 's/^/        /' | head; else ok "テキストリンク（Markdownリンクなし）"; fi
badcolor=$(grep -oE '<a [^>]*href[^>]*>' "$F" | grep -v '#0000EE' || true)
[ -z "$badcolor" ] && ok "リンク色 #0000EE 指定OK" || ng "色未指定の<a>あり（#0000EE必須）"

# 6. em ダッシュ禁止
if grep -q '——\|—' "$F"; then ng "emダッシュ（——/—）使用"; else ok "emダッシュなし"; fi

# 6.5 引用とciteが別blockquoteに割れていないか（> 本文 と > <cite> の間は空行でなく「>」でつなぐ）
citesplit=$(python3 - "$F" <<'PY'
import sys
lines=open(sys.argv[1]).read().split('\n')
bad=0
for i,ln in enumerate(lines):
    if ln.lstrip().startswith('> <cite') and i>0 and lines[i-1].strip()=='':
        bad+=1
print(bad)
PY
)
[ "$citesplit" -eq 0 ] && ok "引用とcite同一ブロック" || ng "引用とciteが空行で分断 ${citesplit}箇所（間は空行でなく「>」にする）"

# 7. 冒頭の段落数（最初のLINE誘導まで）。警告のみ
intro=$(python3 - "$F" <<'PY'
import sys
lines=open(sys.argv[1]).read().split('\n'); fm=0; inbal=False; c=0
for ln in lines:
    s=ln.strip()
    if s=='---': fm+=1; continue
    if fm<2: continue
    if s.startswith('<LineButton'): break
    if s.startswith('<Balloon'): inbal=True; continue
    if s.startswith('</Balloon'): inbal=False; continue
    if inbal or not s or s.startswith(('import','![','#')): continue
    c+=1
print(c)
PY
)
if [ "$intro" -le 10 ]; then ok "冒頭 ${intro}段落（実運用の範囲内）"; else warn "冒頭 ${intro}段落 → やや長め（落とさず警告のみ）"; fi

# 8. 各H2セクションに画像 ＋ 1文1段落 ＋ 文字数
res=$(python3 - "$F" <<'PY'
import sys,re
lines=open(sys.argv[1]).read().split('\n')
sec=None;img=0;noimg=[]
for ln in lines:
    if ln.startswith('## '):
        if sec is not None and img==0: noimg.append(sec)
        sec=ln[3:].strip();img=0
    if '![' in ln and sec is not None: img+=1
if sec is not None and img==0: noimg.append(sec)
inbal=False; fm=0; viol=0
for ln in lines:
    s=ln.strip()
    if s=='---': fm+=1; continue
    if fm<2: continue
    if s.startswith('<Balloon'): inbal=True
    if s.startswith('</Balloon'): inbal=False; continue
    if inbal: continue
    if not s or s.startswith(('>','|','#','import','<LineButton','![','</','-')): continue
    if s.count('。')>=2: viol+=1
# 文字数は「読者が実際に読む地の文」だけを数える。
# 2026-08-04修正: 以前は frontmatter・import文・リンクのURL・表の罫線まで数えており、
# 記事によっては2割ほど水増しされていた（fbss/qualia.mdx はゲート9,514に対し地の文7,650）。
fm2=0; keep=[]
for ln in lines:
    s=ln.strip()
    if s=='---': fm2+=1; continue
    if fm2<2: continue                      # frontmatter は本文ではない
    if s.startswith('import '): continue    # import文は本文ではない
    if re.match(r'^\|[\s:\-|]+\|$', s): continue   # 表の区切り行（|---|---|）
    keep.append(ln)
body="\n".join(keep)
body=re.sub(r'!\[.*?\]\(.*?\)','',body)          # 画像（altも表示されない）
body=re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', body)  # リンクは表示テキストだけ残す
body=re.sub(r'<[^>]+>','',body)                  # HTMLタグ
body=body.replace('|','')                        # 表の罫線（セルの中身は残す）
body=re.sub(r'^[#>]+\s*','',body,flags=re.M)     # 見出し記号・引用記号
n=len(re.sub(r'\s','',body))
print("%d|%d|%s"%(viol,n,";".join(noimg)))
PY
)
viol=$(echo "$res"|cut -d'|' -f1); chars=$(echo "$res"|cut -d'|' -f2); noimg=$(echo "$res"|cut -d'|' -f3)
if [ "$H2IMG" = "strict" ]; then
  [ -z "$noimg" ] && ok "全H2セクションに画像あり" || ng "画像が無いセクション: $noimg"
else
  [ -z "$noimg" ] && ok "全H2セクションに画像あり" || warn "画像が無いセクション: ${noimg}（${TYPE} は警告のみ）"
fi
[ "$viol" -eq 0 ] && ok "1文1段落 OK" || ng "1文1段落 違反 ${viol}箇所（。が2つの段落）"
[ "$chars" -ge "$MIN_CHARS" ] && ok "文字数 ${chars} (>=${MIN_CHARS})" || ng "文字数 ${chars} → ${MIN_CHARS}未満"

# 9. E-E-A-T 機械チェック（seo-eeat-check/check_eeat.py を統合）
#    案件/LP/188・#9110誘導/公的機関言及/②一次情報 などを判定。
#    errorがあれば exit 1 を返すので fail に合流する（warnは exit 0 で素通り）。
EEAT="skills/seo-eeat-check/check_eeat.py"
if [ -f "$EEAT" ]; then
  if python3 "$EEAT" "$F" >/tmp/ca_eeat.txt 2>&1; then
    ok "E-E-A-Tチェック（案件/LP/188誘導/公的機関/一次情報）"
    grep -E '⚠️' /tmp/ca_eeat.txt | sed 's/^/        /'
  else
    ng "E-E-A-T違反（下記・seo-eeat-check）"
    grep -E '❌|\[[0-9]+\]' /tmp/ca_eeat.txt | grep -v '件:' | sed 's/^/        /'
  fi
else
  warn "check_eeat.py が無いため E-E-A-T 機械チェックをスキップ"
fi

# 10. H2見出しゲート: 中心KW（商材名/会社名/人物名）の有無 ＋ サブ題パイプ｜の検出
#     ・タイトル由来の固有名トークンを中心KWとし、どのKWも含まないH2をWARN（運営H2など誤検知ありのため警告）
#     ・パイプ｜は「〜｜結論」「〜｜まとめ」を正規の型として許可。それ以外のサブ題｜だけFAIL。
res10=$(python3 - "$F" <<'PY'
import sys,re
from collections import Counter
t=open(sys.argv[1]).read()
m=re.search(r'^title:\s*"?(.+?)"?\s*$', t, re.M)
title=m.group(1) if m else ""
GENERIC=set("副業 投資 調査 検証 評判 口コミ 料金 費用 結論 実態 運営 会社 怪しい 詐欺 危険 注意 登録 本当 仕組 仕組み まとめ 収入 稼げる 稼ぐ 内訳 条件 返金 実績 無料 中身 流れ 相場 経歴 特商法 制度 高額 実際 案内 広告 情報 電話 番号 参加 保証 電子 書籍 理由 正体 手口 方法 完全 徹底 スクール セミナー ビジネス 資産 運用".split())
def toks(s):
    r=set()
    for x in re.findall(r'[ァ-ヴー]{3,}', s): r.add(x)
    for x in re.findall(r'[A-Za-z0-9\.]{2,}', s): r.add(x)
    for x in re.findall(r'[一-龠]{2,}', s):
        if x not in GENERIC: r.add(x)
    for x in re.findall(r'(?:株式会社|合同会社|一般社団法人|有限会社)[ぁ-んァ-ヴー一-龠A-Za-z0-9]+', s): r.add(x)
    return {x for x in r if len(x)>=2}
h2=re.findall(r'^##\s+(.+)$', t, re.M)
cand=toks(title)
freq=Counter()
for h in h2:
    for k in cand:
        if k in h: freq[k]+=1
if not freq and h2:
    hc=Counter()
    for h in h2:
        for k in toks(h): hc[k]+=1
    freq=Counter({k:v for k,v in hc.items() if v>=2})
core=[k for k,_ in freq.most_common(4) if freq[k]>=2]
nokw=[h for h in h2 if core and not any(k in h for k in core)] if core else []
def bad_pipe(h):
    if '｜' not in h: return False
    return h.split('｜')[-1].strip() not in ('結論','まとめ')
pipe=[h for h in h2 if bad_pipe(h)]
print("%d|%d|%s|%s|%s"%(len(nokw),len(pipe),",".join(core[:3]),"  /  ".join(nokw[:4]),"  /  ".join(pipe[:4])))
PY
)
nokw=$(echo "$res10"|cut -d'|' -f1); npipe=$(echo "$res10"|cut -d'|' -f2)
core=$(echo "$res10"|cut -d'|' -f3); nokwh=$(echo "$res10"|cut -d'|' -f4); pipeh=$(echo "$res10"|cut -d'|' -f5)
if [ "${npipe:-0}" -gt 0 ]; then ng "H2にサブ題パイプ｜ ${npipe}件（｜結論/｜まとめ以外は不可・KW入りの文に統合）: ${pipeh}"; else ok "H2パイプOK（｜結論/｜まとめのみ許可）"; fi
if [ "${nokw:-0}" -ge 1 ]; then warn "中心KW(${core})の無いH2が${nokw}件 → 各H2に商材名/会社名を入れる（運営H2など誤検知の場合あり・要目視）: ${nokwh}"; else ok "全H2に中心KWあり"; fi

# 11. つなぎの4点（読者に理解を任せない）— writing-agent「つなぎの4点」に対応
#     A 画像の直前が説明文でない（見出し/吹き出し/LINEボタン/画像の直後に画像を直置き）→ WARN
#       ※旧来の型（H2直後に画像）が全サイトに約2,250箇所あるため、既存リライトを止めないようWARN。
#         新記事は writing-agent の並び順（H2→結論→画像の説明→画像）に従うこと。
#     B LINE誘導の直前が画像/見出し（誘導文なし）→ FAIL
#       ただし最後のH2内の line_article_3 は、締めの吹き出し直後を正規配置として許可する。
#     C H2セクションの末尾が画像/表/箇条書き/引用（次章への橋渡し文なし）→ FAIL
#     D H2の直後にH3が直結（章の全体像を示す一文なし）→ FAIL
res11=$(python3 - "$F" <<'PY'
import sys,re
lines=open(sys.argv[1],encoding="utf-8").read().split('\n')
fm=0; ne=[]
for i,ln in enumerate(lines):
    s=ln.strip()
    if s=='---': fm+=1; continue
    if fm<2 or not s or s.startswith('import '): continue
    ne.append((i+1,s))
img =lambda s:s.startswith('![')
h2  =lambda s:s.startswith('## ')
h3  =lambda s:s.startswith('### ')
lb  =lambda s:s.startswith('<LineButton')
bal =lambda s:s.startswith('</Balloon')
cta_bal=lambda s:s.startswith('<Balloon') or s.startswith('</Balloon')
tbl =lambda s:s.startswith('|')
lst =lambda s:re.match(r'^[-*]\s',s) is not None
qte =lambda s:s.startswith('>')
A=[];B=[];C=[];D=[]
hi=[i for i,(_,s) in enumerate(ne) if h2(s)]
for i,(n,s) in enumerate(ne):
    p=ne[i-1][1] if i else ''
    final_balloon_cta = bool(
        lb(s)
        and ('id="line_article_3"' in s or "id='line_article_3'" in s)
        and cta_bal(p)
        and hi
        and i > hi[-1]
    )
    if img(s) and (h2(p) or h3(p) or bal(p) or lb(p) or img(p)): A.append(n)
    if lb(s) and not final_balloon_cta and (img(p) or h2(p) or h3(p) or lb(p) or cta_bal(p) or tbl(p) or lst(p) or qte(p)): B.append(n)
    if h3(s)  and h2(p): D.append(n)
for k,st in enumerate(hi):
    if k+1>=len(hi): break
    seg=ne[st+1:hi[k+1]]
    if not seg: continue
    n,last=seg[-1]
    if img(last) or tbl(last) or lst(last) or qte(last): C.append(n)
j=lambda v:",".join(map(str,v[:6]))
print("%d|%d|%d|%d|%s|%s|%s|%s"%(len(A),len(B),len(C),len(D),j(A),j(B),j(C),j(D)))
PY
)
nA=$(echo "$res11"|cut -d'|' -f1); nB=$(echo "$res11"|cut -d'|' -f2)
nC=$(echo "$res11"|cut -d'|' -f3); nD=$(echo "$res11"|cut -d'|' -f4)
lA=$(echo "$res11"|cut -d'|' -f5); lB=$(echo "$res11"|cut -d'|' -f6)
lC=$(echo "$res11"|cut -d'|' -f7); lD=$(echo "$res11"|cut -d'|' -f8)
if [ "${nA:-0}" -gt 0 ]; then warn "画像の直前に説明文がない ${nA}箇所（H2→結論→画像の説明→画像 の順にする）L:${lA}"; else ok "画像の直前に説明文あり"; fi
if [ "${nB:-0}" -gt 0 ]; then ng "LINE誘導の直前に誘導文がない ${nB}箇所（押すと何ができるかを1文書く）L:${lB}"; else ok "LINE誘導の直前に誘導文あり"; fi
if [ "${nC:-0}" -gt 0 ]; then ng "H2末尾が画像/表/箇条書き/引用で途切れている ${nC}箇所（次章への橋渡し文を足す）L:${lC}"; else ok "全H2に次章への橋渡し文あり"; fi
if [ "${nD:-0}" -gt 0 ]; then ng "H2の直後にH3が直結 ${nD}箇所（間に章の全体像を示す一文を入れる）L:${lD}"; else ok "H2→H3の間に導入文あり"; fi

# 12. LINE CV ゲート（skills/scripts/check-line-cv.sh を統合。CVを下げる書き方を弾く）
CVGATE="skills/scripts/check-line-cv.sh"
if [ -f "$CVGATE" ]; then
  if bash "$CVGATE" "$F" >/tmp/ca_cv.txt 2>&1; then
    ok "LINE CVチェック（催促NG/審判者/自己弁護・line-cvr スキル）"
    grep -E '⚠️' /tmp/ca_cv.txt | sed 's/^/        /'
  else
    ng "LINE CV違反（下記・skills/line-cvr/SKILL.md）"
    grep -E '❌' /tmp/ca_cv.txt | sed 's/^/        /'
  fi
else
  warn "check-line-cv.sh が無いため LINE CV チェックをスキップ"
fi

# 13. AI臭ゲート（skills/scripts/check-ai-slop.sh を統合。脱人間味の書き方を弾く）
AIGATE="skills/scripts/check-ai-slop.sh"
if [ -f "$AIGATE" ]; then
  if bash "$AIGATE" "$F" >/tmp/ca_ai.txt 2>&1; then
    ok "AI臭チェック（採点ラベル/もったいぶり/誇張・human-voice.md）"
    grep -E '⚠️' /tmp/ca_ai.txt | sed 's/^/        /'
  else
    ng "AI臭違反（下記・writing-agent/references/human-voice.md）"
    grep -E '❌' /tmp/ca_ai.txt | sed 's/^/        /'
  fi
else
  warn "check-ai-slop.sh が無いため AI臭チェックをスキップ"
fi

# 14. 表の数（料金・返金条件・確認項目を表で整理しているか）
#     字数だけ増やすと水増しになる。競合は6〜7個の表で条件を整理していた。
tbl=$(python3 - "$F" <<'PY'
import sys,re
fm=0;n=0
for ln in open(sys.argv[1],encoding="utf-8"):
    s=ln.strip()
    if s=='---': fm+=1; continue
    if fm<2: continue
    # 区切り行（|---|---|）の数＝表の数
    if re.match(r'^\|[\s:\-|]+\|$', s) and '-' in s: n+=1
print(n)
PY
)
if [ "$MIN_TBL" -gt 0 ]; then
  [ "${tbl:-0}" -ge "$MIN_TBL" ] && ok "表 ${tbl}個 (>=${MIN_TBL})" || ng "表 ${tbl}個 → ${MIN_TBL}個未満（料金/返金条件/確認項目を表で整理する）"
fi

# 15. H3の数（H2の半分以上）。H2だけで並べると1本の記事で拾える検索意図が狭い。
#     競合の2位記事は H2 10本に対し H3 14本。うちは H3 0本だった。
res15=$(python3 - "$F" <<'PY'
import sys,re
fm=0;h2=0;h3=0
for ln in open(sys.argv[1],encoding="utf-8"):
    s=ln.rstrip()
    if s.strip()=='---': fm+=1; continue
    if fm<2: continue
    if s.startswith('### '): h3+=1
    elif s.startswith('## '): h2+=1
print("%d|%d|%d"%(h2,h3,-(-h2//2)))
PY
)
n2=$(echo "$res15"|cut -d'|' -f1); n3=$(echo "$res15"|cut -d'|' -f2); need3=$(echo "$res15"|cut -d'|' -f3)
if [ "$H3MODE" != "off" ]; then
  if [ "${n3:-0}" -ge "${need3:-0}" ]; then
    ok "H3 ${n3}本 (H2 ${n2}本の半分 ${need3} 以上)"
  elif [ "$H3MODE" = "strict" ]; then
    ng "H3 ${n3}本 → H2 ${n2}本に対して${need3}本未満（各H2をH3で分解して拾える検索意図を広げる）"
  else
    warn "H3 ${n3}本 → H2 ${n2}本に対して${need3}本未満（${TYPE} は警告のみ）"
  fi
fi

# 16. 公的機関リンクの深さと本数（トップページに貼るだけでは裏取りにならない）
#     競合は caa.go.jp/notice/entry/042732/ のような該当ページへ直リンクし、最大6本入れていた。
res16=$(python3 - "$F" <<'PY'
import sys,re
t=open(sys.argv[1],encoding="utf-8").read()
deep=set(); bad=[]
for u in re.findall(r'https?://[^\s"<>)]+', t):
    host=re.sub(r'^https?://','',u).split('/')[0]
    if not (host.endswith('.go.jp') or host.endswith('.lg.jp')): continue
    path=[p for p in u.split(host,1)[1].split('?')[0].split('#')[0].split('/') if p]
    if len(path) >= 2: deep.add(u.split('#')[0])
    else: bad.append(u)
print("%d|%s"%(len(deep), "|".join(bad[:5])))
PY
)
ndeep=$(echo "$res16"|cut -d'|' -f1); shallow=$(echo "$res16"|cut -d'|' -f2-)
if [ "$MIN_GOV" -gt 0 ]; then
  [ "${ndeep:-0}" -ge "$MIN_GOV" ] && ok "公的機関の該当ページリンク ${ndeep}本 (>=${MIN_GOV})" \
    || ng "公的機関の該当ページリンク ${ndeep}本 → ${MIN_GOV}本未満（注意喚起・条文・法人番号などの該当ページまで貼る）"
fi
[ -n "$shallow" ] && warn "公的機関リンクが浅い（該当ページまで貼る）: ${shallow}" || ok "公的機関リンクは全て該当ページ指定"

# 17. 疑問形で終わるH2（見出しの時点で答えを言い切る）
#     競合は全記事で疑問形H2ゼロ。ただし「〇〇は詐欺？」はKWとしても機能するためWARN止まりにする。
q=$(grep -cE '^## .*[？?]\s*$' "$F" || true)
[ "${q:-0}" -eq 0 ] && ok "H2は全て言い切り" || warn "疑問形で終わるH2 ${q}件（見出しだけ拾い読みしても結論が伝わる形にする・KW狙いなら可）"

# 18. タイトルゲート（writing-agent「タイトルのルール」に対応）
#     基準の出どころ: Google のタイトルリンクは PC 全角30字前後 / モバイル40字前後で省略され、
#     単語の途中では切れない（＝末尾の重要KWは丸ごと消える）。実測335本（fbss206/nhk-no112/
#     fukugyo-hotline16）の中央値は30〜31字、36字以上は22本、最長47字。
#     → 41字以上はモバイルでも切れるので FAIL。36〜40字は PC で切れるので WARN。
#     ・メインKW（商材名・会社名などの固有名）は先頭20字以内（それ以降は WARN）
#     ・同じ単語の2回使いは検索評価が上がらない（同じ文字数なら別の訴求軸に充てる）
#     ・金額はタイトルに入れない／全角｜のサブ題は使わない（サイト名は BaseLayout が半角 | で連結）
res18=$(python3 - "$F" <<'PY'
import sys,re
t=open(sys.argv[1]).read()
m=re.search(r'^title:\s*"?(.+?)"?\s*$', t, re.M)
title=(m.group(1) if m else "").strip()
GENERIC=set("副業 投資 調査 検証 評判 口コミ 料金 費用 結論 実態 運営 会社 怪しい 詐欺 危険 注意 登録 本当 仕組 仕組み まとめ 収入 稼げる 稼ぐ 内訳 条件 返金 実績 無料 中身 流れ 相場 経歴 特商法 制度 高額 実際 案内 広告 情報 電話 番号 参加 保証 電子 書籍 理由 正体 手口 方法 完全 徹底 スクール セミナー ビジネス 資産 運用 儲かる 解説 安全 退会 解約 被害 大丈夫".split())
def toks(s):
    r=set()
    for x in re.findall(r'[ァ-ヴー]{3,}', s): r.add(x)
    for x in re.findall(r'[A-Za-z][A-Za-z0-9\.]{1,}', s): r.add(x)
    for x in re.findall(r'[一-龠]{2,}', s):
        if x not in GENERIC: r.add(x)
    for x in re.findall(r'(?:株式会社|合同会社|一般社団法人|有限会社)[ぁ-んァ-ヴー一-龠A-Za-z0-9]+', s): r.add(x)
    return {x for x in r if len(x)>=2 and x not in GENERIC}
cand=toks(title)
pos=min([title.find(k) for k in cand], default=-1)
dup=sorted({k for k in cand if title.count(k)>=2})
money=re.findall(r'[0-9０-９][0-9０-９,，.．]*\s*(?:円|万円|億円)', title)
pipe=1 if '｜' in title else 0
print("%d|%d|%s|%s|%d"%(len(title), pos, ",".join(dup[:3]), ",".join(money[:3]), pipe))
PY
)
tlen=$(echo "$res18"|cut -d'|' -f1); tpos=$(echo "$res18"|cut -d'|' -f2)
tdup=$(echo "$res18"|cut -d'|' -f3); tmoney=$(echo "$res18"|cut -d'|' -f4); tpipe=$(echo "$res18"|cut -d'|' -f5)
if [ "${tlen:-0}" -ge 41 ]; then
  ng "タイトル ${tlen}字（モバイル40字前後でも切れる）→ 32字を原則に詰める。末尾は「調査」等の消えても困らない語で締める"
elif [ "${tlen:-0}" -ge 36 ]; then
  warn "タイトル ${tlen}字（PCは30字前後で省略・原則32字以内）。重要KWが末尾に無いか確認する"
else
  ok "タイトル ${tlen}字（原則32字以内）"
fi
if [ "${tpos:-0}" -lt 0 ]; then
  warn "タイトルに商材名・会社名などの固有名が見当たらない（メインKWを先頭に置く）"
elif [ "${tpos:-0}" -gt 20 ]; then
  warn "メインKWがタイトルの${tpos}文字目（先頭20字以内に置く。先頭に近いほど検索評価も視認性も高い）"
else
  ok "メインKWは先頭${tpos}文字目（20字以内）"
fi
[ -n "$tdup" ] && warn "タイトルで同じ単語を2回使用（${tdup}）。繰り返しても評価は上がらない。同じ文字数を別の訴求軸か読者を絞り込むKWに充てる（※会社名が商材名を含む「AIスキルアカデミー／株式会社AIスキル」のように避けられない場合は無視可）" || ok "タイトルの同一単語の重複なし"
[ -n "$tmoney" ] && warn "タイトルに具体的な金額（${tmoney}）。料金は記事内で出す（「料金は？」と問いで示すのは可）" || ok "タイトルに金額なし"
[ "${tpipe:-0}" -eq 0 ] && ok "タイトルにサブ題｜なし" || warn "タイトルに全角｜（BaseLayoutが半角 | でサイト名を連結するため区切りが2種類並ぶ）"

# 結論セクションに理由・根拠を書いていないか（FAIL）
#   出典: 2026-08-28 管理人さん。「結論は、結論と、その後の記事を読みたくなるように書く場所、
#   あとライン誘導。それ以外はごちゃごちゃ書かなくていい」。
#   同日に4回直させた末、H3「〇〇をおすすめしない3つの理由」が別記事に残っていた。
#   H3を立てると目次にも載り、「結論＝理由の解説をする場所」という構造を宣言してしまう。
#   3つの理由は全部あとの章の主役なので、先に見せるとその章を読む理由が消える。
concl=$(python3 - "$F" <<'PY2'
import sys, re
fm=0; inc=False; bad=[]
for ln in open(sys.argv[1], encoding="utf-8"):
    s=ln.rstrip("\n")
    if s.strip()=='---': fm+=1; continue
    if fm<2: continue
    if s.startswith('## '):
        inc = ('結論' in s); continue
    if not inc: continue
    if s.startswith('### '):
        bad.append("H3: "+s[4:40])
    elif re.search(r'(理由|根拠|ポイント|注意点)は[0-9０-９一二三四五六七八九]+つ', s):
        bad.append("列挙: "+s[:40])
print("\n".join(bad))
PY2
)
if [ -n "$concl" ]; then
  ng "結論セクションに理由の解説（結論／読みたくなる一言／LINE誘導の3つだけにする。理由は後ろの章の主役）"
  echo "$concl" | sed 's/^/        /' | head -5
else
  ok "結論セクションに理由の解説なし"
fi

echo "----------------------------------------"
if [ "$fail" -eq 0 ]; then echo "✅ 全チェック通過。納品OK。"; else echo "❌ 違反あり。修正するまで納品しないこと。"; fi
exit $fail
