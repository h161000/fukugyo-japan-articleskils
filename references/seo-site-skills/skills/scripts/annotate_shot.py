#!/usr/bin/env python3
"""annotate_shot.py — LPの実スクショに「見出し帯」「枠＋番号」「注釈」を焼き込む。

設計方針（重要）:
  ・テキスト注釈は画像の【外側の帯】に置く。LP上の文字を注釈で覆い隠さない。
    引用として提示している以上、元の記載を消したり書き換えたりしない。
  ・画像の【内側】に入れてよいのは、枠（outline）と番号バッジと矢印だけ。
  ・個人情報（氏名・電話・口座等）が写り込んだときだけ mask でぼかす。

生成方法はアイキャッチと同じ HTML/CSS + Playwright スクショ。PILで文字を描かない
（日本語の字形・行間が崩れるため）。

使い方（Python から）:

    from annotate_shot import annotate

    annotate(
        src="public/images/foo-sec03.webp",
        out="public/images/foo-sec03.webp",
        title="料金プランの記載",                      # 上帯（何を示す画像か）
        boxes=[
            {"x": 4, "y": 46, "w": 44, "h": 22, "label": "1"},
            {"x": 52, "y": 46, "w": 44, "h": 22, "label": "2", "color": "#f6e05e"},
        ],
        notes=[
            "1 月額9,800円と表示されている",
            "2 初期費用は「別途」とだけ書かれ金額の記載がない",
        ],
        footer="実際の広告ページより",
    )

使い方（CLI）:
    python3 annotate_shot.py in.webp out.webp --title "料金プランの記載" \
        --box 4,46,44,22,1 --note "1 月額9,800円と表示されている"

座標は画像に対する【％】。ピクセルではない。元画像のサイズが変わっても崩れない。
"""

from __future__ import annotations

import argparse
import base64
import os
import subprocess
import sys
import tempfile

# 帯の色。サイトのトンマナに合わせて変えてよい（キャラファイル側で指定可）
BAR_BG = "#1f2937"
BAR_FG = "#ffffff"
NOTE_BG = "#faf9f6"
NOTE_FG = "#1a1a1a"
DEFAULT_BOX_COLOR = "#e53e3e"

# 日本語フォントはシステム内蔵を使う（ネットワーク不要・CI でも落ちない）
FONT_STACK = (
    "'Hiragino Kaku Gothic ProN','Hiragino Sans','Noto Sans JP',"
    "'Yu Gothic','Meiryo',sans-serif"
)


def _to_png(path: str) -> str:
    """webp を含む任意の画像を PNG の一時ファイルにして返す。"""
    from PIL import Image

    im = Image.open(path).convert("RGB")
    fd, tmp = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    im.save(tmp)
    return tmp


def _b64(path: str) -> str:
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def _build_html(img_uri: str, w: int, h: int, title, boxes, notes, footer, masks) -> str:
    bar_h = 46 if title else 0
    # 注釈帯の高さ: 1行28px + 上下パディング
    note_h = (len(notes) * 28 + 20) if notes else 0
    foot_h = 30 if footer else 0
    total_h = bar_h + h + note_h + foot_h

    box_html = []
    for b in boxes:
        color = b.get("color", DEFAULT_BOX_COLOR)
        label = str(b.get("label", "")).strip()
        badge = (
            f'<span class="badge" style="background:{color}">{label}</span>' if label else ""
        )
        box_html.append(
            f'<div class="box" style="left:{b["x"]}%;top:{b["y"]}%;'
            f'width:{b["w"]}%;height:{b["h"]}%;border-color:{color}">{badge}</div>'
        )

    mask_html = [
        f'<div class="mask" style="left:{m["x"]}%;top:{m["y"]}%;'
        f'width:{m["w"]}%;height:{m["h"]}%"></div>'
        for m in masks
    ]

    # 枠の label→色 の対応表。注釈の先頭番号を同じ色の丸バッジにして目で追えるようにする
    box_color = {}
    for b in boxes:
        lb = str(b.get("label", "")).strip()
        if lb:
            box_color[lb] = b.get("color", DEFAULT_BOX_COLOR)

    import re

    def _text_on(bg: str) -> str:
        """下地色の輝度から、白文字か黒文字かを自動で選ぶ（明るい色→黒、濃い色→白）。"""
        h = bg.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "#111111" if lum > 0.6 else "#ffffff"

    def _render_note(n: str) -> str:
        # 注釈行は「枠と同色のベタ塗りバー」。文字色は下地の輝度から自動で決める
        m = re.match(r"^\s*(\d+)\s+(.*)$", n)
        if m:
            num, rest = m.group(1), m.group(2)
            fill = box_color.get(num, DEFAULT_BOX_COLOR)
        else:
            num, rest, fill = "", n, DEFAULT_BOX_COLOR
        txt = _text_on(fill)
        chip = f'<span class="nchip">{num}</span>' if num else ""
        return (
            f'<div class="note" style="background:{fill};color:{txt}">'
            f'{chip}<span class="ntext">{rest}</span></div>'
        )

    notes_html = "".join(_render_note(n) for n in notes)

    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{w}px;font-family:{FONT_STACK};background:{NOTE_BG}}}
.bar{{height:{bar_h}px;background:{BAR_BG};color:{BAR_FG};display:flex;align-items:center;
     padding:0 16px;font-size:19px;font-weight:700;letter-spacing:.02em}}
.bar .mark{{margin-right:8px;font-size:15px;opacity:.85}}
.shot{{position:relative;width:{w}px;height:{h}px;overflow:hidden}}
.shot img{{width:100%;height:100%;display:block}}
.box{{position:absolute;border:12px solid {DEFAULT_BOX_COLOR};border-radius:4px;
     box-shadow:0 0 0 2px rgba(255,255,255,.75) inset}}
.badge{{position:absolute;top:-20px;left:-20px;width:40px;height:40px;border-radius:50%;
       color:#fff;font-size:22px;font-weight:800;display:flex;align-items:center;
       justify-content:center;box-shadow:0 2px 6px rgba(0,0,0,.3)}}
.mask{{position:absolute;background:#3b3b3b;border-radius:2px}}
.notes{{padding:13px 16px 15px;background:#f0eee7;border-top:2px solid #d8d2c4;
       display:flex;flex-direction:column;gap:8px}}
.note{{display:flex;align-items:flex-start;gap:10px;font-size:16px;line-height:24px;
      font-weight:700;border-radius:7px;padding:9px 14px}}
.nchip{{flex:0 0 auto;width:22px;height:22px;border-radius:50%;border:2px solid currentColor;
       background:transparent;font-size:14px;font-weight:800;display:flex;
       align-items:center;justify-content:center;margin-top:1px}}
.ntext{{flex:1;min-width:0}}
.foot{{display:flex;align-items:center;padding:8px 18px 10px;
      font-size:13px;color:#777;font-weight:700}}
</style></head><body>
{f'<div class="bar"><span class="mark">▼</span>{title}</div>' if title else ''}
<div class="shot"><img src="{img_uri}">{''.join(box_html)}{''.join(mask_html)}</div>
{f'<div class="notes">{notes_html}</div>' if notes else ''}
{f'<div class="foot">{footer}</div>' if footer else ''}
</body></html>"""


def annotate(
    src: str,
    out: str,
    title: str | None = None,
    boxes: list | None = None,
    notes: list | None = None,
    footer: str | None = None,
    masks: list | None = None,
    max_width: int = 800,
    max_height: int = 600,
) -> str:
    """スクショに注釈を焼き込んで out に保存する（.webp なら cwebp 変換まで行う）。

    boxes / masks の座標は元画像に対する％（x, y, w, h）。
    boxes には label（番号）と color（枠色）を指定できる。
    notes は画像の下に出る注釈行。番号と対応させて書く。
    """
    from PIL import Image
    from playwright.sync_api import sync_playwright

    boxes = boxes or []
    notes = notes or []
    masks = masks or []

    png = _to_png(src)
    w, h = Image.open(png).size

    # 元スクショが上限を超えていたら先に縮める（帯を足すと更に伸びるため）
    if w > max_width:
        im = Image.open(png)
        h = int(h * max_width / w)
        w = max_width
        im.resize((w, h), Image.LANCZOS).save(png)

    html = _build_html(_b64(png), w, h, title, boxes, notes, footer, masks)
    fd, html_path = tempfile.mkstemp(suffix=".html")
    os.close(fd)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    raw_out = out[:-5] + ".png" if out.endswith(".webp") else out
    os.makedirs(os.path.dirname(os.path.abspath(raw_out)) or ".", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_context(device_scale_factor=2).new_page()
        page.goto("file://" + html_path)
        page.wait_for_timeout(200)
        page.locator("body").screenshot(path=raw_out)
        browser.close()

    # 高さ上限を超えたら縮める（注釈帯のぶん伸びるので必ず確認する）
    im = Image.open(raw_out)
    if im.height > max_height or im.width > max_width:
        r = min(max_width / im.width, max_height / im.height)
        im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS).save(raw_out)

    if out.endswith(".webp"):
        subprocess.run(["cwebp", "-q", "88", raw_out, "-o", out], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(raw_out)

    for t in (png, html_path):
        try:
            os.remove(t)
        except OSError:
            pass
    return out


def _parse_box(s: str) -> dict:
    """'x,y,w,h[,label[,color]]' をパースする。"""
    parts = s.split(",")
    if len(parts) < 4:
        raise argparse.ArgumentTypeError("--box は x,y,w,h[,label[,color]] 形式")
    b = {k: float(v) for k, v in zip("xywh", parts[:4])}
    if len(parts) >= 5:
        b["label"] = parts[4]
    if len(parts) >= 6:
        b["color"] = parts[5]
    return b


def main() -> int:
    ap = argparse.ArgumentParser(description="LPスクショに見出し帯・枠・注釈を焼き込む")
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--title", help="上帯に出す「何を示す画像か」の一文")
    ap.add_argument("--box", action="append", type=_parse_box, default=[],
                    help="x,y,w,h[,label[,color]]（％指定・複数可）")
    ap.add_argument("--note", action="append", default=[], help="下に出す注釈行（複数可）")
    ap.add_argument("--mask", action="append", type=_parse_box, default=[],
                    help="ぼかす領域 x,y,w,h（個人情報の写り込み用）")
    ap.add_argument("--footer", default="実際の広告ページより")
    a = ap.parse_args()

    path = annotate(a.src, a.out, title=a.title, boxes=a.box, notes=a.note,
                    footer=a.footer, masks=a.mask)
    print(f"saved: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
