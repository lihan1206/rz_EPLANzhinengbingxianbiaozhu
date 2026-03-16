#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
PKG_NAME="eplan_parallel_release_${TIMESTAMP}.tar.gz"
PKG_PATH="release/${PKG_NAME}"

# 仅打包源码与运行所需文件，不执行任何自动化测试。
tar -czf "$PKG_PATH" \
  --exclude='./release' \
  --exclude='./.git' \
  --exclude='./**/.git' \
  --exclude='./frontend/node_modules' \
  --exclude='./**/node_modules' \
  --exclude='./.venv' \
  --exclude='./venv' \
  --exclude='./**/.venv' \
  --exclude='./**/venv' \
  --exclude='./target' \
  --exclude='./**/target' \
  --exclude='./**/__pycache__' \
  --exclude='./**/.pytest_cache' \
  --exclude='./**/.mypy_cache' \
  --exclude='./**/*.pyc' \
  --exclude='./**/dist' \
  --exclude='./**/build' \
  --exclude='./**/coverage' \
  --exclude='./**/tsconfig.tsbuildinfo' \
  --exclude='./**/*test*' \
  --exclude='./**/*spec*' \
  --exclude='./Prompt.md' \
  --exclude='./user_rule.md' \
  --exclude='./mb1.docx' \
  --exclude='./EPLAN智能并线标注系统V1.0软著材料说明书.docx' \
  .

ls -lh "$PKG_PATH"
