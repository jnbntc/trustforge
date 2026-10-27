#!/usr/bin/env bash
set -euo pipefail
REPO="jnbntc/trustforge"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
command -v gh >/dev/null || { echo 'Missing gh CLI' >&2; exit 1; }
command -v git >/dev/null || { echo 'Missing git CLI' >&2; exit 1; }
command -v python3 >/dev/null || { echo 'Missing python3' >&2; exit 1; }
gh auth status >/dev/null
LOGIN="$(gh api user --jq .login)"
[[ "$LOGIN" == "jnbntc" ]] || { echo "Authenticated user $LOGIN is not jnbntc" >&2; exit 1; }
if gh repo view "$REPO" >/dev/null 2>&1; then
  echo "Repository already exists; refusing automatic changes: $REPO" >&2; exit 1
fi
[[ ! -e .git ]] || { echo 'Already a git repo; inspect manually.' >&2; exit 1; }
echo "About to CREATE PUBLIC repository $REPO, push documentation, create 6 milestones and 28 issues."
read -r -p "Type CREATE-PUBLIC-TRUSTFORGE to proceed: " ACK
[[ "$ACK" == 'CREATE-PUBLIC-TRUSTFORGE' ]] || exit 1
git init -b main
git add README.md AGENTS.md CONTRIBUTING.md SECURITY.md .gitignore docs .github scripts
git -c user.name="${GIT_AUTHOR_NAME:-TrustForge Bootstrap}" -c user.email="${GIT_AUTHOR_EMAIL:-trustforge-bootstrap@users.noreply.github.com}" commit -m 'docs: initialize TrustForge architecture baseline'
gh repo create "$REPO" --public --description 'Educational OCI software supply chain security and verified updates lab' --source=. --remote=origin --push
python3 - <<'PYISSUES'
import json, subprocess
from pathlib import Path
issues=json.loads(Path('docs/issues.json').read_text())
repo='jnbntc/trustforge'
labels={'M0':'Foundation','M1':'OCI Explorer','M2':'Signed Build','M3':'TrustForge Gate','M4':'Adversarial Lab','M5':'Verified Updates'}
nums={}
for key,name in labels.items():
    data=json.loads(subprocess.check_output(['gh','api','-X','POST',f'repos/{repo}/milestones','-f',f'title={key} — {name}','-f','state=open'],text=True))
    nums[key]=data['number']; print('milestone',key,nums[key])
for item in issues:
    args=['gh','api','-X','POST',f'repos/{repo}/issues','-f',f'title=[{item["id"]}] {item["title"]}','-f',f'body={item["body"]}','-F',f'milestone={nums[item["milestone"]]}']
    data=json.loads(subprocess.check_output(args,text=True))
    print(item['id'],data['html_url'])
PYISSUES
echo "Bootstrap complete: https://github.com/$REPO"
