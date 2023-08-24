import asyncio
import datetime
import discord
import requests
import re
import math
import os
from bs4 import BeautifulSoup
from discord import app_commands, Interaction

discord_token = os.environ['DISCORD_TOKEN']
my_guild = discord.Object(id=os.environ['GUILD_ID'])

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def close(self):
        await super().close()
        await self.session.close()

    async def fetch_data(self, url):
        async with self.session.get(url) as response:
            return await response.text()

    async def setup_hook(self):
        self.tree.copy_global_to(guild=my_guild)
        await self.tree.sync(guild=my_guild)

intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)

@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")

@client.tree.command(description='Calculate TP from your character')
async def calculate(interaction: Interaction, username: str):
    await interaction.channel.send("`Please wait...`")
    response = await client.fetch_data(f'https://account.aq.com/CharPage?id={username}')

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        ccid_script = soup.find('script', string=re.compile(r'var ccid = \d+;'))

        if ccid_script:
            ccid_content = ccid_script.string
            ccid_match = re.search(r'var ccid = (\d+);', ccid_content)
            
            if ccid_match:
                ccid = int(ccid_match.group(1))
                inventory_url = f"https://account.aq.com/CharPage/Inventory?ccid={ccid}"
                inventory_response = await client.fetch_data(inventory_url)

                if inventory_response.status_code == 200:
                    inventory_data = inventory_response.json()
                    target_item_name = "Treasure Potion"
                    target_item_entry = next((item for item in inventory_data if item.get("strName") == target_item_name), None)
                    
                    if target_item_entry:
                        int_count = target_item_entry.get("intCount")
                        await interaction.channel.send(f"`{username.title()} current TP = {int_count} TP`")
                        
                        if int_count >= 1000:
                            await interaction.channel.send("```Gausah Sok Merendah Puh, Dah Dapet Wioda Itu```")
                        else:
                            target_count = 1000
                            await calculate_and_send_results(interaction.channel, target_count, int_count, daily_gain=2, weekly_bonus=2, cost_per_potion=200)
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
    
    rounded_days_legend = math.ceil(days_to_reach_legend)
    rounded_days_non_legend = math.ceil(days_to_reach_non_legend)
    
    future_date_legend = current_date + datetime.timedelta(days=rounded_days_legend)
    future_date_legend_formatted = future_date_legend.strftime('%d %B %Y')
    
    future_date_non_legend = current_date + datetime.timedelta(days=rounded_days_non_legend)
    future_date_non_legend_formatted = future_date_non_legend.strftime('%d %B %Y')
    
    acs_needed = (target_count - int_count) * (cost_per_potion / daily_gain)
    rounded_acs = math.ceil(acs_needed)
    spin_needed = (target_count - int_count) / daily_gain
    rounded_spin = math.ceil(spin_needed)
    
    await channel.send(f"```{daily_gain}X/Spin\nLegend = {rounded_days_legend} days ({future_date_legend_formatted})\nNon-Legend = {rounded_days_non_legend} days ({future_date_non_legend_formatted})\nWith ACS = {rounded_spin} Spin / {rounded_acs} ACS```")

async def main():
    await client.start(discord_token)
    await client.setup_hook()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
