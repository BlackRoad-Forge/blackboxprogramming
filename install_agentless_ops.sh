#!/usr/bin/env bash
# install_agentless_ops.sh
# Creates all Agentless Ops files in the current repo directory

set -euo pipefail

mkdir -p .github/workflows tools .blackroad .github/ISSUE_TEMPLATE

# 1) Workflow
cat > .github/workflows/ops.yml <<'YAML'
<PASTE ops.yml CONTENT FROM MY EARLIER DROP HERE>
YAML

# 2) issue_sync.py
cat > tools/issue_sync.py <<'PY'
<PASTE issue_sync.py CONTENT HERE>
PY
chmod +x tools/issue_sync.py

# 3) autopush.sh
cat > tools/autopush.sh <<'BASH'
<PASTE autopush.sh CONTENT HERE>
BASH
chmod +x tools/autopush.sh

# 4) issue manifest
cat > .blackroad/issue-manifest.json <<'JSON'
{
  "assignee": "blackboxprogramming",
  "issues": [
    "Security: enable Dependabot, secret scanning, and CodeQL",
    "Create Ops README with standard runbooks",
    "Set up RoadView pipeline stub and tracking issue",
    "Backfill CI for lint/tests on main",
    "Add login gate + route placeholders for all portals"
  ]
}
JSON

# 5) plan.md template
cat > .github/ISSUE_TEMPLATE/plan.md <<'MD'
<PASTE plan.md CONTENT HERE>
MD

# 6) Makefile
cat > Makefile <<'MAKE'
<PASTE Makefile CONTENT HERE>
MAKE

# 7) .env.example
cat > .env.example <<'ENV'
# Copy to .env and fill locally/runner-side (never commit real secrets)
GITHUB_REPO=blackboxprogramming/blackboxprogramming
DEPLOY_SSH_KEY_PATH=~/.ssh/id_ed25519
ENV

echo "✅ Agentless Ops files created. Now commit & push:"
echo "   git add . && git commit -m 'feat: add agentless ops workflow + tools' && git push -u origin agentless-ops"