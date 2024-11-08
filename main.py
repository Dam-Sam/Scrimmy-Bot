import discord
from discord.ext import commands
from discord.ext.commands import Greedy
from discord import app_commands
from dotenv import load_dotenv
import random
import json
import os

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
DATA = {}

class Bot(commands.Bot):
    async def on_ready(self):
        print(f'{self.user} is here!!!!!!')

        with open('data.json', 'r') as json_file:
            DATA.update(json.load(json_file))

        # try:
        #     guild = discord.Object(id=GUILD_ID)
        #     synced = await self.tree.sync(guild=guild)
        #     print(f'Synced {len(synced)} commands to guild {GUILD_ID}')
        # except Exception as e:
        #     print(f'Error Syncing commands: {e}')

    async def on_message(self, message):
        if message.author == self.user:
            return
        
        if message.content.startswith('hello'):
            await message.channel.send(f'Hello {message.author}')
        
        await self.process_commands(message)
        


intents = discord.Intents.default()
intents.message_content = True
Bot = Bot(command_prefix="!", intents=intents)
guild = discord.Object(id=GUILD_ID)

# @Bot.event
# async def on_command_error(ctx, error):
#     if isinstance(error, commands.BadArgument):
#         await ctx.send("Oops! Bad Argument. Please check your command and try again.")
#     else:
#         print(f'Ignoring exception in command {ctx.command}:')

def is_in_guild(ctx):
    return ctx.guild and ctx.guild.id == GUILD_ID

@Bot.tree.command(name="hello", description="Says Hello", guild=guild)
async def sayHello(interaction: discord.Interaction):
    await interaction.response.send_message("Hi There!")


@Bot.command(name="echo")
async def echo(ctx, *args):
    # Join the *args tuple into a single string
    message = " ".join(args)
    print(message)
    await ctx.send(message)


@Bot.command(name="register")
@commands.check(is_in_guild)
@commands.has_role("referee")
async def register_to_leaderboard(ctx, *members: discord.Member):
    for member in members:
        id = str(member.id)
        if id not in DATA:
            DATA[id] = 0
        else:
            print(f'User: {member}, ID: {id} already exists in the database')
    
    with open('data.json', 'w') as json_file:
        json.dump(DATA, json_file)
    
    await ctx.send("Done!")
    return


@Bot.command(name="clear")
@commands.check(is_in_guild)
@commands.has_role("referee")
async def clear_leaderboard(ctx):
    try:
        DATA.clear()

        with open('data.json', 'w') as json_file:
            json.dump(DATA, json_file)
        
        await ctx.send("Cleared Leaderboard")
    except Exception as e:
        print(f'Error clearing leaderboard: {e}')

    return


@Bot.command(name="score")
@commands.check(is_in_guild)
@commands.has_role("referee")
async def change_score(ctx, members: Greedy[discord.Member], score: int):
    nonregistered = []
    
    for member in members:
        id = str(member.id)
        if id not in DATA:
            nonregistered.append(member)
    
    if nonregistered:
        embed = discord.Embed(title="❌FAILED: Following Members Are Not Registered❌", color=discord.Color.red())

        for member in nonregistered:
            embed.add_field(
                name=f"{member}",
                value="",
                inline=False
            )
        
        await ctx.send(embed=embed)

    else:
        for member in members:
            DATA[str(member.id)] = max(0, DATA[str(member.id)] + score)
        
        with open('data.json', 'w') as json_file:
            json.dump(DATA, json_file)
    return


@Bot.command(name="leaderboard")
@commands.check(is_in_guild)
@commands.has_role("referee")
async def display_leaderboard(ctx):
    sorted_data = sorted(DATA.items(), key=lambda item: item[1], reverse=True)  
    len_sorted = len(sorted_data) 

    embed = discord.Embed(title="🏆 Leaderboard 🏆", color=discord.Color.gold())
    embed.set_footer(text="Top 10 Players")

    for i in range(10):
        if i > len_sorted - 1:
            embed.add_field(
                name="",
                value="",
                inline=False  # Each entry on a new line
            )
        elif i==0:
            user = await Bot.fetch_user(int(sorted_data[i][0]))
            embed.add_field(
                name="",
                value=f"🥇 **{user.global_name}: {sorted_data[i][1]} Points**",
                inline=False  # Each entry on a new line
            )
        elif i==1:
            user = await Bot.fetch_user(int(sorted_data[i][0]))
            embed.add_field(
                name="",
                value=f"**🥈 {user.global_name}: {sorted_data[i][1]} Points**",
                inline=False  # Each entry on a new line
            )
        elif i==2:
            user = await Bot.fetch_user(int(sorted_data[i][0]))
            embed.add_field(
                name="",
                value=f"**🥉 {user.global_name}: {sorted_data[i][1]} Points**",
                inline=False  # Each entry on a new line
            )
        else:
            user = await Bot.fetch_user(int(sorted_data[i][0]))
            embed.add_field(
                name="",
                value=f"{i+1}th Place - **{user.global_name}**: {sorted_data[i][1]} Points",
                inline=False  # Each entry on a new line
            )

    await ctx.send(embed=embed)
    return


@Bot.command(name="secretsanta")
async def secret_santa(ctx, members: Greedy[discord.Member], budget: int):
    if len(members) < 2:
        await ctx.send("You need atleast two members for Secret Sanata")
        return
    
    recipients = members.copy()
    random.shuffle(recipients)

    for i in range(len(members)):
        # If a giver is assigned to themselves, reshuffle the recipients list
        if members[i] == recipients[i]:
            random.shuffle(recipients)
            i = 0  # Restart checking to ensure no one is assigned to themselves

    try:
        for member, recipient in zip(members, recipients):
            await member.send(f"🎄 Secret Santa! 🎅 You are assigned to give a gift to **{recipient.display_name}** with the budget of ${budget}.")
        
        await ctx.send("Secret Santa assignments have been sent to each participant!")
    
    except Exception as e:
            print(f'Error sending dms: {e}')


Bot.run(BOT_TOKEN)