#!/usr/bin/env bash
# check-ai-slop.sh — AI臭・脱人間味の書き方を機械判定する「見張り」。
# check-line-cv.sh(CV) の口調版。human-voice.md の"やらないこと"を機械化。
# 判定パターンは管理人さんの実戦フィードバック由来＝誤検知を最小化。
#   FAIL(弾く): 採点ラベル / もったいぶり・出し惜しみ繋ぎ / AI定番の誇張  ← 高精度・0許容
#   WARN(目視): 長すぎる段落(モバイル折返し過多) / 「ではないでしょうか」多用
# 使い方: bash scripts/check-ai-slop.sh src/content/articles/<slug>.mdx
set -uo pipefail
F="${1:-}"
[ -n "$F" ] && [ -f "$F" ] || { echo "使い方: bash scripts/check-ai-slop.sh <記事.mdx>"; exit 1; }

fail=0
ok(){   echo "  ✅ $1"; }
ng(){   echo "  ❌ $1"; fail=1; }
warn(){ echo "  ⚠️ $1"; }

echo "=== AI臭チェック: ${F} ==="

# 1. 読者を採点するラベル（FAIL・0許容）
#    出典: 本セッション「〜して正解です＝気取ったラベル貼り」。行動を採点しない。
GRADE='して正解です|て正解でした|できて偉い|のは偉い|のは正解です|えらいです'
hits=$(grep -nE "$GRADE" "$F" || true)
if [ -n "$hits" ]; then
  ng "読者を採点するラベル（「〜して正解」等・気取り。次の行動だけ言う）"
  echo "$hits" | sed 's/^/        /' | head
else
  ok "採点ラベルなし"
fi

# 2. もったいぶり前置き・出し惜しみ繋ぎ（FAIL・0許容）
#    出典: human-voice.md「出し惜しみ繋ぎ禁止」/ voice-is-sales-talk「もったいぶり前置き」
#    2026-08-28 追記: 記事の構成を宣言する型も同じ（管理人さん「一緒に確認していきましょう、なら
#    分かるけど『料金の章でそのまま出します』←こんなん書くなよ」）。目次の説明は営業の言葉ではない。
#    ⭕「順番に見ていきましょう」 ❌「〜の章で出します」❌「順番に並べます」
#    ⚠️「あとで一緒に確認しましょう」も同じ（管理人さん「あとでってなに？もう書けんなら書くな
#    こんな文章」）。伏せるのは黙って伏せる。「あとで書きます」という宣言自体が中身ゼロの1文。
TEASE='本当に大事なのは|いちばん大事なのは|一番大事なのは|一番重かったのは|いちばん重かったのは|問題は、その先|実は、ここからが|さらに、いちばん|ここからが本題|理由はひとつ|理由は1つ|理由は一つ|答えはひとつ|結論はひとつ|大事なことはひとつ|した流れです|した流れをお伝えし|確かめた流れです|まとめていきます|解説していきます|いよいよ本題|いよいよ、本題|ここが本題|の章で(出|見|触|扱)|後の章で|あとの章で|次の章で|後述しま|順番に並べます|そのまま出します|先にまとめます|整理します。|お伝えしていきます|(あとで|後で|のちほど|後ほど)[^。]{0,12}(確認しましょう|見ていきましょう|出します|触れます|説明します|お伝えします)'
hits=$(grep -nE "$TEASE" "$F" || true)
if [ -n "$hits" ]; then
  ng "もったいぶり・空予告・私主役の実況（タメず・自分の作業実況をやめ、その場で中身/結果を読者に渡す）"
  echo "$hits" | sed 's/^/        /' | head
else
  ok "もったいぶりなし"
fi

# 3. AI定番の誇張・大げさな断定（FAIL・0許容）
BIG='と言っても過言では|と言えるでしょう[^か]|に他なりません|ではないでしょうか。.*ではないでしょうか'
hits=$(grep -nE "$BIG" "$F" || true)
if [ -n "$hits" ]; then
  ng "AI定番の誇張（「過言ではない」「他なりません」等・素直に言い切る）"
  echo "$hits" | sed 's/^/        /' | head
else
  ok "AI定番の誇張なし"
fi

# 3b. 書き手の作業実況（FAIL・0許容）
#    出典: 2026-07-28 teria/cocotalk。「自分でたどって確かめた/そのまま進めて確かめた」＝作業の実況。
#    主語は読者・渡すのは結果。※「実際に自分で登録して確かめる」等はヤマトの検証スタンス＝正当なので除外。
#    ※「調べました/確かめました」宣言では権威は出ない(具体と社会的証明から)＝これは目視/criticで。
#    2026-08-11 追記: 管理人さんから「自分語りやめろ」と再度の指摘。冒頭で全部踏んだので機械化する。
#      ・調べ方の宣言（登録して確認しています／確かめました／調べました）
#      ・空予告（〜まで書きました／まとめています／見ていきます／紹介します）
#      ・自己弁護の言い訳（否定したいわけではないので）
#      ※「実際に登録して調査を行っています」等ペルソナ定型は除外パターンで逃がす
NARRATE='自分でたどっ|そのまま.{0,4}進めて確かめ|進めて確かめました|たどって確かめ|たどってみま'
NARRATE="$NARRATE"'|画面を(全部|すべて)?確認しています|登録して確かめました|登録して確認しています'
NARRATE="$NARRATE"'|まで書きました|までまとめています|までまとめました|そのまま紹介します'
NARRATE="$NARRATE"'|見ていきます|見ておきます|確かめていきます'
NARRATE="$NARRATE"'|私が(実際に)?[^。]{0,14}(確かめた|確認した|調べた)、'
NARRATE="$NARRATE"'|わけではないので'
hits=$(grep -nE "$NARRATE" "$F" || true)
if [ -n "$hits" ]; then
  ng "書き手の作業実況（自分でたどって/そのまま進めて確かめ＝作業でなく結果を渡す）"
  echo "$hits" | sed 's/^/        /' | head
else
  ok "作業実況なし"
fi

# 3e. 主語のない指示語始まりの文（FAIL・0許容）
#    出典: 2026-08-06/08-28 管理人さん指摘。「ここが〜」「それを〜」で始めて主語を落とすと
#    読者は前の行を読み返すことになる。副業ホットラインの check_voice.py にしか無かったので共通化。
#    ※「どちらの方も」等はクロージングで直前に2つの立場を並べたあとの受けなので除外
demo=$(python3 - "$F" <<'PY2'
import sys, re
fm=0; inbal=False; hits=[]
for ln in open(sys.argv[1], encoding="utf-8"):
    s=ln.strip()
    if s=='---': fm+=1; continue
    if fm<2: continue
    if s.startswith('<Balloon'): inbal=True
    if s.startswith('</Balloon'): inbal=False; continue
    if inbal: continue
    s=re.sub(r'<[^>]+>','',s).strip()
    if not s or s.startswith(('|','!','#','-','>','import','※')): continue
    if re.match(r'^どちら(の方も|も|の記事も)', s): continue
    if re.match(r'^(ここ|これ|そこ|それ|どちら|どっち|そちら)[がはをのに]', s):
        hits.append(s[:34])
print("\n".join(hits))
PY2
)
if [ -n "$demo" ]; then
  ng "主語のない指示語始まりの文（何の話か伝わらない。主語を置く）"
  echo "$demo" | sed 's/^/        /' | head
else
  ok "主語のない指示語始まりの文なし"
fi

# 3i. 登録検証より前で、登録後にしか分からない事実を使っている（FAIL）
#    出典: 2026-08-28 管理人さん。「これを登録検証のセクションの前に持ってくる意味がわからん。
#    時系列がおかしい。ユーザーも『何の話？』ってなるから。何回も言ってきたことだけど」。
#    「〇〇とは？」の節に、登録して届いた教材の中身を書いていた。読者はまだ登録の話を
#    聞いていないので、そこだけ話が飛ぶ。
#    ⚠️ 原因＝直前の指摘を潰すために、手元にある一番強い事実をその場に貼っただけで、
#    そのセクションが記事の何番目かを見ていない。1箇所を直すときほど全体の順番を見る。
jump=$(python3 - "$F" <<'PY2'
import sys, re
lines=[l.rstrip("\n") for l in open(sys.argv[1], encoding="utf-8")]
# 登録・インストール検証のH2を探す
start=None
for i,l in enumerate(lines):
    if l.startswith('## ') and re.search(r'(登録すると|登録したら|インストール|申し込むと|友だち追加すると|登録して)', l):
        start=i; break
if start is None: sys.exit(0)
# 登録後にしか分からない事実を指す語（CTAの立場並記は除く）
KEY=r'(登録して届|届いた(教材|メッセージ|会員証|資料)|配られる教材|教材の[0-9０-９]|会員証|PDFの本|アプリの中のチャット|規約の特約|申し込みページには)'
# 冒頭と結論は「読みたくなる一言」で先を匂わせてよいので対象外
begin=0
for i,l in enumerate(lines):
    if l.startswith('## ') and '結論' not in l: begin=i; break
fm=2; hits=[]
for i,l in enumerate(lines[begin:start], begin+1):
    t=l.strip()
    if t=='---': fm+=1; continue
    if fm<2 or not t or t[0] in '|!#>-': continue
    c=re.sub(r'<[^>]+>','',t)
    if re.search(r'(方も|ください|送って|聞いて|相談)', c): continue   # CTA
    if re.search(KEY, c): hits.append("L%d %s"%(i,c[:40]))
print("\n".join(hits))
PY2
)
if [ -n "$jump" ]; then
  ng "登録検証より前で、登録後にしか分からない事実を使っている（時系列が飛ぶ）"
  echo "$jump" | sed 's/^/        /' | head -5
else
  ok "登録後の事実を先取りしていない"
fi

# 3j. 読者に通じない技術語・回りくどい言い方（FAIL）
#    出典: 2026-08-28 管理人さん。「このPDFは広告と同じドメインに置かれていて、中を最後まで
#    開きました」を見て「ユーザーに難しすぎるから ドメインとか。中を最後まで開きましたも
#    意味わからんし。実際に見てみましたで通じる。回りくどい言い方して文字数稼ぐな」。
#    ⚠️ 引用（「」やblockquote）と画像のalt、リンクのアンカーテキストは対象外。
tech=$(python3 - "$F" <<'PY2'
import sys, re
NG = {
 'ドメイン':'「広告と同じ会社が置いている」等、事実で言い換える',
 'サーバー':'「ページ」「置いてある場所」',
 'URL':'「ページのアドレス」',
 'ASP':'「広告を配っている会社」',
 'フッター':'「ページの一番下」',
 'ステータスメッセージ':'「名前の下に出る一言」',
 'リダイレクト':'「別のページに飛ばされる」',
 'プロトコル':'書かない',
 'クローラ':'書かない',
 'インデックス':'書かない',
}
ROUND = {
 '中を最後まで開きました':'「実際に見てみました」',
 '最後まで目を通しました':'「実際に見てみました」',
 '確認を行いました':'「確かめました」',
 '実施しました':'「やりました」',
 'という位置づけです':'言い切る',
 'ことがうかがえます':'言い切る',
 'と言えるでしょう':'言い切る',
}
fm=0; inq=False; hits=[]
for ln in open(sys.argv[1], encoding="utf-8"):
    t=ln.rstrip("\n"); st=t.strip()
    if st=='---': fm+=1; continue
    if fm<2: continue
    if st.startswith('<SourceQuote'): inq=True
    if st.startswith('</SourceQuote'): inq=False; continue
    if inq: continue
    if not st or st[0] in '!>#': continue          # 画像alt・引用・見出しは除外
    c=re.sub(r'<a [^>]*>.*?</a>','',t)             # リンクのアンカーテキストを除外
    c=re.sub(r'<[^>]+>','',c)
    c=re.sub(r'「[^」]*」','',c)                   # 引用部分を除外
    for w,fix in list(NG.items())+list(ROUND.items()):
        if w in c: hits.append(f"{w} → {fix}  :: {st[:34]}")
print("\n".join(hits))
PY2
)
if [ -n "$tech" ]; then
  warn "読者に通じない技術語・回りくどい言い方（読者の言葉に直す。文字数稼ぎになっている）※清掃済みサイトはFAILに上げる"
  echo "$tech" | sed 's/^/        /' | head -6
else
  ok "技術語・回りくどい言い方なし"
fi

# 3g. LPの位置・体裁を説明するだけの文（FAIL）
#    出典: 2026-08-28 管理人さん。
#    「説明ページには、配られるまでの流れが3段階で書いてあります」を見て
#    「これってLPの説明なんよね。違うんよ。LPの説明するってより、こう書いてありますけど、
#     怪しいですよね、的な。LPをユーザーと一緒に叩く感じだから」。
#    CLAUDE.md の「LP・広告の文言を引用してからツッコむ」を、要約から入る形で破っていた。
#    読者はLPを理解しに来ていない。怪しいかどうかを知りに来ている。
#    → 引用（「」か具体的な数字）を含まないまま、LPのどこに何が載っているかだけを言う文を弾く。
lpdesc=$(python3 - "$F" <<'PY2'
import sys, re
LOC = r'(ページ|画面|広告|説明ページ|フッター|注記|目次|教材|規約|プロフィール|申し込み)'
POS = r'(の(上|下|中ほど|最後|冒頭|すぐ下|一番下|下のほう|上のほう|中))?'
lines=[l.rstrip("\n") for l in open(sys.argv[1], encoding="utf-8")]
fm=0; inbal=False; body=[]
for i,ln in enumerate(lines):
    t=ln.strip()
    if t=='---': fm+=1; continue
    if fm<2: continue
    if t.startswith('<Balloon'): inbal=True
    if t.startswith('</Balloon'): inbal=False; continue
    if inbal: continue
    body.append(t)
hits=[]
for i,t in enumerate(body):
    s=re.sub(r'<[^>]+>','',t).strip()
    if not s or t.startswith(('|','!','#','-','>','import','※')): continue
    if '「' in s: continue                                  # 自分で引用している
    if re.search(r'(国税庁|消費者庁|国民生活センター|警察庁|金融庁|法務局|独立行政法人)', s): continue  # 公的資料の引用
    if re.search(r'(ていません|ていない|ありません|見当たら|出てきません|残っていません)', s): continue  # 否定＝発見
    # 直後3つの中身行に引用（blockquote か 「」）が来るなら、引用の導入文なのでOK
    nxt=[x for x in body[i+1:i+5] if x][:3]
    if any(x.startswith('>') or '「' in x for x in nxt): continue
    if re.search(LOC+POS+r'(には|に(は)?、)', s) and re.search(r'(書いて|書かれて|載って|並んで|入って|置いて|出て)', s):
        hits.append(s[:38])
    elif re.search(r'(形になっています|順番に説明する|構成になっています)', s):
        hits.append(s[:38])
print("\n".join(hits))
PY2
)
if [ -n "$lpdesc" ]; then
  warn "LPの位置・体裁を説明するだけの文（引用してすぐ叩く。読者はLPの構成を知りたくない）※清掃済みサイトはFAILに上げる"
  echo "$lpdesc" | sed 's/^/        /' | head -5
else
  ok "LPの位置・体裁だけを説明する文なし"
fi

# 3h. 「見ての通り」型のメタ文（FAIL）
#    出典: 2026-08-28 管理人さん「見ての通り、上には〜と出ています。こう言うのもやめて」。
#    画像を見れば分かることを文で言い直しているだけ。どのゲートも拾っていなかった。
mita=$(grep -nE "見ての通り|ご覧の通り|お分かりのように|上記のとおり" "$F" | grep -v '^[0-9]*:>' || true)
if [ -n "$mita" ]; then
  warn "「見ての通り」型のメタ文（画像を見れば分かることを言い直している）※清掃済みサイトはFAILに上げる"
  echo "$mita" | sed 's/^/        /' | head -5
else
  ok "「見ての通り」型のメタ文なし"
fi

# 3f. ぼかし（WARN・目視）
#    出典: 2026-08-28。オチを隠そうとして具体名詞を全部消すと意味が通らなくなる。
#    「渡されるもの」「それを自分で認めています」等。具体があるから先が気になる。
VAGUE2='渡されるもの|届くもの|渡されるものが|それを自分で|そのことを自分で|それが分かります|それを認め'
hits=$(grep -nE "$VAGUE2" "$F" || true)
if [ -n "$hits" ]; then
  warn "ぼかしの疑い（具体名詞を消していないか・「渡されるもの」→「84ページの教材」）"
  echo "$hits" | sed 's/^/        /' | head -5
fi

# 3d. 思わせぶり（FAIL・0許容）
#    出典: line-cvr「書いた瞬間に消す7つのAI癖」② 何に間に合う？何が残っている？が無い文。
VAGUE='まだ間に合います|まだ間に合う|できることは残って|できることが残って|打てる手は残って'
hits=$(grep -nE "$VAGUE" "$F" || true)
if [ -n "$hits" ]; then
  ng "思わせぶり（"間に合う/できることが残っている"＝何が？を具体に。例: カード払いなら支払いを止められる）"
  echo "$hits" | sed 's/^/        /' | head
else
  ok "思わせぶりなし"
fi

# 3c. 観察トーン・藁人形対比・絵に描けない抽象・思わせぶり（WARN・目視）
#    出典: 2026-07-28。外から眺める「言葉が並びます」/ 誰も言ってない対比「問題はAではなく」/ 抽象「見通しの悪い」/ タメ「その先に待って」
OBS='言葉が並びます|言葉が並んでい|問題は[^。]{0,18}ではなく|見通しの悪い|その先に待って|その先で待って'
hits=$(grep -nE "$OBS" "$F" || true)
if [ -n "$hits" ]; then
  warn "観察トーン/藁人形/抽象の可能性（言葉が並ぶ・問題はAではなく・見通しの悪い→具体で・目視）"
  echo "$hits" | sed 's/^/        /' | head
fi

# 4. 長すぎる段落＝モバイル折返し過多（WARN・目視）
#    出典: gate-misses-mobile-lines-and-ai-phrases。本文の1段落が長いとAI臭＋読まれない。
#    吹き出し・引用・見出し・frontmatter・HTML行は除外。目安60字以上をカウント。
long=$(python3 - "$F" <<'PY'
import sys,re
lines=open(sys.argv[1]).read().split('\n'); fm=0; inbal=False; n=0
for ln in lines:
    s=ln.strip()
    if s=='---': fm+=1; continue
    if fm<2: continue
    if s.startswith('<Balloon'): inbal=True; continue
    if s.startswith('</Balloon'): inbal=False; continue
    if inbal or not s: continue
    if s.startswith(('>','|','#','<','!','-','import','```')): continue
    body=re.sub(r'<[^>]+>','',s)
    if len(body)>=60: n+=1
print(n)
PY
)
if [ "${long:-0}" -eq 0 ]; then ok "長すぎる段落なし"; else warn "長すぎる段落 ${long}箇所（60字≥・モバイルで折返し過多→「、」で分割・短く）"; fi

echo "----------------------------------------"
if [ "$fail" -eq 0 ]; then echo "✅ AI臭チェック通過。"; else echo "❌ AI臭あり（FAIL）。直すまで納品しないこと。"; fi
exit $fail
