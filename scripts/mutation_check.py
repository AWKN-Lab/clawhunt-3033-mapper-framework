#!/usr/bin/env python3
"""变异自证：删掉 mapper_base 里的别名索引，AC1 断言必须变红。

- A 相：原代码跑全量 pytest，期望 exit 0。
- B 相：复制整仓到临时目录，只删 src/mapper_base.py 里建别名索引的那段
  （column_aliases 写入 alias_index 的循环），用复制仓跑
  tests/test_ac1_alias_match.py，期望 exit != 0（别名再也匹配不上，
  只有目标字段名本身能匹配）。
- C 相：原代码重跑全量 pytest，期望 exit 0。
- 全程不改仓库内的 mapper_base.py：前后各算一次 SHA256 并打印。
- 本脚本只打印结果；调用方把原始 stdout 存入 evidence/mutation-check.log。
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, "src", "mapper_base.py")

REMOVED_BLOCK = """    for target, aliases in column_aliases.items():
        if target not in field_names:
            continue
        for alias in aliases:
            alias_index.setdefault(normalize_column(alias), target)
"""


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def run(cmd: list[str], cwd: str) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def main() -> int:
    before = sha256(TARGET)
    print(f"mapper_base sha256 before: {before}")

    print("=== PHASE A: 原代码全量 pytest ===")
    code_a, out_a = run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT)
    print(out_a, end="")
    print(f"PHASE A exit={code_a}")

    print("=== PHASE B: 变异代码（删别名索引）跑 test_ac1_alias_match.py ===")
    code_b, out_b = -1, ""
    with tempfile.TemporaryDirectory(prefix="3033-mutation-") as tmp:
        copy_root = os.path.join(tmp, "repo")
        shutil.copytree(
            ROOT,
            copy_root,
            ignore=shutil.ignore_patterns(
                ".venv", ".git", "__pycache__", ".pytest_cache", "evidence"
            ),
        )
        mutated = os.path.join(copy_root, "src", "mapper_base.py")
        with open(mutated, encoding="utf-8") as f:
            text = f.read()
        assert REMOVED_BLOCK in text, "变异目标行在复制仓里找不到，变异未生效"
        with open(mutated, "w", encoding="utf-8") as f:
            f.write(text.replace(REMOVED_BLOCK, ""))
        code_b, out_b = run(
            [sys.executable, "-m", "pytest", "tests/test_ac1_alias_match.py", "-q"],
            cwd=copy_root,
        )
        print(out_b, end="")
        print(f"PHASE B exit={code_b}")

    after = sha256(TARGET)
    print(f"mapper_base sha256 after: {after}")
    print(f"mapper_base unchanged: {before == after}")

    print("=== PHASE C: 恢复原代码，全量 pytest ===")
    code_c, out_c = run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT)
    print(out_c, end="")
    print(f"PHASE C exit={code_c}")

    ok = code_a == 0 and code_b != 0 and code_c == 0 and before == after
    print(f"MUTATION CHECK: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
