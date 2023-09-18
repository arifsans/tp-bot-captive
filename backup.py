import datetime
import discord
import requests
import re
import math
import os
from bs4 import BeautifulSoup
from discord import app_commands, Interaction
import re

discord_token = os.environ['DISCORD_TOKEN']
my_guild = discord.Object(id=os.environ['GUILD_ID'])


class MyClient(discord.Client):
    def __init__(self,*,intents:discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        
    async def setup_hook(self):
        self.tree.copy_global_to(guild=my_guild)
        await self.tree.sync(guild=my_guild)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = MyClient(intents=intents)

@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")

@client.tree.command(description = 'Introduce yourself with name, charname, and guild')
async def introduce(interaction: Interaction, fullname: str, aqwname: str, guild: str):
    if not fullname or not aqwname or not guild:
        await interaction.response.send_message("Datadiri aja kamu kosongin apalagi hati doi 😭")
        return
    
    member = interaction.user
    verifId = 1144684681263075419
    unverifId = 1144680870272303256
    verif = interaction.guild.get_role(verifId)
    unverif = interaction.guild.get_role(unverifId)
    
    print(f"Member {member} melakukan introduce")
    print(f"Melakukan Pemeriksaan Role {verif}")
    print(f"Melakukan Pemeriksaan Role {unverif}")

    if verif:
        if unverif in member.roles:
            await member.remove_roles(unverif)
            
        async for message in interaction.channel.history():
            start = 13
            end = start + len(f"{member.id}")
            previousId = message.content[start:end]
            currentId = str(member.id)
            if previousId == currentId and message.content.startswith("```Halo User"):
               await message.delete()
               break
        
        if guild == "-":
            guild = "Solo Player"
            
        achievements = "0"
        await member.add_roles(verif)
        text = f"Halo User {member.id}\n\nNAMA PANGGILAN    : {fullname.title()}\nNAMA KARAKTER     : {aqwname.title()}\nGUILD             : {guild.title()}"
        response = requests.get(f'https://account.aq.com/CharPage?id={aqwname}')
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            ccid_script = soup.find('script', string=re.compile(r'var ccid = \d+;'))
            if ccid_script:
                ccid_content = ccid_script.string
                ccid_match = re.search(r'var ccid = (\d+);', ccid_content)
                if ccid_match:
                    ccid = int(ccid_match.group(1))

                    # Now make a request to the API endpoint with the obtained ccid
                    badges_url = f"https://account.aq.com/CharPage/Badges?ccid={ccid}"
                    badges_response = requests.get(badges_url)

                    if badges_response.status_code == 200:
                        badges_data = badges_response.json()
                        achievements = f"{len(badges_data)}"
                        
        nickname = f"{aqwname.title()} [{achievements}] | {guild.title()}"
        
        if len(nickname) > 32:
            nickname = f"{aqwname.title()} [{achievements}] | -"
            await interaction.response.send_message(f"```{text}\n\nNama melebihi batas, Nama guild akan disingkat```<@{276681083997650947}>")
        else:
            nickname = nickname
            await interaction.response.send_message(f"```{text}```")
        await member.edit(nick = nickname)
        
    else:
        await interaction.response.send_message("The role verified couldn't be found.")



@client.tree.command(description = 'Calculate TP from your character')
async def calculate(interaction: Interaction, username: str):
    await interaction.response.send_message("```Please wait...```")
    response = requests.get(f'https://account.aq.com/CharPage?id={username}')
    if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Use regular expression to extract the ccid value from JavaScript
                ccid_script = soup.find('script', string=re.compile(r'var ccid = \d+;'))
                if ccid_script:
                    ccid_content = ccid_script.string
                    ccid_match = re.search(r'var ccid = (\d+);', ccid_content)
                    if ccid_match:
                        ccid = int(ccid_match.group(1))

                        # Now make a request to the API endpoint with the obtained ccid
                        inventory_url = f"https://account.aq.com/CharPage/Inventory?ccid={ccid}"
                        inventory_response = requests.get(inventory_url)

                        if inventory_response.status_code == 200:
                            inventory_data = inventory_response.json()
                            
                            target_item_name = "Treasure Potion"
                            target_item_entry = next((item for item in inventory_data if item.get("strName") == target_item_name), None)
                            if target_item_entry:
                                int_count = target_item_entry.get("intCount")
                                await interaction.channel.send(f"```{username.title()} current TP = {int_count} TP```")
                                
                                if int_count >= 1000:
                                    await interaction.channel.send("```Gausah Sok Merendah Puh, Dah Dapet Wioda Itu```")
                                    
                                else:
                                    if int_count < 10:
                                        await interaction.channel.send("```Buset Abis Redeem Wioda Nih```")
                                    if int_count > 900:
                                        await interaction.channel.send("```Bentar Lagi Dapet Wioda Nih```")
                                    target_count = 1000
                                    # Calculate days and ACS for 2X TP/Spin
                                    await calculate_and_send_results(interaction.channel, target_count, int_count, daily_gain=2, weekly_bonus=2, cost_per_potion=200)
                                    
                                    # Calculate days and ACS for 6X TP/Spin
                                    await calculate_and_send_results(interaction.channel, target_count, int_count, daily_gain=6, weekly_bonus=6, cost_per_potion=200)
                                    
                                    await interaction.channel.send("```From Captive with ❤️\nCredit by Zou```")
                                
                            else:
                                await interaction.channel.send(f"{target_item_name} not found in inventory.")
                        else:
                            await interaction.channel.send("Failed to fetch inventory data.")
                    else:
                        await interaction.channel.send("ccid value not found in the script.")
                else:
                    await interaction.channel.send("Character Not Found.")
    else:
        await interaction.channel.send("Failed to fetch data from the website.")

async def calculate_and_send_results(channel, target_count, int_count, daily_gain, weekly_bonus, cost_per_potion):
    current_date = datetime.datetime.now()
    
    days_per_week = 7
    total_daily_gain_legend = daily_gain
    total_daily_gain_non_legend = 0 + (weekly_bonus / days_per_week)
    
    days_to_reach_legend = (target_count - int_count) / total_daily_gain_legend
    days_to_reach_non_legend = (target_count - int_count) / total_daily_gain_non_legend
    
    rounded_days_legend = math.ceil(days_to_reach_legend)  # Round up the days
    rounded_days_non_legend = math.ceil(days_to_reach_non_legend)  #Round up the days
    
    future_date_legend = current_date + datetime.timedelta(days=rounded_days_legend)
    future_date_legend_formatted = future_date_legend.strftime('%d %B %Y')
    
    future_date_non_legend = current_date + datetime.timedelta(days=rounded_days_non_legend)
    future_date_non_legend_formatted = future_date_non_legend.strftime('%d %B %Y')
    
    acs_needed = (target_count - int_count) * (cost_per_potion / daily_gain)  # ACS needed to buy the required potions
    rounded_acs = math.ceil(acs_needed)  # Round up the ACS
    spin_needed = (target_count - int_count) / daily_gain
    rounded_spin = math.ceil(spin_needed)
    
    await channel.send(f"```{daily_gain}X/Spin\nLegend = {rounded_days_legend} days ({future_date_legend_formatted})\nNon-Legend = {rounded_days_non_legend} days ({future_date_non_legend_formatted})\nWith ACS = {rounded_spin} Spin / {rounded_acs} ACS```")
    
@client.tree.command(description='Rank AQW On Captive Server By Achievements')
async def rank(interaction: Interaction):
    await interaction.response.send_message("```Please wait...```")

    # Get all members in the server
    members = interaction.guild.members

    data = []

    # Extract and validate the data using substring operations
    for member in members:
        if not member.bot:
            display_name = member.display_name
            open_bracket_index = display_name.find('[')
            close_bracket_index = display_name.find(']')
            if open_bracket_index != -1 and close_bracket_index != -1:
                name = display_name[:open_bracket_index].strip()
                badge_part = display_name[open_bracket_index + 1:close_bracket_index].strip()
                try:
                    badge = int(badge_part)
                    if badge == 0:
                        continue
                    else:
                        data.append({"nick": name, "badges": badge})

                except ValueError:
                    # Handle cases where badge is not a valid integer
                    pass

    # Sort the data by "badges" in descending order
    data.sort(key=lambda x: x["badges"], reverse=True)

    datas = []

    if data:
        for i, entry in enumerate(data, start=1):
            datas.append(f"\n{i}. {entry['nick']} = {entry['badges']} Badges")
    else:
        datas.append("No valid data found.")

    # Join the results into a single string and send it
    result_content = "AQW Rank on Captive Server\n"
    result_content = result_content + "\n".join(datas)
    with open('rank_report.md', 'w', encoding='utf-8') as file:
        file.write(result_content)
    
    with open('rank_report.md', 'rb') as file:
        await interaction.channel.send(file=discord.File(file, 'rank_report.md'))
    
client.run(discord_token)