import discord
from discord import app_commands
from discord.ext import commands
from akinator.async_aki import Akinator
import aiohttp

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
aki = Akinator()

games = {}

@bot.event
async def on_ready():
    print(f"Bot起動成功: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"スラッシュコマンド同期完了 ({len(synced)} 個)")
    except Exception as e:
        print("同期失敗:", e)

@bot.tree.command(name="start", description="アキネーターを開始します")
async def start(interaction: discord.Interaction):
    await interaction.response.defer()

    if interaction.user.id in games:
        await interaction.followup.send("⚠️ すでにゲームが進行中です。")
        return

    try:
        q = await aki.start_game(language="ja")  # または "en"（安定性優先）
    except Exception as e:
        await interaction.followup.send(f"❌ ゲーム開始失敗: {type(e).__name__} - {e}")
        return

    games[interaction.user.id] = aki

    view = AkinatorView(interaction.user)
    await interaction.followup.send(f"🧞 Q1: {aki.question}", view=view)


class AkinatorView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=60)
        self.user = user
        self.answer_map = {
            "はい": "yes",
            "いいえ": "no",
            "分からない": "idk",
            "多分そう": "probably",
            "多分違う": "probably not"
        }
        for label in self.answer_map:
            self.add_item(AkinatorButton(label, self.answer_map[label]))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id


class AkinatorButton(discord.ui.Button):
    def __init__(self, label: str, answer: str):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.answer = answer

    async def callback(self, interaction: discord.Interaction):
        aki = games.get(interaction.user.id)
        if not aki:
            await interaction.response.send_message("❌ ゲームが見つかりません。", ephemeral=True)
            return

        try:
            await aki.answer(self.answer)
        except Exception as e:
            await interaction.response.send_message(f"エラー: {e}", ephemeral=True)
            return

        if aki.progression >= 80:
            await aki.win()
            img_url = aki.first_guess['absolute_picture_path']
            embed = discord.Embed(
                title=f"あなたが思い浮かべていたのは… {aki.first_guess['name']} ですか？",
                description=aki.first_guess['description'],
                color=discord.Color.blue()
            )
            if img_url:
                embed.set_image(url=img_url)
            else:
                embed.set_thumbnail(url="https://i.imgur.com/BVY6ZtN.png")  # fallback画像

            await interaction.response.edit_message(embed=embed, view=None)
            games.pop(interaction.user.id, None)
        else:
            view = AkinatorView(interaction.user)
            await interaction.response.edit_message(content=f"🧞 Q: {aki.question}", view=view)


@bot.tree.command(name="stop", description="進行中のアキネーターを終了します")
async def stop(interaction: discord.Interaction):
    if interaction.user.id not in games:
        await interaction.response.send_message("⚠️ 現在進行中のゲームはありません。", ephemeral=True)
        return
    games.pop(interaction.user.id, None)
    await interaction.response.send_message("🛑 ゲームを終了しました。", ephemeral=True)


import os
TOKEN = os.getenv("TOKEN")  # Railwayの環境変数に TOKEN を設定しておく
bot.run(TOKEN)
