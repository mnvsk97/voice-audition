#!/bin/bash
# Install the VoiceAudition skill into your project's .claude/skills/ directory.
# Usage: bash install-skill.sh /path/to/your/project

TARGET="${1:-.}"
SKILL_DIR="$TARGET/.claude/skills/voice-audition"

mkdir -p "$SKILL_DIR"

if [ -f "$(dirname "$0")/.claude/skills/voice-audition/SKILL.md" ]; then
  cp "$(dirname "$0")/.claude/skills/voice-audition/SKILL.md" "$SKILL_DIR/SKILL.md"
else
  echo "Error: SKILL.md not found. Run this from the voice-audition directory."
  exit 1
fi

echo "VoiceAudition skill installed to $SKILL_DIR"
echo "Usage: Ask Claude 'audition voices for my agent' in your project."
