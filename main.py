import discord
from datetime import datetime
import os
import pytz
from keep_alive import keep_alive
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from discord.ext import tasks

cred = credentials.Certificate('firebase-sdk.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

my_secret = os.environ['TOKEN']

client = discord.Client()

@client.event
async def on_ready():
    always.start()
    print('We have logged in as {0.user}'.format(client))

@tasks.loop(seconds=5)
async def always():
    
    date_ref = db.collection(u'Assignments')
    docs = date_ref.stream()

    now = datetime.now(pytz.timezone('Turkey')).strftime("%d/%m/%Y %H:%M:%S")
    day = now.split(" ")[0].split("/")[0]
    month = now.split(" ")[0].split("/")[1]
    hour = now.split(" ")[1].split(":")[0]
    minute = now.split(" ")[1].split(":")[1]

    for doc in docs:
        if doc.to_dict().get("used") == "false":
            date = str(doc.to_dict().get("deadline"))
            print(date)

            deadlineDay = date.split(" ")[0].split("/")[0]
            deadlineMonth = date.split(" ")[0].split("/")[1]
            deadlineHour = date.split(" ")[1].split(":")[0]
            deadlineMinute = date.split(" ")[1].split(":")[1]

            if deadlineMonth == month and deadlineDay == day and deadlineHour == hour and 0<=int(minute)-int(deadlineMinute)<=10:
                print("lock")
                tasksChannel = client.get_channel(935269708511453304)
                overwrite = tasksChannel.overwrites_for(client.get_guild(934523473848590387).default_role)
                overwrite.send_messages = False
                await tasksChannel.set_permissions(client.get_guild(934523473848590387).default_role, overwrite=overwrite)

                embed = discord.Embed(title=f'🔒 Locked', description=f'Reason: Deadline ended.')

                await tasksChannel.send(embed=embed)
                doc_ref = db.collection(u'Assignments').document(doc.id)
                doc_ref.update({"used": "true"})
            
            if deadlineMonth == month and deadlineDay == day and deadlineHour == hour and 0<=int(deadlineMinute)-int(minute)<=30 and doc.to_dict().get("warned") == "false":
                tasksChannel = client.get_channel(935269708511453304)
                await tasksChannel.send("Görevin son teslim tarihi olan " + doc.to_dict().get("deadline") + "'a yaklaşık 30 dakika kalmıştır.")
                doc_ref = db.collection(u'Assignments').document(doc.id)
                doc_ref.update({"warned": "true"})



@client.event
async def on_message(message):
    if message.author == client.user:
        return

    role = discord.utils.get(message.guild.roles, name="Yönetici")
        
    if message.content.startswith('$lock '):
        if role in message.author.roles:
            channel = discord.utils.get(message.guild.text_channels, name=message.content.split (" ")[1])
            overwrite = channel.overwrites_for(message.guild.default_role)
            overwrite.send_messages = False
            await channel.set_permissions(message.guild.default_role, overwrite=overwrite)

            embed = discord.Embed(title=f'🔒 Kapandı', description=f'')

            await channel.send(embed=embed)
        else:
            await message.channel.send("Ne yazık ki bu komutu kullanma yetkisine sahip değilsiniz.")

    if message.content.startswith('$unlock '):
        if role in message.author.roles:
            channel = discord.utils.get(message.guild.text_channels, name=message.content.split(" ")[1])
            overwrite = channel.overwrites_for(message.guild.default_role)
            overwrite.send_messages = True
            await channel.set_permissions(message.guild.default_role, overwrite=overwrite)
            embed = discord.Embed(title=f'🔓 Açıldı', description='Sıradaki Görev Verildi')
            await channel.send(embed=embed)
        else:
            await message.channel.send("Ne yazık ki bu komutu kullanma yetkisine sahip değilsiniz.")

    if message.content.startswith('$lockdef'):
        if role in message.author.roles:

            # message Syntax : $lockdef 31/01 00:00 assignment1
            start = message.content.split(" ")
            startDay = start[1] + "/2022"
            startTime = start[2] + ":00"
            assignmentName = start[3]

            startDate = startDay + " " + startTime

            doc_ref = db.collection(u'Assignments').document(assignmentName)
            doc_ref.set({
                u'deadline': startDate,
                u'used': "false",
                u'warned': "false"
            })
            await message.channel.send(startDate + " tarihinde görevler kanalı kapanacaktır.")
        else:
            await message.channel.send("Ne yazık ki bu komutu kullanma yetkisine sahip değilsiniz.")

keep_alive()
client.run(my_secret)
