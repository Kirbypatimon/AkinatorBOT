import discord
from discord import app_commands
from discord.ext import commands
import akinator
import os

# 環境変数の確認とログ出力
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("❌ TOKENが設定されていません！RailwayのVariablesにTOKENを追加してください。")
    exit()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree
aki_sessions = {}

@bot.event
async def on_ready():
    print(f"✅ ログイン成功: {bot.user}")
    try:
        synced = await tree.sync()
        print(f"✅ スラッシュコマンド同期完了: {len(synced)} 件")
    except Exception as e:
        print(f"❌ コマンド同期エラー: {e}")

@tree.command(name="start", description="アキネーターを開始します")
async def start(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🧠 アキネーターを始めます！回答は「はい」「いいえ」「わからない」「多分」「多分違う」のどれかを送ってね。",
        ephemeral=False
    )

    aki = akinator.Akinator()
    aki_sessions[interaction.user.id] = aki

    try:
        q = aki.start_game()
    except Exception as e:
        await interaction.followup.send(f"❌ ゲーム開始失敗: {e}")
        return

    await interaction.followup.send(f"Q1: {q}")

    def check(m):
        return m.author.id == interaction.user.id and m.channel == interaction.channel

    question_count = 1
    while aki.progression <= 80:
        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
        except:
            await interaction.followup.send("⌛ タイムアウトしました。もう一度 `/start` してください。")
            return

        user_input = msg.content.lower()
        if user_input not in ["はい", "いいえ", "わからない", "多分", "多分違う"]:
            await msg.channel.send("⚠️ 有効な返答を入力してください：「はい」「いいえ」「わからない」「多分」「多分違う」")
            continue

        try:
            q = aki.answer(user_input)
            question_count += 1
            await msg.channel.send(f"Q{question_count}: {q}")
        except akinator.AkiNoQuestions:
            break
        except Exception as e:
            await msg.channel.send(f"❌ エラーが発生しました: {e}")
            return

    try:
        aki.win()
        embed = discord.Embed(
            title=f"🎯 あなたが思い浮かべているのは… {aki.first_guess['name']}？",
            description=aki.first_guess['description'],
            color=discord.Color.gold()
        )
        embed.set_image(url=aki.first_guess['absolute_picture_path'])
        await msg.channel.send(embed=embed)
    except Exception as e:
        await msg.channel.send(f"❌ 結果の取得に失敗しました: {e}")

# 実行開始
try:
    print("🔄 BOTを起動中…")
    bot.run(TOKEN)
except Exception as e:
    print(f"❌ 起動時エラー: {e}")
