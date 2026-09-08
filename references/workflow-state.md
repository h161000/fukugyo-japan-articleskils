# 工程の記録とGate

記事作成時、最初の資料読み込みから記録を残す。slug未確定時は取得パス・日時・適用要件を会話内に保持し、案件確定後に作業フォルダへ移す。初期化のcreated_atは実際に記事作業を開始した日時へ合わせる。別記事の完了記録はコピーしない。

## 初期化と工程移行

```bash
python3 <SKILL_ROOT>/scripts/check_workflow.py init <ARTICLEWORK>/workflow-state.json --slug <slug> --case-id <task-id> --request '今回の依頼原文'
python3 <SKILL_ROOT>/scripts/check_workflow.py ready <ARTICLEWORK>/workflow-state.json --stage research
python3 <SKILL_ROOT>/scripts/check_workflow.py complete <ARTICLEWORK>/workflow-state.json --stage research
```

資料取得前の仮slugで初期化した場合は、案件確定後に作業フォルダ・slug・case_idを同期する。ユーザー提供資料のみの場合、case_idにはその資料を識別できる値を使う。既存stateの上書き初期化は禁止。公開が明示されたら依頼原文を追記しscopeをpublishへ変更する。作成依頼でpublishを実行しない。

- `ready`は前工程までの完了と、対象工程の必読資料の記録を検査する。合格後にstarted_atを実時刻で記録してstatusをin_progressにし、工程を開始する。
- cta工程ではline-cvrを読んで型を判定し、その後closing-templatesを読む。型選定の準備後、CTA文言の制作を始める前にreadyを通す。
- 終了条件を内容確認してchecksを記録し、statusをcomplete、completed_atを実時刻にして`complete`を通す。失敗時はin_progressへ戻して不足を解消する。Gateは自動で完了扱いにしない。
- 証拠画像の取得は調査中でも行える。画像取得前に該当資料を読み、imagesのreadsへ記録する。images工程の完了には構成・本文との整合も必要。
- 作成の納品前は`complete --stage review`、本番公開完了時は`complete --stage publish`を実行する。公開前は`ready --stage publish`も必要。

## 記録形式

工程・必読パス・必須成果物・検査IDの正本は`workflow-manifest.json`。初期化が作るreadsは未読状態であり、生成だけで読了にはならない。

readsの各要素に次を記録する。

- path: 実際に読んだ正本の絶対パス
- sha256: 読んだ時点のファイルのSHA-256（ファイル変更検出用）
- read_at: 全文取得を確認した日時（タイムゾーン付きISO 8601）
- applied_rule: その資料から対象工程へ適用する具体的な要件

子スキルが指定する必読参照、利用するimagegenスキル、初回キャラ作成資料等も条件成立時にreadsへ追加する。必読経路が循環しても、同一記事・同一内容のファイルを同じ工程内で無限に読み直す必要はない。別工程の同一資料は今回の記事で読んだ記録を参照できるが、原文が文脈から失われた場合や読み直し指定がある場合は再取得する。

checksは検査IDをキーに、status（合格時pass）、detail（判断根拠と該当箇所）、evidence（ログ・調査記録・レビュー等の絶対パス）、sha256（証跡ファイルのSHA-256）を保存する。既存のreview-reportなどを証跡に利用してよい。成功した検査コマンド・終了コード・対象原稿のハッシュは証跡内へ記録する。ブラウザ確認では対象URL・日時・幅・結果を保存する。未実施をpassにしない。

必須検査IDのうちidentityは案件・サイト・取得者の一致、sourcesは調査根拠と未確認事項、cta-choiceは型と読者状態、critic-responseは指摘対応、draft-syncは正本と公開MDXの一致を示す。その他はSKILL.mdの同名工程に対応する。imagegen-skillでは実際に使う画像生成スキルの読了と適用根拠も示す。必要な追加検査はchecksに追加する。

適用除外はexceptionsへrule_source（正本パスと該当規定）、reason、replacement_check（checks内の代替検査ID）を記録する。必須検査全体を除外せず、明示された対象項目だけを代替検査で補い、その結果を必須検査のdetailにも記録する。

## 再開・修正後

中断後は対象案件・依頼範囲・未解決事項・次の未完了工程を照合する。原文を参照できなければ再読する。資料や原稿を変更したら影響する工程・検査をin_progressへ戻し、再確認する。更新された証跡のハッシュだけを付け替えて合格扱いにしない。共通のreview-reportへ追記しただけの場合は、既存判定が変わっていないことを照合してハッシュを更新してよい。

Gateは必読パス・記録形式・成果物の存在・証跡の変更を検出する補助検査である。読了日時と判断理由は自己申告であり、理解の証明やツール操作の強制制御ではない。全文取得は実行ログと照合し、案件一致・内容品質・動的に追加すべき必読資料は主担当が確認する。単に「読了」「問題なし」と記録して通過させない。
