import os

import discord
# 유저정보를 관리할 용도의 라이브러리 pandas
from discord.ext import commands
# 반복 작업을 위한 패키지
from discord.ext import tasks
import database_api as db
import pandas as pd

intent = discord.Intents(value=3181056)

client = discord.Client(intents=intent)

# base command prefix is !
bot = commands.Bot(command_prefix='/', intents=intent)
TOKEN = os.environ['TOKEN']

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

user_dataframe = pd.DataFrame()


def load_dataframe():
    global user_dataframe

    db.load_BOJ_dataframe()
    try:
        user_dataframe = pd.read_csv("User_DB.csv", sep=',', index_col=0)
        print(user_dataframe)
    except pd.errors.EmptyDataError:
        cname = ['user_id', 'guild_id', 'text_channel_id', 'boj_id']
        user_dataframe = pd.DataFrame(columns=cname)
        user_dataframe.set_index('user_id')


def backup_dataframe():
    db.backup_BOJ_dataframe()
    user_dataframe.to_csv("User_DB.csv")


def user_embed(boj_id):
    user_data_series = db.get_user_data(boj_id)

    embed = discord.Embed(
        color=Tier_color[Tier_list[user_data_series['tier']].split()[0]],
        title=f"BOJ_Player : {boj_id}",
        url=f"https://solved.ac/profile/{boj_id}"
    )
    embed.add_field(name='> 티어', value='`' + Tier_list[user_data_series['tier']] + '`')
    embed.add_field(name='> 레이팅', value='`' + str(user_data_series['rating']) + '`')
    embed.add_field(name='> 랭킹', value='`' + str(user_data_series['rank']) + '`')
    return embed


def problem_embed(problem_id):
    problem_data = db.get_problem_data(problem_id)
    # 필요한 데이터
    # 1. 티어, 2. 레이팅 증가량, 3. 태그, 4. 이름

    problem_name = problem_data['titleKo']
    problem_tier = Tier_list[problem_data['level']]
    problem_tags = [i['displayNames'][0]['name'] for i in problem_data['tags']]

    embed = discord.Embed(
        color=Tier_color[(problem_tier.split())[0]],
        title=f"{problem_id} : {problem_name}",
        url=f"https://www.acmicpc.net/problem/{problem_id}"
    )
    embed.add_field(name='> Tier', value='`' + problem_tier + '`')
    embed.add_field(name='> Tags', value='`' + ','.join(problem_tags) + '`')

    return embed


@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("개발"))
    print("유저 정보 로딩 중. . .")
    load_dataframe()
    print('[알림][봇이 정상적으로 구동되었습니다.]')

    update_user_data.start()


@tasks.loop(seconds=5)
async def update_user_data():
    print("update_user_info")

    discord_user_id_list = list(set(user_dataframe.index))
    for dsc_user_id in discord_user_id_list:
        discord_user = await bot.fetch_user(dsc_user_id)

        df = user_dataframe[user_dataframe.index == dsc_user_id]

        boj_id = df['boj_id'].values[0]
        channels_id = df['text_channel_id'].tolist()
        delta = db.reset_user_data(boj_id)

        if delta is None: continue
        await bot.wait_until_ready()
        print("solved alert")
        print(delta)

        if delta['solvedCount'] == 1:
            for idx in range(df.shape[0]):
                if not delta['solvedProblems']: continue
                # guild = await bot.fetch_guild(guilds_id[idx])
                # print(guild.name)
                channel = await bot.fetch_channel(channels_id[idx])
                await channel.send(f"{discord_user.mention} solved problem {delta['solvedProblems'][0]}"
                                   , embed=problem_embed(delta['solvedProblems'][0]))

    backup_dataframe()

    """,
        if changed['solved_count'] > 0:
            embed = discord.Embed(
                color=Tier_color[(player_boj.get_user_info()['tier'].split())[0]],
                title=f"{player_dsc} solved problem",
                url=f"https://solved.ac/profile/{player_boj.id}"
            )
            embed.add_field(name='> 해결한 문제', value='`' + str(changed['solved_count']) + '개`')
            embed.add_field(name='> 레이팅', value='`+' + str(changed['rating']) + '`')
            embed.add_field(name='> 랭킹', value='`' + str(changed['rank']) + '`')
            await alert_channel.send(embed=embed)

        if changed['tier'] > 0:
            embed = discord.Embed(
                color=Tier_color[list(player_boj.get_user_info()['tier'].split())[0]],
                title=f"{player_dsc}의 티어가 {changed['tier']}단계 상승했습니다!",
                url=f"https://solved.ac/profile/{player_boj.id}"
            )
            info = player_boj.get_user_info()
            embed.add_field(name='> 티어', value='`' + info['tier'] + '`')
            embed.add_field(name='> 레이팅', value='`' + str(info['rating']) + '`')
            embed.add_field(name='> 랭킹', value='`' + str(info['rank']) + '`')
            await alert_channel.send(embed=embed)
    """


@bot.event
async def on_message(msg):
    if msg.author.bot: return None
    await bot.process_commands(msg)


@bot.command()
async def repeat(ctx, message):
    await ctx.send(message)


@bot.command()
async def 등록(ctx, boj_id, discord_user=None):
    global user_dataframe

    if discord_user is None:
        discord_user = ctx.author
    else:
        mentioned_members = ctx.message.mentions
        if not mentioned_members:
            discord_user = ctx.author
        else:
            discord_user = mentioned_members[0]

    user_id = discord_user.id
    guild_id = ctx.guild.id
    channel_id = ctx.channel.id

    success = db.add_user_data(boj_id)
    if not success:
        await ctx.channel.send(f"Error : 아이디 : {boj_id}를 solved.ac 페이지에서 찾을 수 없음.")
        return

    old_user_df = user_dataframe[user_dataframe.index == user_id]

    if not old_user_df.empty:
        old_boj_id = old_user_df.iloc[0]["boj_id"]

        if old_boj_id != boj_id:
            await ctx.send(f"이미 solved.ac 계정 '{old_boj_id}'에 연동 되어 있습니다.\n연동 계정을 변경합니다.")

            user_dataframe.loc[user_id, "boj_id"] = boj_id
        else:
            await ctx.send(f"이미 solved.ac 계정 '{old_boj_id}'에 연동 되어 있습니다.")

    new_user_series = pd.Series({
        'user_id': user_id,
        'guild_id': guild_id,
        'text_channel_id': channel_id,
        'boj_id': boj_id
    }, name=user_id)

    if list(filter(lambda i: old_user_df.loc[i].equals(new_user_series), old_user_df.index)):
        return

    user_dataframe = user_dataframe.append(new_user_series)

    print(user_dataframe)
    backup_dataframe()

    await ctx.send("등록 완료\n", embed=user_embed(boj_id))


@bot.command()
async def profile(ctx, boj_id):
    await ctx.send(embed=user_embed(boj_id))


bot.run(token=TOKEN)
