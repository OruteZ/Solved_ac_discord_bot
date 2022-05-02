import requests
import json
import random

#해당 태그가 존재하는지 확인하는 함수, 반환값 : True or False
def is_tag_available(tag):
   url = "https://solved.ac/api/v3/search/tag"
   querystring = {"query": "#"+tag, "page": "1"}
   headers = {"Content-Type": "application/json"}
   response = requests.request("GET", url, headers=headers, params=querystring)
   JSON = json.loads(response.text)
   return JSON['count'] != 0


def BOJ_random_defense(Tier = '', Tag = []):
   print("random Boj call")

   query = "s#100.. "

   if(Tier != '') : query += f"*{Tier} "

   for tag in Tag:
      if(is_tag_available(tag)) : query += "#" + tag + " "

   print(f"query = {query}")

   page = 1
   url = "https://solved.ac/api/v3/search/problem"
   querystring = {"query" : query, "page": str(page), "sort": "solved", "direction": "desc"}
   headers = {"Content-Type": "application/json"}
   response = requests.request("GET", url, headers=headers, params=querystring)

   problems_json_object = json.loads(response.text)

   problems = problems_json_object['items']


   #만약 해당 문제가 없을경우, 최소 100명 풀이 제한 제거 후 다시 탐색
   if problems==[] :
      query = ""

      if (Tier != ''): query += f"*{Tier} "

      for tag in Tag:
         if (is_tag_available(tag)): query += "#" + tag + " "

      print(f"query = {query}")

      page = 1
      url = "https://solved.ac/api/v3/search/problem"
      querystring = {"query": query, "page": str(page), "sort": "solved", "direction": "desc"}
      headers = {"Content-Type": "application/json"}
      response = requests.request("GET", url, headers=headers, params=querystring)

      problems_json_object = json.loads(response.text)

      problems = problems_json_object['items']

   return None if problems==[] else random.choice(problems)






class Solved_ac_user : pass

Tier_list = [
   "Unrated",
   "Bronze V","Bronze IV","Bronze III","Bronze II","Bronze I",
   "Silver V","Silver IV","Silver III","Silver II","Silver I",
   "Gold V","Gold IV","Gold III","Gold II","Gold I",
   "Platinum V","Platinum IV","Platinum III","Platinum II","Platinum I",
   "Diamond V","Diamond IV","Diamond III","Diamond II","Diamond I",
   "Ruby V","Ruby IV","Ruby III","Ruby II","Ruby I",
   "Master"
]

class BOJIDNotFoundError(Exception):
   def __init__(self):
      super().__init__('해당 BOJ ID를 SolvedAc에서 찾을 수 없음')

class Solved_ac_user:
   def set_user_info(self):
      # api에서 정보 가져오기
      url = "https://solved.ac/api/v3/user/show"
      querystring = {"handle": self.id}
      headers = {"Content-Type": "application/json"}
      response = requests.request("GET", url, headers=headers, params=querystring)

      if(response.status_code == 404) : raise BOJIDNotFoundError

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

   """
   해당 백준 계정의 정보를 갱신하고, 변화량을 딕셔너리로 전달
   
   """
   def Reset_user_info(self):
      variances = {}

      # api에서 정보 가져오기
      url = "https://solved.ac/api/v3/user/show"
      querystring = {"handle": self.id}
      headers = {"Content-Type": "application/json"}
      response = requests.request("GET", url, headers=headers, params=querystring)

      if (response.status_code == 404): raise BOJIDNotFoundError

      try:
         user_json_object = json.loads(response.text)
      except:
         print("Json 변환 오류")
         return {'tier' : 0, 'rank' : 0, 'rating' : 0, 'solved_count' : 0}

      variances['tier'] = user_json_object['tier'] - self.tier
      self.tier = user_json_object['tier']

      variances['rank'] = user_json_object['rank'] - self.rank
      self.rank = user_json_object['rank']

      variances['rating'] = user_json_object['rating'] - self.rating
      self.rating = user_json_object['rating']

      variances['solved_count'] = user_json_object['solvedCount'] - self.solved_problem_count
      self.solved_problem_count = user_json_object['solvedCount']

      return variances




