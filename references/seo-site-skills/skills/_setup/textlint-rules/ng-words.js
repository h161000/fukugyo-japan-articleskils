// カスタムルール: NGワード検出
// CLAUDE.mdとSKILL.mdのルールに基づく

const NG_WORDS = [
  // 法的リスク系（絶対禁止）
  // 「逮捕」は打ち消し・引用・疑問の文脈のみ許可。断定（「〇〇は逮捕された」と言い切る）は引き続き禁止。
  // 禁止の趣旨は「こちらが“逮捕された”と断定して名誉毀損になること」を防ぐ点にあるため、
  //   ・容疑/警察発表を伴う事実報道の引用
  //   ・「逮捕されていない」「逮捕された事実はない」等の打ち消し（なりすまし被害者の保護）
  //   ・「逮捕はデマ」「なりすまし」「噂」等でデマと明示する文脈
  //   ・「…逮捕…」の引用（デマ文言そのものの引用）
  //   ・「…逮捕…本当か」等の疑問形
  // は趣旨に反しないため許可する（違法ワードの否定形許可と同じ考え方）。
  { word: "逮捕", severity: "error", message: "法的リスクのあるワードです（断定は禁止。「逮捕されていない」「逮捕はデマ」等の打ち消し・引用・疑問、または容疑/警察発表の事実報道のみ可）", allowIf: /容疑|府警|警察|デマ|事実ではあ|事実ではな|事実はな|逮捕され(てい)?(ま?せん|ない|なく)|逮捕された事実(は|も)?(なく|ない|ありませ|は無)|本当か|本当[?？]|「[^」]*逮捕[^」]*」/ },
  // 「犯罪」は警察用語「匿名・流動型犯罪グループ」の引用のみ許可
  { word: "犯罪", severity: "error", message: "法的リスクのあるワードです", allowIf: /匿名・流動型犯罪グループ/ },
  // 「違法」は否定形・疑問形のみ許可（例:「違法ではありません」「〜は違法？」）。
  // 禁止の趣旨は「こちらが“違法だ”と断定して名誉毀損になること」を防ぐ点にあるため、
  // 打ち消す用法は趣旨に反しない。「〜は違法です」等の断定は引き続きerrorのまま。
  { word: "違法", severity: "error", message: "法的リスクのあるワードです（断定は禁止。「違法ではありません」「違法？」の否定・疑問形のみ可）", allowIf: /違法ではありません|違法とは言えません|違法ではない|違法ではなく|違法[？?]/ },
  { word: "返金させる方法", severity: "error", message: "法的リスクのあるワードです" },

  // 「案件」は使わない
  { word: "案件", severity: "warning", message: "「案件」はユーザーに馴染みがない言葉です。「副業」「ネットビジネス」等に変えてください" },

  // 難しい言葉
  { word: "有耶無耶", severity: "warning", message: "難しい言葉です。中学生でもわかる言葉に変えてください" },
  { word: "エビデンス", severity: "warning", message: "難しい言葉です。「根拠」「証拠」に変えてください" },
  // 以下は ng-words.md にあるのにルール未登録だったもの（2026-08-10に追加）。
  // このルールは severity を実装しておらず全て error になるため、
  // 既存記事に多数出現する語は登録していない（既存記事の編集がブロックされるため）。
  // 未登録のまま残っている禁止語 … 入口/入り口(152記事407箇所)、マネタイズ、スキーム、
  // ローンチ、リテラシー。これらは ng-words.md の目視運用に委ねている。
  // 全8サイトの既存記事を実測した結果（2026-08-10）、下記4語のヒットは2記事のみ:
  //   玉石混交 → koyama-roumu/access-buppan.mdx ／ 賛否両論 → rise-job/shelikes.mdx
  // この2記事を編集するときだけ引っかかるので、そのとき本文を書き換えること。
  { word: "玉石混交", severity: "error", message: "難しい言葉です。「良いものと悪いものが混ざっている」に変えてください" },
  { word: "賛否両論", severity: "error", message: "難しい言葉です。具体的にどんな声があるかを書いてください" },
  { word: "一概には言えない", severity: "error", message: "結論をはっきり書いてください" },
  { word: "コンバージョン", severity: "error", message: "説明なしでは使わないでください" },

  // 自分に対するネガティブ
  { word: "気づかないかもしれません", severity: "warning", message: "自分に対するネガティブ表現は避けてください" },

  // 煽り系
  { word: "この記事を読み終わる頃には", severity: "warning", message: "煽りっぽい表現です" },
  { word: "しっかり理解できるはずです", severity: "warning", message: "煽りっぽい表現です" }
];

function reporter(context) {
  const { Syntax, RuleError, report, getSource } = context;

  return {
    [Syntax.Str](node) {
      const text = getSource(node);
      if (!text) return;

      for (const ng of NG_WORDS) {
        const index = text.indexOf(ng.word);
        if (index !== -1) {
          // allowIf: 同一テキスト内に許可パターンがあればスキップ（事実報道の引用等）
          if (ng.allowIf && ng.allowIf.test(text)) continue;
          report(
            node,
            new RuleError(
              `NGワード「${ng.word}」: ${ng.message}`,
              { index }
            )
          );
        }
      }
    }
  };
}

module.exports = {
  linter: reporter,
  fixer: undefined
};
