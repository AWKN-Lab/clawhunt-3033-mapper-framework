#!/usr/bin/env bash
# #3033 最小样品一键自测：pytest 全量 + 变异自证 + MANIFEST 核验。
# 任何一步失败都退出非零。由 setup.sh 调用，也可单独跑。
set -eu
cd "$(dirname "$0")/.."

PY="${TEST_PY:-.venv/bin/python}"
if [ ! -x "$PY" ]; then PY="python3"; fi

echo "=== 1/3 pytest ==="
"$PY" -m pytest -q

echo "=== 2/3 变异自证 ==="
"$PY" scripts/mutation_check.py

echo "=== 3/3 核对 MANIFEST ==="
sha256sum -c MANIFEST

echo "RUN_ALL: PASS"
