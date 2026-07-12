#!/bin/bash
# 每日自动存档脚本
set -e

REPO="/home/minke/myMarkdown"
BACKUP_DIR="/home/minke/backup"
LOG="$REPO/scripts/backup.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M')] $1" >> "$LOG"; }

# ---- 1. Git 本地存档 ----
cd "$REPO"
if [ -n "$(git status --porcelain)" ]; then
    git add -A
    git commit -m "auto: daily backup $(date '+%Y-%m-%d')" 2>&1 | head -1 >> "$LOG"
    log "git commit done"
    # 有网络时自动推送
    if timeout 10 git push origin main 2>/dev/null; then
        log "push ok"
    else
        log "push failed (no network)"
    fi
else
    log "git clean, skip commit"
fi

# ---- 2. 每周压缩快照 (周日执行) ----
WEEKDAY=$(date +%u)
if [ "$WEEKDAY" = "7" ]; then
    mkdir -p "$BACKUP_DIR"
    TARFILE="$BACKUP_DIR/wiki-$(date +%Y%m%d).tar.xz"
    tar -caf "$TARFILE" \
        --exclude='.git' \
        --exclude='*/__pycache__' \
        --exclude='chat-analyzer/data' \
        --exclude='site' \
        -C /home/minke myMarkdown 2>/dev/null
    log "tar backup: $TARFILE ($(du -h "$TARFILE" | cut -f1))"
    # 只保留最近 4 个周备份
    ls -t "$BACKUP_DIR"/wiki-*.tar.xz 2>/dev/null | tail -n +5 | xargs rm -f 2>/dev/null
fi
