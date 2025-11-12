#!/bin/bash
# Quick project status check

echo "=== Regen Registry Review MCP - Quick Status ==="
echo ""

echo "📊 Git Status:"
git status --short
echo ""

echo "📝 Recent Commits (last 5):"
git log --oneline -5
echo ""

echo "📁 Project Structure:"
echo "Specs: $(find docs/specs -type f 2>/dev/null | wc -l) files"
echo "Transcripts: $(find docs/transcripts -type f 2>/dev/null | wc -l) files"
echo "Examples: $(find examples -type f 2>/dev/null | wc -l) files"
echo "Source: $(find src -type f 2>/dev/null | wc -l) files"
echo ""

echo "🔧 Implementation Status:"
if [ -d "src" ]; then
  echo "✅ Source directory exists"
  find src -name "*.py" -o -name "*.ts" -o -name "*.js" 2>/dev/null | head -5
else
  echo "⚠️  No src/ directory yet"
fi
echo ""

echo "📋 Todos:"
if [ -f ".claude/todos.md" ]; then
  grep -c "status.*pending\|status.*in_progress" .claude/todos.md 2>/dev/null || echo "0"
  echo "active tasks"
else
  echo "No todos tracked"
fi
echo ""

echo "🌿 Branches:"
git branch -a | grep -v HEAD
echo ""

echo "📅 Last Modified:"
# Cross-platform stat command (Linux uses -c, macOS uses -f)
if stat -c %y /dev/null >/dev/null 2>&1; then
  # Linux
  STAT_CMD="stat -c %y"
else
  # macOS
  STAT_CMD="stat -f %Sm -t '%Y-%m-%d %H:%M:%S'"
fi

LATEST_SPEC=$(ls -t docs/specs/*.md 2>/dev/null | head -1)
if [ -n "$LATEST_SPEC" ]; then
  echo "Specs: $($STAT_CMD "$LATEST_SPEC" 2>/dev/null || echo 'N/A')"
else
  echo "Specs: N/A"
fi

if [ -d "src" ]; then
  LATEST_SRC=$(find src -type f 2>/dev/null | head -1 | xargs ls -lt 2>/dev/null | head -1 | awk '{print $NF}')
  if [ -n "$LATEST_SRC" ]; then
    echo "Source: $($STAT_CMD "$LATEST_SRC" 2>/dev/null || echo 'N/A')"
  else
    echo "Source: N/A (no files in src/)"
  fi
else
  echo "Source: N/A (no src/ directory)"
fi
