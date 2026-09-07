// カスタムルール: 同じ語尾の連続を検出
// 1) 段落内: 「〜しょう。〜しょう。」等、特定語尾の2文連続はNG（です。ます。はここでは対象外＝従来どおり）
// 2) 段落をまたいだ「です。」「ます。」系（でした/ました/ています等の助動詞まで含む広いくくり）が
//    3段落以上連続するのもNG（2026-07-31追加）。
//    「1つの<p>に1文」で書く運用だと、段落内チェックだけでは複数文にまたがる語尾の単調さを
//    検出できない（textlintが常に✅でも実際は「〜です。〜です。〜です。」の反復が起きていた）。
//    詳細: memory「textlint-ending-check-is-per-paragraph-blind-spot」

const ENDINGS_TO_CHECK = [
  "しょう。",
  "しょう！",
  "ください。",
  "ください！",
  "しません。",
  "しません！",
  "ですよね。",
  "ですよね！",
  "いきます。",
  "いきますね。",
  "伝えていきますね。"
];

// 広いくくり（段落またぎチェック用）。長い語尾を先に判定する（「でした。」を「です。」より先に見る等）。
const BROAD_CLASSES = [
  "ではありません。", "ません。",
  "でしょう。", "ましょう。",
  "ました。", "でした。",
  "ください。",
  "です。", "ます。"
];

function classifyBroad(sentence) {
  for (const cls of BROAD_CLASSES) {
    if (sentence.endsWith(cls)) return cls;
  }
  return null;
}

function lastSentence(text) {
  const sentences = text.split(/(?<=[。！？])/).map((s) => s.trim()).filter(Boolean);
  return sentences.length ? sentences[sentences.length - 1] : null;
}

function reporter(context) {
  const { Syntax, RuleError, report, getSource } = context;
  const paragraphEndings = [];

  return {
    [Syntax.Paragraph](node) {
      const text = getSource(node);
      if (!text) return;

      // Split by sentences
      const sentences = text.split(/(?<=[。！？])/);

      let prevEnding = null;
      for (const sentence of sentences) {
        const trimmed = sentence.trim();
        if (!trimmed) continue;

        let currentEnding = null;
        for (const ending of ENDINGS_TO_CHECK) {
          if (trimmed.endsWith(ending)) {
            currentEnding = ending;
            break;
          }
        }

        if (currentEnding && currentEnding === prevEnding) {
          const index = text.indexOf(trimmed);
          report(
            node,
            new RuleError(
              `「${currentEnding.replace(/[。！？]$/, '')}」が2文連続しています。語尾を変えてください。`,
              { index }
            )
          );
        }

        prevEnding = currentEnding;
      }

      // 段落またぎチェック用に、この段落の最後の文の広いくくりを記録する。
      // 吹き出し(<Balloon>)等のJSX子要素も個別のParagraphとして拾われるため、
      // 判定対象は素の文章段落だけに絞りたいが、textlintのAST上で厳密な区別は難しいので
      // ここでは全Paragraphを対象にする（誤検知が出たら都度この段落の文言を直せばよく、
      // ルール自体を複雑にしすぎない）。
      const last = lastSentence(text);
      const cls = last ? classifyBroad(last) : null;
      paragraphEndings.push({ node, cls });
    },
    [`${Syntax.Document}:exit`]() {
      let streak = 1;
      for (let i = 1; i < paragraphEndings.length; i++) {
        const cur = paragraphEndings[i];
        const prev = paragraphEndings[i - 1];
        if (cur.cls && cur.cls === prev.cls) {
          streak++;
          if (streak === 3) {
            report(
              cur.node,
              new RuleError(
                `「${cur.cls.replace(/[。！？]$/, '')}」で終わる段落が3つ以上連続しています。語尾（でしょう/ました/ません/ましょう等）を混ぜてください。`,
                { index: 0 }
              )
            );
          }
        } else {
          streak = 1;
        }
      }
    }
  };
}

module.exports = {
  linter: reporter,
  fixer: undefined
};
