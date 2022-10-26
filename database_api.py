import pandas as pd
import numpy as np
import requests
import json
import random
import time


class BOJIDNotFoundError(Exception):
    def __init__(self):
        super().__init__('해당 BOJ ID를 Solved.Ac 에서 찾을 수 없음')


class TooManyRequestsError(Exception):
    def __init__(self):
        super().__init__('API request가 너무 많아 잠시 휴식 중. . . ')


BOJ_users_dataframe = pd.DataFrame()


def string2list(target):
    if target == '[]': return []
    if type(target) == list: return target

    target = target[2:-2]
    return list(map(int, target.split(',')))


def load_BOJ_dataframe():
    global BOJ_users_dataframe

    try:
        BOJ_users_dataframe = pd.read_csv("BOJ_DB.csv", sep=',', index_col=0)
    except pd.errors.EmptyDataError:
        cname = ['handle', 'bio', 'organizations', 'badge', 'background',
                 'profileImageUrl', 'solvedCount', 'voteCount', 'class',
                 'classDecoration', 'tier', 'rating', 'ratingByProblemsSum',
                 'ratingByClass', 'ratingBySolvedCount', 'ratingByVoteCount', 'exp',
                 'rivalCount', 'reverseRivalCount', 'maxStreak', 'proUntil', 'rank', 'solvedProblems']
        BOJ_users_dataframe = pd.DataFrame(columns=cname)

        BOJ_users_dataframe.set_index('handle')


load_BOJ_dataframe()


# return True if tag is available else False
def is_tag_available(tag):
    print('requests')

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
def get_user_data(boj_id, reset=False, get_solved_prob=False):
    if boj_id in BOJ_users_dataframe.index and not reset:
        return BOJ_users_dataframe.loc[boj_id]

    print('requests get user data :', boj_id)

    url = "https://solved.ac/api/v3/user/show"
    querystring = {"handle": boj_id}
    headers = {"Content-Type": "application/json"}
    response = requests.request("GET", url, headers=headers, params=querystring)

    if response.status_code == 404: raise BOJIDNotFoundError
    if response.text == 'Too Many Requests': raise TooManyRequestsError

    user_info = response.json()

    if get_solved_prob: user_info['solvedProblems'] = get_solved_problems(boj_id)

    return pd.Series(user_info)


# Get all problems that user solved by list
def get_solved_problems(boj_id):
    """
    get all problems that user solved
    :param boj_id: users name
    :return: id of problems by list
    """
    print('requests')

    url = "https://solved.ac/api/v3/search/problem"
    headers = {"Content-Type": "application/json"}

    solved_problem_list = []
    page = 1
    while True:
        querystring = {"query": "@" + boj_id, "page": page, "sort": "id", "direction": "asc"}
        response = requests.request("GET", url, headers=headers, params=querystring)

        if response.status_code == 404: raise BOJIDNotFoundError
        if response.text == 'Too Many Requests': raise TooManyRequestsError

        lists = list(map(lambda item: item['problemId'], json.loads(response.text)['items']))
        if not lists: break
        solved_problem_list += lists
        page += 1
    return solved_problem_list


def add_user_data(boj_id):
    """
    add user by backjoon online judge id

    :param boj_id: backjoon online judge name
    :return: False is boj_id no exist else True
    """
    if boj_id in BOJ_users_dataframe.index: return True

    try:
        user_info = get_user_data(boj_id, reset=True, get_solved_prob=True)
    except BOJIDNotFoundError:
        return False
    BOJ_users_dataframe.loc[boj_id] = user_info
    return True


def remove_user_data(boj_id):
    BOJ_users_dataframe.drop(labels=boj_id, inplace=True)


def find_solved_problem(old_problems, new_problems):
    old_problems = string2list(old_problems)
    return list(set(new_problems).difference(old_problems))


def backup_BOJ_dataframe(): BOJ_users_dataframe.to_csv("BOJ_DB.csv")


def reset_user_data(boj_id):
    """
    reset user data by boj id

    :param boj_id: backjoon online judge name
    :return: delta of changed values by Series ('solvedCount', 'tier', 'rating', 'rank', 'solvedProblems')
    """
    if boj_id not in BOJ_users_dataframe.index: return None

    old_data = get_user_data(boj_id, reset=False)
    new_data = get_user_data(boj_id, reset=True, get_solved_prob=False)

    # print(old_data)
    # print(new_data)

    delta = None
    if new_data["solvedCount"] > old_data["solvedCount"]:
        new_data['solvedProblems'] = get_solved_problems(boj_id)

        delta_index = ['solvedCount', 'tier', 'rating', 'rank']

        delta = new_data[delta_index] - old_data[delta_index]
        delta['solvedProblems'] = find_solved_problem(old_data['solvedProblems'], new_data['solvedProblems'])
    else:
        new_data['solvedProblems'] = old_data['solvedProblems']
    BOJ_users_dataframe.loc[boj_id, :] = new_data
    return delta


def get_problem_data(problem_id):
    url = "https://solved.ac/api/v3/problem/show"
    querystring = {"problemId": problem_id}
    headers = {"Content-Type": "application/json"}
    response = requests.request("GET", url, headers=headers, params=querystring)

    if response.status_code == 404: raise BOJIDNotFoundError

    problem_data = response.json()
    return pd.Series(problem_data)


def delete_user_data(boj_id):
    if boj_id not in BOJ_users_dataframe.index:
        raise BOJIDNotFoundError

    BOJ_users_dataframe.drop(index=boj_id, inplace=True, axis=0)


def get_BOJ_dataframe_index():
    return BOJ_users_dataframe.index
