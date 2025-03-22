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
        downloads_resp = requests.get(self._data['releases_url'], timeout=1)
        
        download_score = 0
        
        last_pushed = datetime.strptime(self._data['pushed_at'], '%Y-%m-%dT%H:%M:%SZ')
        days_since_last_push = (datetime.now() - last_pushed).days
        push_score: int = 0
        
        if days_since_last_push <= 40:
            push_score = int(days_since_last_push)
            
        else:
            push_score = 1
        
        assets = None
        
        try:
            assets: dict[str, dict] = downloads_resp.json()["0"]['assets']
        
        except KeyError:
            download_score = 1
        
        if not download_score:
            downloads = 0
            
            for k in assets.keys():
                downloads += assets[k]['download_count']
                
            download_score = math.log(downloads + 1)
    
        final_score = (((self._data['stargazers_count'] + self._data['watchers_count']) + (self._data['forks_count'] * 2)) * ((download_score + push_score) / 2)) # type: ignore
        
        percentage = min((final_score / 40000) * 100, 100)

        return round(percentage, 2)

if __name__ == '__main__':
    test_a = Repo('MF366-Coding', "WriterClassic")
    print(test_a.calculate_trust_level())
    
    test_b = Repo('id-Software', "DOOM")
    print(test_b.calculate_trust_level())
