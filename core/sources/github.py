import subprocess
import requests
import os
from math import log
from datetime import datetime
import re

WEIGHTS = {
        'wstars': 0.25,
        'wforks': 0.25,
        'wcontributors': 0.21,
        'wdays': 0.07,
        'wlicense': 0.06,
        'wissue': 0.1,
        'wfollowers': 0.06
}

LICENSE_CLASSIFICATION = {
    # [*] Very Permissive
    "MIT": 1.0,
    "Apache-2.0": 1.0,
    "BSD-2-Clause": 1.0,
    "Unlicense": 1.0,
    "CC0-1.0": 1.0,
    "WTFPL": 1.0,
    "Public-Domain": 1.0,
    "Boost": 1.0,
    "Zlib": 1.0,
    "ISC": 1.0,

    # [*] Permissive with minor restrictions
    "BSD-3-Clause": 0.9,
    "ECL-2.0": 0.9,

    # [*] Neutral (Attribution, Non-commercial)
    "CC-BY-4.0": 0.7,
    "CC-BY-SA-4.0": 0.7,
    "CC-BY-NC-4.0": 0.7,
    "CC-BY-NC-SA-4.0": 0.7,
    "EPL-1.0": 0.7,
    "EPL-2.0": 0.7,

    # [*] Copyleft (even weaker)
    "LGPL-3.0": 0.6,
    "LGPL-2.1": 0.6,

    # [*] Copyleft (weaker)
    "GPL-3.0": 0.4,
    "GPL-3.0-only": 0.4,
    "GPL-3.0-or-later": 0.4,

    # [*] Stronger Copyleft (Network use, etc.)
    "AGPL-3.0": 0.3,
    "GPL-2.0-only": 0.2,
    "GPL-2.0-or-later": 0.2,
    "GPL-2.0": 0.2,

    # [*] Other recognized licenses
    "ECL-1.0": 0.9,
    "EUPL-1.2": 0.7,
    "NCSA": 1.0,
    "JSON": 1.0,
    "CC-BY-ND-4.0": 0.7,
    "CC-BY-NC-ND-4.0": 0.7,
    "Eclipse-1.0": 0.7,
    "Creative-Commons": 0.7
}


def get_license_tier(license: dict[str, str] | None) -> float:
    if not license:
        # [i] Unlicensed repo = Very permissive
        return 1.0

    if license['spdx_id'] == 'NOASSERTION' or license['key'] == 'other':
        # [i] Custom license
        return 0.5

    if license['spdx_id'] != 'NOASSERTION' and license['spdx_id'] not in LICENSE_CLASSIFICATION:
        return 0.7

    return LICENSE_CLASSIFICATION.get(license['spdx_id'], 0.7)


class Repo:
    def __init__(self, owner: str, name: str):
        self._OWNER = owner
        self._NAME = name
        self._FULLNAME = f"{owner}/{name}"
        
        self._response = requests.get(f"https://api.github.com/repos/{owner}/{name}", timeout=1)

        if self._response.status_code != 200:
            raise ConnectionError('status code is not 200')

        self._data: dict[str, str | int | bool | None] = self._response.json()

        self._contributors = -1
        self._most_recent_issue = {
            'all': -1,
            'closed': -1,
            'open': -1
        }
        self._followers = -1
        
    @property
    def is_contenterx_package(self):
        url = "https://raw.githubusercontent.com/MF366-Coding/WriterClassic/refs/heads/main/contenterx/setup.cx"
        response = requests.get(url, timeout=1)
        
        return (response.status_code == 200)

    def clone(self, directory: str, method: str = 'https'):
        os.chdir(directory)
        
        match method:
            case 'ssh':
                subprocess.run(['git', 'clone', self._data['ssh_url']], text=True)
                return
                
            case _:
                subprocess.run(['git', 'clone', self._data['clone_url']], text=True)
                return

    @property
    def is_legacy(self) -> bool:
        date = self._data['created_at'].replace("Z", "+0000")
        year = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z").year
        delta_years = datetime.now().year - year

        return delta_years >= 10

    def fetch_user_followers(self, fallback: int = 0) -> int:
        url = f"https://api.github.com/users/{self._OWNER}"
        response = requests.get(url, timeout=1.2)

        if response.status_code == 200:
            return response.json().get('followers', fallback)

        return fallback

    def fetch_contributor_count(self, fallback: tuple[int, int] = (10, 15000), multiplier: int = 10) -> int:
        # [i] there are 2 fallbacks because one is for error/missing and the second is for Too Large
        url = f"https://api.github.com/repos/{self._OWNER}/{self._NAME}/contributors?per_page=1&anon=false"
        response = requests.get(url, timeout=1.5)

        if response.status_code == 200:
            link_header = response.headers.get("Link")

            if link_header:
                # [i] there are other pages
                match = re.search(r'&page=(\d+)>; rel="last"', link_header)

                if match:
                    return int(match.group(1)) * multiplier # [i] GitHub's API does not reflect the amount of contributors well so we multiply it to approximate the result

            # [i] there are NO other pages
            return len(response.json())

        elif response.status_code == 403:
            if response.json().get('message', None) == "The history or contributor list is too large to list contributors for this repository via the API.":
                return fallback[1] # [i] Fallback for values that are too large

            return fallback[0] # [i] General Fallback

        else:
            return fallback[0] # [i] Fallback for unknown values or errors

    @property
    def is_elligible_for_trust_boost(self):
        is_legacy = self.is_legacy

        if self._contributors == -1:
            self._contributors = self.fetch_contributor_count()

        has_contributors = (self._contributors >= 7500)
        has_forks = (self._data.get('forks_count', self._data.get('forks', 1)) >= 10000) # type: ignore

        return (is_legacy and has_contributors and has_forks)

    def fetch_most_recent_issue(self, state: str = 'all', fallback: int = 0, prs: int = 10) -> int:
        url = f"https://api.github.com/repos/{self._OWNER}/{self._NAME}/issues?state={state}&per_page=1&anon=false"
        response = requests.get(url, timeout=1.5)

        if response.status_code == 200:
            issue_id = max(response.json()[0].get('number', fallback), 1)

            if issue_id >= 11:
                issue_id -= prs

            return issue_id

        return fallback

    def get_days_since_last_push(self) -> int:
        if not self._data.get('pushed_at', None):
            return 366 # [i] Won't receive benefits, even if ellegible

        date = self._data['pushed_at']#.replace('Z', '+0000')
        days = datetime.now().day - datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").day

        return days

    def calculate_trust_rate(self, **weights: float):
        if self.is_elligible_for_trust_boost:
            THRESHOLD = 200

        elif self.is_legacy:
            THRESHOLD = 365

        else:
            THRESHOLD = 100

        if self._most_recent_issue['all'] == -1:
            self._most_recent_issue['all'] = self.fetch_most_recent_issue(fallback=1)

        if (not self._most_recent_issue['all']) or (not self._data['has_issues']):
            issue_responsiveness = 0

        else:
            issue_responsiveness = (1 - (self._data['open_issues_count'] / self._most_recent_issue['all'])) * 100 # type: ignore

        if self._contributors == -1:
            self._contributors = self.fetch_contributor_count(multiplier=11) # [i] smol extra boost? :eyes:

        if self._followers == -1:
            self._followers = self.fetch_user_followers()

        trust_rate = (
            (min(log(self._data.get('stargazers_count', 0)) * 10, 100)) * weights['wstars'] +
            (min(log(self._data.get('forks_count', self._data.get('forks', 0))) * 10, 100)) * weights['wforks'] +
            (min(log(self._contributors) * 10, 100)) * weights['wcontributors'] +
            (max(0, THRESHOLD - self.get_days_since_last_push())) * weights['wdays'] +
            (get_license_tier(self._data['license']) * weights['wlicense']) +
            (issue_responsiveness * weights['wissue']) +
            (min(log(self._followers) * 10, 100)) * weights['wfollowers']
        )

        if self.is_elligible_for_trust_boost:
            trust_rate += 7

        final_result = max(trust_rate, 0)
        final_result = min(final_result, 100)

        return round(final_result, 2)


if __name__ == '__main__':
    test_a = Repo('MF366-Coding', "WriterClassic")
    print(test_a.calculate_trust_rate(**WEIGHTS))
    
    test_b = Repo('id-Software', "DOOM")
    print(test_b.calculate_trust_rate(**WEIGHTS))

    test_c = Repo('torvalds', "linux")
    print(test_c.calculate_trust_rate(**WEIGHTS))

    test_d = Repo('microsoft', "vscode")
    print(test_d.calculate_trust_rate(**WEIGHTS))

    test_e = Repo('norbcodes', "entities")
    print(test_e.calculate_trust_rate(**WEIGHTS))
