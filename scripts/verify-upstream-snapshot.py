#!/usr/bin/env python3
"""同梱したseo-site-skillsスナップショットの改変を検出する。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_ROOT = SKILL_ROOT / "references" / "seo-site-skills"
MANIFEST_PATH = SKILL_ROOT / "upstream-manifest.json"


def snapshot_digest(root: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    for path in files:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        data = path.read_bytes()
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest(), len(files)


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    actual_digest, actual_count = snapshot_digest(SNAPSHOT_ROOT)
    expected_digest = manifest["snapshotSha256"]
    expected_count = manifest["fileCount"]

    if actual_digest != expected_digest or actual_count != expected_count:
        print("FAIL: seo-site-skillsスナップショットが記録時点から変わっています")
        print(f"expected sha256={expected_digest} files={expected_count}")
        print(f"actual   sha256={actual_digest} files={actual_count}")
        return 1

    print(
        "PASS: seo-site-skillsスナップショット一致 "
        f"sha256={actual_digest} files={actual_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
