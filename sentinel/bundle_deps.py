"""Run before deploying: copies refundbot/prompt_content.py and policy.md into sentinel/vendored/.
This is needed because Cloud Run only ships the current folder, so we can't sibling-import."""

import shutil
from pathlib import Path

src_dir = Path(__file__).parent.parent / "refundbot"
dst_dir = Path(__file__).parent / "vendored"
dst_dir.mkdir(exist_ok=True)

for fname in ["prompt_content.py", "policy.md"]:
    src = src_dir / fname
    dst = dst_dir / fname
    if not src.exists():
        print(f"⚠️  WARNING: {src} not found — skipping")
        continue
    shutil.copy(src, dst)
    print(f"✅ Vendored {fname}")

print("\nDone. Bundle ready for deploy.")