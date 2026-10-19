"""Write stats.svg with all-time GitHub totals, private contributions included.

Needs `gh` and GH_TOKEN (a token that can read the user's private contributions).
Only totals are emitted, never repo names.
"""
import json
import subprocess
from datetime import datetime, timezone


def gql(query):
    out = subprocess.run(["gh", "api", "graphql", "-f", f"query={query}"],
                         check=True, capture_output=True, text=True).stdout
    return json.loads(out)["data"]["viewer"]


me = gql("{viewer{login createdAt repositories(ownerAffiliations:OWNER,first:100){totalCount nodes{stargazerCount}}}}")
start = datetime.fromisoformat(me["createdAt"].replace("Z", "+00:00"))
now = datetime.now(timezone.utc)

t = dict(commits=0, private=0, prs=0, issues=0, reviews=0)
for year in range(start.year, now.year + 1):
    lo = max(start, datetime(year, 1, 1, tzinfo=timezone.utc))
    hi = min(now, datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc))
    c = gql('{viewer{contributionsCollection(from:"%s",to:"%s"){totalCommitContributions restrictedContributionsCount '
            'totalPullRequestContributions totalIssueContributions totalPullRequestReviewContributions}}}'
            % (lo.isoformat(), hi.isoformat()))["contributionsCollection"]
    t["commits"] += c["totalCommitContributions"]
    t["private"] += c["restrictedContributionsCount"]
    t["prs"] += c["totalPullRequestContributions"]
    t["issues"] += c["totalIssueContributions"]
    t["reviews"] += c["totalPullRequestReviewContributions"]

stars = sum(n["stargazerCount"] for n in me["repositories"]["nodes"])
total = sum(t.values())
rows = [
    ("Total contributions", total),
    ("Public commits", t["commits"]),
    ("Private contributions", t["private"]),
    ("Pull requests", t["prs"]),
    ("Code reviews", t["reviews"]),
    ("Repositories", me["repositories"]["totalCount"]),
    ("Stars earned", stars),
]

h = 60 + 28 * len(rows)
body = "".join(
    f'<text x="28" y="{78 + 28 * i}" class="k">{k}</text>'
    f'<text x="392" y="{78 + 28 * i}" class="v" text-anchor="end">{v:,}</text>'
    for i, (k, v) in enumerate(rows)
)
svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="420" height="{h}" viewBox="0 0 420 {h}" role="img" aria-label="GitHub stats">
<style>.t{{font:600 18px 'Segoe UI',Ubuntu,sans-serif;fill:#bd93f9}}.k{{font:400 14px 'Segoe UI',Ubuntu,sans-serif;fill:#f8f8f2}}.v{{font:600 14px 'Segoe UI',Ubuntu,sans-serif;fill:#ff79c6}}</style>
<rect width="418" height="{h - 2}" x="1" y="1" rx="8" fill="#282a36" stroke="#44475a"/>
<text x="28" y="38" class="t">{me['login']}'s GitHub stats (incl. private)</text>
{body}
</svg>
"""
open("stats.svg", "w").write(svg)
print(dict(rows))
