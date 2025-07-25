import discord
from discord.ext import commands
from akinator import Akinator

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='/', intents=intents)

games = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command(name='start')
async def start(ctx):
    if ctx.author.id in games:
        await ctx.send("❌ すでにゲームが進行中です！")
        return

    aki = Akinator()
    games[ctx.author.id] = aki

    try:
        q = await aki.start_game(language='ja')
        await ctx.send(f"🎮 アキネーターゲーム開始！\n\n**{q}**\n\n(はい/いいえ/わからない/たぶん/たぶん違う)")
    except Exception as e:
        del games[ctx.author.id]
        await ctx.send(f"❌ ゲーム開始失敗: {str(e)}")

@bot.command(name='end')
async def end(ctx):
    if ctx.author.id in games:
        del games[ctx.author.id]
        await ctx.send("🛑 ゲームを終了しました。")
    else:
        await ctx.send("❌ ゲームは開始されていません。")

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author.bot:
        return

    if message.author.id not in games:
        return

    aki = games[message.author.id]
    answer_map = {
        "はい": "yes",
        "いいえ": "no",
        "わからない": "idk",
        "たぶん": "probably",
        "たぶん違う": "probably not"
    }

    answer = answer_map.get(message.content.lower())
    if not answer:
        await message.channel.send("❓ 有効な回答: はい / いいえ / わからない / たぶん / たぶん違う")
        return

    try:
        q = await aki.answer(answer)

        if aki.progression > 80:
            await aki.win()
            embed = discord.Embed(
                title=f"🤖 アキネーターの予想: {aki.first_guess['name']}",
                description=aki.first_guess['description'],
                color=discord.Color.blue()
            )
            embed.set_image(url=aki.first_guess['absolute_picture_path'])
            await message.channel.send(embed=embed)
            del games[message.author.id]
        else:
            await message.channel.send(f"❓ {q}")
    except Exception as e:
        del games[message.author.id]
        await message.channel.send(f"❌ エラーが発生しました: {str(e)}")

bot.run("YOUR_DISCORD_BOT_TOKEN")
