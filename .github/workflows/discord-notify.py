from httpx import HTTPStatusError
from dataclasses import dataclass
from pathlib import Path
import httpx
import json
import os

@dataclass
class GitHubCommit:
  sha: str
  author: str
  link: str
  header: str
  description: str | None = None

class repo:
  name = os.environ.get("REPO_FULL")
  branch = os.environ.get("BRANCH")
  link = f"https://github.com/{name}"

actor = os.environ.get("ACTOR")
event_path = os.environ.get("GITHUB_EVENT_PATH")
webhook = os.environ.get("WEBHOOK_URL")

commits_list: list[dict[str, str]] = []

if event_path and Path(event_path).exists():
  with open(event_path, "r", encoding='utf-8') as f:
    event_data = json.load(f)

    commits = event_data.get("commits", [])
    for commit in commits:
      commits_list.append({
        "sha": commit["id"],
        "message": commit["message"],
        "username": commit["author"]["username"]
      })

# do the stuff
commits_list.reverse() # latest commit is at the top
commit_count = len(commits_list)
commits: list[GitHubCommit] = []

for data in commits_list:
  sha = data["sha"][:7]
  sha_link = f"{repo.link}/commits/{data['sha']}"
  username = data["username"]
  
  parts = data["message"].split("\n", maxsplit=1)
  header = parts[0]
  description = parts[1][:100] if len(parts) > 1 else None
  description += "..." if len(description) == 100 and description != None else None # type: ignore | reason: unsupported operators (None)

  commits.append(GitHubCommit(sha, username, sha_link, header, description))

messages: list[str] = []
for commit in commits:
  messages.append(f"- [`[{commit.sha}]`]({commit.link}) - {commit.header} | **@{commit.author}**{"\n" if commit.description != None else ""}{commit.description if commit.description != None else ""}")

embed_header = f"<:github:1535885661683589161> │ GitHub Workflows/Actions\n# [[{repo.name} - {repo.branch}] {commit_count} new {'commits' if commit_count > 1 else "commit"}]({repo.link}/tree/{repo.branch})"

payload = {
  "username": "GitHub",
  "avatar_url": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png",
  "tts": False,
  "flags": 32768,
  "allowed_mentions": {
    "parse": [],
    "users": [],
    "roles": [],
    "replied_user": False
  },
  "components": [
    {
      "type": 17,
      "spoiler": False,
      "components": [
        {
          "type": 10,
          "content": embed_header
        },
        {
          "type": 14,
          "divider": True,
          "spacing": 1
        },
        {
          "type": 10,
          "content": "\n".join(messages)
        },
        {
          "type": 14,
          "divider": True,
          "spacing": 1
        },
        {
          "type": 10,
          "content": "-# <a:blasieuwu:1566439835013480579> [@blasieuwu](https://blasieuwu.neocities.org) (creator) - not affiliated with GitHub"
        }
      ]
    }
  ]
}

res = httpx.post(f"{webhook}?with_components=true", json=payload)

if res.status_code not in (200, 204):
  raise HTTPStatusError(f"discord webhook failed to send with error {res.status_code}", response=res, request=res.request)
