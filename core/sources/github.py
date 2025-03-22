import subprocess
import requests
import os
import math
from datetime import datetime


class User:
    def __init__(self, name: str):
        self._NAME = name.lower()
        
        self._response = requests.get(f"https://api.github.com/users/{name}", timeout=1)
        
        if self._response.status_code != 200:
            raise ConnectionError('status code is not 200')
        
        self._data: dict[str, str | int | bool | None] = self._response.json()
        
    @property
    def avatar_url(self) -> str:
        # [i] Even Ghost accounts and accounts that did not change their default GitHub avatar have an avatar
        return self._data["avatar_url"] # type: ignore
    
    @property
    def url(self) -> str:
        return self._data["html_url"] # type: ignore
    
    @property
    def followers(self) -> int:
        return self._data['followers'] # type: ignore
    
    @property
    def following(self) -> int:
        return self._data['following'] # type: ignore

    @property
    def twitter_username(self) -> str | None:
        return self._data["twitter_username"] # type: ignore
    
    @property
    def familiar_name(self) -> str:
        # [i] If there's no username overwrite, we'll just return the name
        name: str | None = self._data['name']
        return self._NAME if name is None else name
    
    @property
    def bio(self) -> str:
        # [i] If there's no bio, we'll quite literally return "No bio."
        bio: str | None = self._data['bio']
        return "No bio." if bio is None else bio
    
    @property
    def blog(self) -> str | None:
        return self._blog # type: ignore


class Repo:
    def __init__(self, owner: str, name: str):
        self._OWNER = owner
        self._NAME = name
        self._FULLNAME = f"{owner}/{name}"
        
        self._response = requests.get(f"https://api.github.com/repos/{owner}/{name}", timeout=1)

        if self._response.status_code != 200:
            raise ConnectionError('status code is not 200')

        self._data: dict[str, str | int | bool | None] = self._response.json()

    def clone(self, directory: str, method: str = 'https'):
        os.chdir(directory)
        
        match method:
            case 'ssh':
                subprocess.run(['git', 'clone', self._data['ssh_url']], text=True)
                return
                
            case _:
                subprocess.run(['git', 'clone', self._data['clone_url']], text=True)
                return
    
    def calculate_trust_level(self):
        # [*] Activity Score (time since last pushed & issue responsiveness)
        # [i] Time since last pushed
        delta_days_weight = 0.4
        issue_resp_weight = 0.6

        last_push_date = datetime.strptime(self._data['pushed_at'], "%Y-%m-%dT%H:%M:%SZ")
        days_since_last_pushed = (datetime.utcnow() - last_push_date).days

        open_issues = self._data['open_issues_count']
        closed_issues: int = 0
        url = f"{self._data['issues_url']}?state=closed"
        has_looped = 0

        while url:
            if has_looped > 4:
                break

            response = requests.get(url)

            closed_issues += len(response.json())
            has_looped += 1
            url = response.links.get('next', {}).get('url')

        url = f"{self._data['pulls_url']}?state=closed"

        has_looped = 0

        while url:
            if has_looped > 4:
                break

            response = requests.get(url)

            closed_issues -= len(response.json())
            has_looped += 1
            url = response.links.get('next', {}).get('url')

        issue_responsiveness = int(closed_issues / (closed_issues + open_issues)) # types: ignore

        return round((issue_responsiveness * issue_resp_weight) + ((60 / max(days_since_last_pushed + 1, 60)) * delta_days_weight), 2)

if __name__ == '__main__':
    test_a = Repo('MF366-Coding', "WriterClassic")
    print(test_a.calculate_trust_level())
    
    test_b = Repo('id-Software', "DOOM")
    print(test_b.calculate_trust_level())

    test_c = Repo('torvalds', "linux")
    print(test_c.calculate_trust_level())
