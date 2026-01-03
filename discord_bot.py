import asyncio
import datetime
import discord
import requests
import re
import math
import os
from bs4 import BeautifulSoup
from discord import app_commands, Interaction
import re
import mysql.connector
import pandas as pd
import datetime

discord_token = os.environ['DISCORD_TOKEN']
my_guild = discord.Object(id=int(os.environ['GUILD_ID']))

db_host = os.environ['DB_HOST']
db_user = os.environ['DB_USER']
db_password = os.environ['DB_PASSWORD']
db_name = os.environ['DB_NAME']
application_id = int(os.environ['APPLICATION_ID'])


class MyClient(discord.Client):
    def __init__(self,*,intents:discord.Intents, application_id: int):
        super().__init__(intents=intents, application_id=application_id)
        self.tree = app_commands.CommandTree(self)
        
    async def setup_hook(self):
        self.tree.copy_global_to(guild=my_guild)
        try:
            await self.tree.sync(guild=my_guild)
        except discord.errors.Forbidden:
            print("ERROR: Missing Access (403). Please make sure the bot is invited with the 'applications.commands' scope.")
            print("Generate a new invite link with 'bot' and 'applications.commands' checked in the Developer Portal.")
        except Exception as e:
            print(f"Failed to sync commands: {e}")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = MyClient(intents=intents, application_id=application_id)

@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")

@client.tree.command(description = 'Introduce yourself with name, charname, and guild')
async def introduce(interaction: Interaction, fullname: str, aqwname: str, guild: str):
    if not fullname or not aqwname or not guild:
        await interaction.response.send_message("Datadiri aja kamu kosongin apalagi hati doi 😭")
        return
    
    await interaction.response.defer()

    
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
            
        await delete_user_messages(member, interaction)
        
        if guild == "-":
            guild = "Solo Player"
            
        achievements = "0"
        achievements = "0"
        try:
            await member.add_roles(verif)
        except discord.errors.Forbidden:
             await interaction.followup.send(f"⚠️ I could not assign the role. My role must be higher than the role I'm giving, and I need 'Manage Roles' permission.")
             return
        except Exception as e:
            print(f"Failed to assign role: {e}")
            return
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
                        
        text = f"Halo User {member.id}\n\nNAMA PANGGILAN    : {fullname.title()}\nNAMA KARAKTER     : {aqwname.title()}\nGUILD             : {guild.title()}"
        nickname = f"{aqwname.title()} [{achievements}] | {guild.title()}"
        
        if len(nickname) > 32:
            nickname = f"{aqwname.title()} [{achievements}] | -"
            pjgNick = len(nickname)
            await interaction.followup.send(f"```{text}\n\nNama lu / guild lu kepanjangan cok, tolong singkat terus tulis dibawah deh (Max {32-pjgNick})```")
            try:
                guild_abbreviation_response = await client.wait_for(
                    "message",
                    check=lambda message: message.author.id == member.id and message.channel.id == interaction.channel_id,
                    timeout=60.0,
                )
                guild_abbreviation = guild_abbreviation_response.content
                text = f"Halo User {member.id}\n\nNAMA PANGGILAN    : {fullname.title()}\nNAMA KARAKTER     : {aqwname.title()}\nGUILD             : {guild_abbreviation.title()}"
                await delete_user_messages(member, interaction)
                async for message in interaction.channel.history():
                    if message.author.id == member.id:
                        await message.delete()
                        break
                await interaction.channel.send(f"```{text}```")

                # Update the nickname with the guild abbreviation
                nickname = f"{aqwname.title()} [{achievements}] | {guild_abbreviation.title()}"
            except asyncio.TimeoutError:
                await interaction.channel.send("Lu kelamaan ajg tolong set manual ya cok <@276681083997650947>.")
        else:
            nickname = nickname
            await interaction.followup.send(f"```{text}```")
            
        try:
            await member.edit(nick=nickname)
        except discord.errors.Forbidden:
            await interaction.followup.send(f"⚠️ I could not change your nickname. My role might be below yours, or I lack 'Manage Nicknames' permission.")
        except Exception as e:
            print(f"Failed to edit nickname: {e}")
        
    else:
        await interaction.followup.send("The role verified couldn't be found.")
        





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
        

async def delete_user_messages(member, interaction):
    async for message in interaction.channel.history():
        start = 13
        end = start + len(f"{member.id}")
        previousId = message.content[start:end]
        currentId = str(member.id)
        if previousId == currentId and message.content.startswith("```Halo User"):
            await message.delete()
            break
        
MAX_REGISTRATIONS = 64  # Set the maximum number of registrations
ALLOWED_CHANNEL_ID = 1181895637797703680  # channel ID register
ALLOWED_USER_ID = 472750553957400597 # my user id

# @client.tree.command(description='Register for Captive event')
# async def register_event(interaction: Interaction, pet_name: str, facebook_name: str, aqw_name: str, guild_name: str, pet_url: str):
#     await interaction.response.send_message("```Please wait...```")
#     # Connect to the MySQL database
#     conn = mysql.connector.connect(
#         host=db_host,
#         port=3306,
#         user=db_user,
#         password=db_password,
#         database=db_name
#     )
#     cursor = conn.cursor()

#     # Check if the command is executed in the allowed channel or by the allowed user
#     if interaction.channel_id != ALLOWED_CHANNEL_ID and interaction.user.id != ALLOWED_USER_ID:
#         await interaction.channel.send("This command can only be executed in the specified channel.")
#         cursor.close()
#         conn.close()
#         return
    
#     # Your existing code for role verification and other checks goes here

#     try:
#         # Check the total number of registrations
#         cursor.execute('SELECT COUNT(*) FROM captive_event')
#         total_registrations = cursor.fetchone()[0]

#         if total_registrations >= MAX_REGISTRATIONS:
#             await interaction.channel.send("Sorry, the maximum number of registrations has been reached.")
#             return

#         # Check if the user has already registered
#         cursor.execute('SELECT * FROM captive_event WHERE user_id = %s', (interaction.user.id,))
#         existing_registration = cursor.fetchone()

#         if existing_registration:
#             await interaction.channel.send("You have already registered for the event.")
#             return

#         # Store the registration details in the MySQL database
#         cursor.execute('''
#             INSERT INTO captive_event (user_id, pet_name, facebook_name, aqw_name, guild_name, pet_url)
#             VALUES (%s, %s, %s, %s, %s, %s)
#         ''', (interaction.user.id, pet_name, facebook_name, aqw_name, guild_name, pet_url))
#         conn.commit()
        
#         # Fetch the updated total number of registrations
#         cursor.execute('SELECT COUNT(*) FROM captive_event')
#         updated_total_registrations = cursor.fetchone()[0]

#         # Assuming you want to print the registration details
#         registration_details = f"```Registration Details:\nPet Name: {pet_name}\nFacebook Name: {facebook_name}\nAQW In-game Name: {aqw_name}\nGuild Name: {guild_name}\nPet URL: {pet_url}\nRegistered Number: {updated_total_registrations}```" 

#         await interaction.channel.send(registration_details)
    
#     finally:
#         # Close the cursor and connection when done (even if an exception occurs)
#         cursor.close()
#         conn.close()

# # Role ID that is allowed to use the command
# ALLOWED_ROLE_ID = 1145046711790739660

# @client.tree.command(description='Check registered list')
# async def check_registered_list(interaction: Interaction):
#     await interaction.response.send_message("```Please wait...```")
#     # Connect to the MySQL database
#     conn = mysql.connector.connect(
#         host=db_host,
#         port=3306,
#         user=db_user,
#         password=db_password,
#         database=db_name
#     )
#     cursor = conn.cursor()

#     try:
#         # Check if the user has the allowed role
#         member = interaction.guild.get_member(interaction.user.id)
#         allowed_role = discord.utils.get(interaction.guild.roles, id=ALLOWED_ROLE_ID)

#         if allowed_role and allowed_role in member.roles:
#             # User has the allowed role, proceed with checking the registered list

#             # Fetch the registered list from the MySQL database
#             cursor.execute('SELECT * FROM captive_event')
#             registrations = cursor.fetchall()

#             if registrations:
#                 # Create a DataFrame from the registrations data without specifying columns
#                 df = pd.DataFrame(registrations)

#                 # Rename the columns with the table names
#                 df.columns = ["ID", "UUID", "PET NAME", "FACEBOOK NAME", "AQW IGN", "GUILD NAME", "PET URL"]

#                 # Generate a timestamp
#                 timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

#                 # Construct the file name with a timestamp
#                 file_name = f"registered_list_{timestamp}.xlsx"

#                 # Convert the DataFrame to Excel with headers
#                 with pd.ExcelWriter(file_name, engine="xlsxwriter") as excel_data:
#                     df.to_excel(excel_data, sheet_name="Registered List", index=False, header=True)

#                 # Send the Excel file
#                 with open(file_name, "rb") as file:
#                     await interaction.channel.send("Registered List:", file=discord.File(file, file_name))
#             else:
#                 await interaction.channel.send("No registrations found.")
#         else:
#             await interaction.channel.send("You do not have the required role to use this command.")
#     finally:
#         # Close the cursor and connection when done
#         cursor.close()
#         conn.close()




    
client.run(discord_token)
