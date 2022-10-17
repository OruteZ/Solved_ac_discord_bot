import pandas as pd
import requests
import json
import random


class BOJIDNotFoundError(Exception):
    def __init__(self):
        super().__init__('해당 BOJ ID를 Solved.Ac 에서 찾을 수 없음')


Tier_list = [
    "Unrated",
    "Bronze V", "Bronze IV", "Bronze III", "Bronze II", "Bronze I",
    "Silver V", "Silver IV", "Silver III", "Silver II", "Silver I",
    "Gold V", "Gold IV", "Gold III", "Gold II", "Gold I",
    "Platinum V", "Platinum IV", "Platinum III", "Platinum II", "Platinum I",
    "Diamond V", "Diamond IV", "Diamond III", "Diamond II", "Diamond I",
    "Ruby V", "Ruby IV", "Ruby III", "Ruby II", "Ruby I",
    "Master"
]


def get_dataframe_from_backup():
    try:
        BOJ_users_dataframe = pd.read_csv("backup.csv", sep=',')
    except pd.errors.EmptyDataError:
        cname = ['discord_id', 'handle', 'bio', 'organizations', 'badge', 'background',
                 'profileImageUrl', 'solvedCount', 'solvedProblems', 'voteCount', 'class',
                 'classDecoration', 'tier', 'rating', 'ratingByProblemsSum',
                 'ratingByClass', 'ratingBySolvedCount', 'ratingByVoteCount', 'exp',
                 'rivalCount', 'reverseRivalCount', 'maxStreak', 'proUntil', 'rank']
        BOJ_users_dataframe = pd.DataFrame(columns=cname)
        BOJ_users_dataframe.set_index('discord_id')
        return BOJ_users_dataframe


BOJ_users_dataframe = get_dataframe_from_backup()


# return True if tag is available else False
def is_tag_available(tag):
    url = "https://solved.ac/api/v3/search/tag"
    querystring = {"query": "#" + tag, "page": "1"}
    headers = {"Content-Type": "application/json"}
    response = requests.request("GET", url, headers=headers, params=querystring)
    Json = json.loads(response.text)
    return Json['count'] != 0


def BOJ_random_defense(Tier='', tags=None):
    if tags is None: tags = []
    print("random Boj call")

    query = "s#100.. "

    if Tier != '': query += f"*{Tier} "

    for tag in tags:
        if is_tag_available(tag): query += "#" + tag + " "

    print(f"query = {query}")

    page = 1
    url = "https://solved.ac/api/v3/search/problem"
    querystring = {"query": query, "page": str(page), "sort": "solved", "direction": "desc"}
    headers = {"Content-Type": "application/json"}
    response = requests.request("GET", url, headers=headers, params=querystring)

    problems_json_object = json.loads(response.text)

    problems = problems_json_object['items']

    # 만약 해당 문제가 없을경우, 최소 100명 풀이 제한 제거 후 다시 탐색
    if not problems:
        query = ""

        if Tier != '': query += f"*{Tier} "

        for tag in tags:
            if is_tag_available(tag): query += "#" + tag + " "

        print(f"query = {query}")

        page = 1
        url = "https://solved.ac/api/v3/search/problem"
        querystring = {"query": query, "page": str(page), "sort": "solved", "direction": "desc"}
        headers = {"Content-Type": "application/json"}
        response = requests.request("GET", url, headers=headers, params=querystring)

        problems_json_object = json.loads(response.text)

        problems = problems_json_object['items']

    return None if problems == [] else random.choice(problems)


# Get information of id by series
def get_user_data(boj_id):
    url = "https://solved.ac/api/v3/user/show"
    querystring = {"handle": boj_id}
    headers = {"Content-Type": "application/json"}
    response = requests.request("GET", url, headers=headers, params=querystring)

    if response.status_code == 404: raise BOJIDNotFoundError

    user_info = response.json()

    user_info['solvedProblems'] = get_solved_problems(boj_id)

    return pd.Series(user_info)


# Get all problems that user solved by list
def get_solved_problems(boj_id):
    url = "https://solved.ac/api/v3/search/problem"
    headers = {"Content-Type": "application/json"}

    solved_problem_list = []
    page = 1
    while True:
        querystring = {"query": "@" + boj_id, "page": page, "sort": "id", "direction": "asc"}
        response = requests.request("GET", url, headers=headers, params=querystring)
        if response is 'Too Many Requests': return False

        lists = list(map(lambda item: item['problemId'], json.loads(response.text)['items']))
        if not lists: break
        solved_problem_list += lists
        page += 1
    return solved_problem_list


# add user by two id, return False is boj_id no exist
def add_user_data(discord_id, boj_id):
    if discord_id in BOJ_users_dataframe.index: return True

    try:
        user_info = get_user_data(boj_id)
    except BOJIDNotFoundError:
        return False

    user_info['discord_id'] = discord_id
    BOJ_users_dataframe.loc[discord_id] = user_info
    return True


def find_solved_problem(old_problems, new_problems):
    return list(set(new_problems) - set(old_problems))


# reset user data by discore id, return delta of changed values by Series
def reset_user_data(discord_id):
    if discord_id not in BOJ_users_dataframe.index: return None

    boj_id = BOJ_users_dataframe.loc[discord_id, 'handle']

    old_data = BOJ_users_dataframe.loc[discord_id]
    new_data = get_user_data(boj_id)
    new_data['discord_id'] = discord_id

    delta = None
    if new_data["solvedCount"] > old_data["solvedCount"]:
        delta_index = ['solvedCount', 'tier', 'rating', 'rank']

        delta = new_data[delta_index] - old_data[delta_index]
        delta['solvedProblems'] = find_solved_problem(old_data['solvedProblems'], new_data['solvedProblems'])

    BOJ_users_dataframe.loc[discord_id] = new_data
    return delta


class Solved_ac_user:
    def set_user_info(self):
        # api에서 정보 가져오기
        url = "https://solved.ac/api/v3/user/show"
        querystring = {"handle": self.id}
        headers = {"Content-Type": "application/json"}
        response = requests.request("GET", url, headers=headers, params=querystring)

        if response.status_code == 404: raise BOJIDNotFoundError

        user_json_object = json.loads(response.text)
        self.tier = user_json_object['tier']
        self.rank = user_json_object['rank']
        self.rating = user_json_object['rating']
        self.solved_problem_count = user_json_object['solvedCount']

    def __init__(self, ID):
        self.id = ID
        self.set_user_info()

    def get_user_info(self):
        return {
            "id": self.id,
            "tier": Tier_list[self.tier],
            "rank": self.rank,
            "rating": self.rating,
        }

    def Reset_user_info(self):
        variances = {}

        # api에서 정보 가져오기
        url = "https://solved.ac/api/v3/user/show"
        querystring = {"handle": self.id}
        headers = {"Content-Type": "application/json"}
        response = requests.request("GET", url, headers=headers, params=querystring)

        if response.status_code == 404: raise BOJIDNotFoundError

        try:
            user_json_object = response.json()
        except:
            print("Json 변환 오류")
            return {'tier': 0, 'rank': 0, 'rating': 0, 'solved_count': 0}

        variances['tier'] = user_json_object['tier'] - self.tier
        self.tier = user_json_object['tier']

        variances['rank'] = user_json_object['rank'] - self.rank
        self.rank = user_json_object['rank']

        variances['rating'] = user_json_object['rating'] - self.rating
        self.rating = user_json_object['rating']

        variances['solved_count'] = user_json_object['solvedCount'] - self.solved_problem_count
        self.solved_problem_count = user_json_object['solvedCount']

        return variances
