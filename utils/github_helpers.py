import requests
from typing import List, Dict, Any

def fetch_starred_repos(username: str, github_token: str) -> List[Dict[str, Any]]:
    url = f"https://api.github.com/users/{username}/starred"
    headers = {"Authorization": f"token {github_token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()
