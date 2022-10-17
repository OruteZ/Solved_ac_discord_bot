import discord
from discord.ext import commands

# 반복 작업을 위한 패키지
from discord.ext import tasks
# 딜레이 걸어서 부담 줄이는 용도
import asyncio
# solved ac 정보 가져오기
from database_api import *
# 유저정보를 관리할 용도의 라이브러리 pandas
import pandas as pd

client = discord.Client()

# base command prefix is !
bot = commands.Bot(command_prefix='!')
TOKEN = 'OTUyNjE2MzA2MDk0NTI2NTY1.Yi4nEg.-Qsh-SzlXq2EM-4kDnmOiHxqt9g'

users = {}  # 백준 유저들을 등록 해 두는 딕셔너리. 디스코드id : boj_player객체
Tier_color = {
    "Unrated": 0X444444,
    "Bronze": 0XD2691E,
    "Silver": 0XE6E6FA,
    "Gold": 0XFFA500,
    "Platinum": 0X33FFCC,
    "Diamond": 0X00FFFF,
    "Ruby": 0XFF0000,
    "Master": 0XCC00FF
}

# 봇이 주기적으로 알림을 보낼 때 사용하는 채널
alert_guild_id = 953192501806780426
alert_textChannel_id = 970369107214094488


class boj_player:
    def __init__(self, _dscUser):
        print(f"setUser : {_dscUser}")
        self.today_boj_solved = False
        self.dscUser = _dscUser
        self.boj_profile = None

    def setBOJ(self, bojID):
        print(f"set BOJ {bojID}")
        self.boj_profile = Solved_ac_user(bojID)


# {디스코드 id : 백준 id}의 딕셔너리 형식으로 csv파일 저장
def backup():
    user_data_frame = pd.DataFrame(
        {
            "discord_id": users.keys(),
            "boj_id": list(map(lambda a: a.boj_profile.id, users.values()))
        }
    )
    print("backup user info")
    print(user_data_frame)

    user_data_frame.to_csv("backup.csv")


# 주기적으로 해야 할 일들
@tasks.loop(seconds=1)
async def periodical_work(alert_channel=None):
    print("periodical_work")
    # 1. 각 유저 정보 갱신
    for dsc_id in users.keys():
        player = users[dsc_id]
        player_boj = player.boj_profile
        player_dsc = player.dscUser

        changed = player_boj.Reset_user_info()

        if changed['solved_count'] > 0:
            embed = discord.Embed(
                color=Tier_color[(player_boj.get_user_info()['tier'].split())[0]],
                title=f"{player_dsc} solved problem",
                url=f"https://solved.ac/profile/{player_boj.id}"
            )
            embed.add_field(name='> 해결한 문제', value='`' + str(changed['solved_count']) + '개`', inline=True)
            embed.add_field(name='> 레이팅', value='`+' + str(changed['rating']) + '`', inline=True)
            embed.add_field(name='> 랭킹', value='`+' + str(changed['rank']) + '`', inline=True)
            await alert_channel.send(embed=embed)

        if changed['tier'] > 0:
            embed = discord.Embed(
                color=Tier_color[list(player_boj.get_user_info()['tier'].split())[0]],
                title=f"{player_dsc}의 티어가 {changed['tier']}단계 상승했습니다!",
                url=f"https://solved.ac/profile/{player_boj.id}"
            )
            await alert_channel.send(embed=embed)


@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("개발"))
    print("유저 정보 로딩 중. . .")
    if not adding_user_info:
        try:
            user_info = pd.read_csv("backup.csv", sep=',')
        except pd.errors.EmptyDataError:
            return

        print(user_info)
        dsc_id_series = user_info['discord_id']
        boj_id_series = user_info['boj_id']

        for info in zip(dsc_id_series, boj_id_series):
            member = await bot.get_guild(alert_guild_id).fetch_member(info[0])
            u = boj_player(member)

            try:
                u.setBOJ(info[1])
            except BOJIDNotFoundError:
                print(f"Error : 아이디 : {info[1]}를 solved.ac 페이지에서 찾을 수 없음.")
                continue

            users[info[0]] = u
    print('[알림][봇이 정상적으로 구동되었습니다.]')
    update_user_info.start()


# 주기적으로 해야 할 일들

# 1. 각 유저 정보 갱신
@tasks.loop(seconds=5)
async def update_user_info():
    if adding_user_info: return
    print("update_user_info")

    alert_channel = bot.get_channel(alert_textChannel_id)
    for dsc_id in users.keys():
        player = users[dsc_id]
        player_boj = player.boj_profile
        player_dsc = player.dscUser

        changed = player_boj.Reset_user_info()

        if changed['solved_count'] > 0:
            embed = discord.Embed(
                color=Tier_color[(player_boj.get_user_info()['tier'].split())[0]],
                title=f"{player_dsc} solved problem",
                url=f"https://solved.ac/profile/{player_boj.id}"
            )
            embed.add_field(name='> 해결한 문제', value='`' + str(changed['solved_count']) + '개`', inline=True)
            embed.add_field(name='> 레이팅', value='`+' + str(changed['rating']) + '`', inline=True)
            embed.add_field(name='> 랭킹', value='`' + str(changed['rank']) + '`', inline=True)
            await alert_channel.send(embed=embed)

        if changed['tier'] > 0:
            embed = discord.Embed(
                color=Tier_color[list(player_boj.get_user_info()['tier'].split())[0]],
                title=f"{player_dsc}의 티어가 {changed['tier']}단계 상승했습니다!",
                url=f"https://solved.ac/profile/{player_boj.id}"
            )
            info = player_boj.get_user_info()
            embed.add_field(name='> 티어', value='`' + info['tier'] + '`', inline=True)
            embed.add_field(name='> 레이팅', value='`' + str(info['rating']) + '`', inline=True)
            embed.add_field(name='> 랭킹', value='`' + str(info['rank']) + '`', inline=True)
            await alert_channel.send(embed=embed)


@bot.event
async def on_message(msg):
    if msg.author.bot: return None
    await bot.process_commands(msg)


@bot.command()
async def 반복(ctx, message):
    await ctx.send(message)


adding_user_info = False


@bot.command()
async def 유저등록(ctx, message, discord_id=None):
    global adding_user_info
    adding_user_info = True

    if discord_id is None:
        discord_id = ctx.author
    else:
        mentioned_members = ctx.message.mentions
        if mentioned_members == []:
            discord_id = ctx.author
        else:
            discord_id = mentioned_members[0]

    if users.get(discord_id.id) is not None:
        await ctx.send(f"이미 solved.ac 계정 '{users.get(discord_id.id).boj_profile.id}'에 연동 되어 있습니다.\n연동 계정을 변경합니다.")

    u = boj_player(discord_id)

    try:
        u.setBOJ(message)
    except BOJIDNotFoundError:
        await ctx.send(f"Error : 아이디 : {message}를 solved.ac 페이지에서 찾을 수 없음.")
        return

    users[discord_id.id] = u

    backup()

    info = u.boj_profile.get_user_info()

    adding_user_info = False

    tier_color = Tier_color[list(info['tier'].split())[0]]
    embed = discord.Embed(color=tier_color, title=f"PROFILE : {info['id']}",
                          url=f"https://solved.ac/profile/{info['id']}")
    embed.add_field(name='> 티어', value='`' + info['tier'] + '`', inline=True)
    embed.add_field(name='> 레이팅', value='`' + str(info['rating']) + '`', inline=True)
    embed.add_field(name='> 랭킹', value='`' + str(info['rank']) + '`', inline=True)
    embed.set_footer(text=f"{discord_id} 1일1백준에 합류하신걸 환영합니다")

    await ctx.send("등록 완료\n", embed=embed)


@bot.command()
async def 랜덤백준(ctx, tier='', tags=''):
    tags = list(tags.split(',')) if tags != '' else []

    problem = BOJ_random_defense(Tier=tier, tags=tags)
    if problem is None:
        await ctx.send("문제가 검색되지 않았습니다, 티어랑 태그가 너무 깐깐한거 아니에요?")
        return

    embed = discord.Embed(
        color=Tier_color[list(Tier_list[problem['level']].split())[0]],
        title=f"{problem['problemId']}번 : {problem['titleKo']}",
        url=f"https://www.acmicpc.net/problem/{problem['problemId']}",
    )
    embed.add_field(name='> 티어', value='`' + Tier_list[problem['level']] + '`', inline=True)

    await ctx.send(embed=embed)


bot.run(TOKEN)
