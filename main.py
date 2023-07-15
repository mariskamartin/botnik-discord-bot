from quart import Quart
import discord
import os
import requests
import random
import re
import utils
from const import HELLO_CMDS, HELLOS, CATCH_YOU, MSG_PREDPLATNE_GAIN, MSG_PREDPLATNE_LOST, WELCOME_GIFS
import pymongo
from datetime import datetime, timedelta
# from collections import namedtuple
# namedtuple object_name = namedtuple("ObjectName", dictionary.keys())(*dictionary.values())
# object_name.key1

print(f'public IP: { requests.get("https://api.ipify.org").text }')

PROFILE_EMOJIS = [
    '\N{PARTY POPPER}', '\N{ROBOT FACE}', '\N{WATERMELON}', '\{U+1F606}',
    '\{U+1F60A}', '\{U+1F603}', '\{U+1F60F}'
]

# globals
D_FORMAT = "%Y-%m-%d"
D_FORMAT_DMY = "%d.%m.%Y"
PREDPLATNE_UPDATE_HOUR = 4
BOT_VERSION = 'v20211226'
GUILD_ID = 853239475773505546  # MOSTMAGIC Klub
OFFTOPIC_CHANNEL = 853239475773505548
ONLINE_CHANNEL = 853318180775395348
SANDBOX_CHANNEL = 855796909389119498
LOG_CHANNEL = 925467073377873970
ROLE_SPRAVCE_ID = 853260291680894996
ROLE_NPC_ID = 853250999958372424
ROLE_PREDPLATITEL_ID = 915371896671981609
_last_update_date = None
_role_spravce = None
_role_npc = None
_role_predplatitel = None
_guild = None
_channel_predplatne = None
_channel_bot_logs = None
_channel_sandbox = None
_channel_online = None
ALLOWED_ADMINS = ['MMartin', 'Clavet','Desetdekasalamu','TapírPapír','mmartin0767','tapirpapir','Desetdekasalamu#9473']


def get_mongodb_client():
    return pymongo.MongoClient(
        f'mongodb+srv://{os.environ["DB_USER"]}:{os.environ["DB_PWD"]}@cluster0.hdr8o.mongodb.net/test?authSource=admin&replicaSet=atlas-vshjv8-shard-0&readPreference=primary&appname=MongoDB%20Compass&ssl=true'
    )


def get_db(dbclient):
    return dbclient['botnik']


def test_db():
    with get_mongodb_client() as myclient:
        print(myclient.list_database_names())
        dblist = myclient.list_database_names()
        if "users" in dblist:
            print("The database exists.")
        myuserdb = myclient["users"]
        myusercol = myuserdb["user"]
        myusers = myusercol.find({})
        #mydoc = mycol.find(myquery).sort("name", -1)
        for u in myusers:
            print(u)


async def update_predplatne(db, guild, channel, force_update=False):
    if datetime.utcnow().strftime(
            D_FORMAT) == _last_update_date and not force_update:
        return

    await channel.send("🔄 - Probíhá aktualizace")
    users_result = db.users.find({})
    str = ''
    hasError = False
    for u in users_result:
        try:
            target_role = guild.get_role(u['roleid'])
            target_member = await guild.fetch_member(u['userid'])
            if utils.has_valid_predplatne(u) and (target_role
                                                  not in target_member.roles):
                await target_member.add_roles(target_role)
                if not target_member.dm_channel:
                    await target_member.create_dm()
                ptxt_start = u['predplatne_start'].strftime(D_FORMAT_DMY)
                ptxt_end = u['predplatne_end'].strftime(D_FORMAT_DMY)
                await target_member.dm_channel.send(
                    MSG_PREDPLATNE_GAIN.format(target_member.name, ptxt_start,
                                               ptxt_end))
                str += f'+ Spuštění předplatného - {target_member} (DM) \n'
            elif not utils.has_valid_predplatne(u) and (
                    target_role in target_member.roles):
                await target_member.remove_roles(target_role)
                if not target_member.dm_channel:
                    await target_member.create_dm()
                await target_member.dm_channel.send(
                    MSG_PREDPLATNE_LOST.format(target_member.name))
                str += f'- Vypršení předplatného - {target_member} (DM) \n'
            # else:
            #   str += f'- Neprovedeny žádné změny - {target_member} \n'
        except Exception as e:
            hasError = True
            str += f'- Chyba - {target_member} ({e}) \n'
    await channel.send(
        str if str else f"{'✅' if not hasError else ':('} - Aktualizováno")
    globals()['_last_update_date'] = datetime.utcnow().strftime(D_FORMAT)


# def try_parse_date(strdate, format='%d/%m/%Y'):
#   try:
#     return datetime.strptime(strdate, format)
#   except:
#     return None

db_client = get_mongodb_client()
db = get_db(db_client)

intents_config = discord.Intents.default()
intents_config.members = True
client = discord.Client(intents=intents_config)


@client.event
async def on_ready():
    # test_db()
    print(f'We have logged as {client.user}')
    print(f'public IP: { requests.get("https://api.ipify.org").text }')

    globals()['_guild'] = discord.utils.get(client.guilds, id=GUILD_ID)
    globals()['_channel_predplatne'] = discord.utils.get(_guild.channels, id=OFFTOPIC_CHANNEL)
    globals()['_channel_bot_logs'] = discord.utils.get(_guild.channels, id=LOG_CHANNEL)
    globals()['_channel_sandbox'] = discord.utils.get(_guild.channels, id=SANDBOX_CHANNEL)
    globals()['_channel_online'] = discord.utils.get(_guild.channels, id=ONLINE_CHANNEL)
    globals()['_role_spravce'] = discord.utils.get(_guild.roles, id=ROLE_SPRAVCE_ID) # role.name: Spravce
    globals()['_role_npc'] = discord.utils.get(_guild.roles, id=ROLE_NPC_ID)
    globals()['_role_predplatitel'] = discord.utils.get(_guild.roles, id=ROLE_PREDPLATITEL_ID)
    print(f'_guild: {_guild}')
    print(f'_channel_predplatne: {_channel_predplatne}')
    print(f'_role_spravce: {_role_spravce.id}')
    print(f'_role_npc: {_role_npc.id}')

    # clavet = await client.fetch_user(179597078052208641)
    # print(f'clavet: {clavet}')
    # cm = await g.fetch_member(179597078052208641)
    # print(f'clavet member: {cm}')

    # await utils.fetch_mtgi2(_channel_bot_logs)

    # test direct message
    # mms = await g.query_members(query='MMartin',limit=1)
    # mm = mms[0]
    # print(f'q member: {mm}')
    # if not mm.dm_channel:
    #   await mm.create_dm()
    # await mm.dm_channel.send(f'Hi {mm.name}, tldr; Pip, Bzzz...')

    # clavet = discord.utils.get(g.members, id=179597078052208641)
    # bot_member = _guild.get_member(client.user.id) # this is working only after query
    # await bot_member.edit(nick=f'BOTNíK') # \N{ROBOT FACE}

    #  e = discord.utils.find(lambda e: e.name == 'robot', client.emojis)
    # print(f'/n/n{client.emojis}/n/n')
    #  print(f'e: {e}')
    #\N{PARTY POPPER}

    # emoji = discord.utils.get(_guild.emojis, name='COIN')
    # print(f'{emoji}')
    # if emoji:
    #   await _channel_sandbox.send(emoji)

    #role predplatitel id: 915371896671981609
    # print(f'g.roles: {g.roles}')
    #  print(f'g.emojis: {g.emojis}')

    # add role if needed
    # gr = _guild.get_role(900658230286495766)
    # if gr not in bot_member.roles:
    #   print(f'roles before: {bot_member.roles}')
    #   new_roles = bot_member.roles + [gr]
    #   await bot_member.edit(roles=new_roles)
    #   print(f'roles after: {bot_member.roles}')

    # random msg
    # await _channel_online.send("Když Vás bude 7, tak si zahraju jako 8")

    PLAY_ACTIVITIES = [
        "Magic the Gathering", "Modern", "Standard", "EDH", "Draft",
        "MtG Arena", "Pauper", "s proxnutou kartou", "bez obalů na karty",
        "jednu a Sol Ring", "MTG s MEE6 botem", "Fallout 2"
    ]
    game = discord.Game(random.choice(PLAY_ACTIVITIES))
    await client.change_presence(status=discord.Status.online, activity=game)
    await _channel_bot_logs.send(f'ready from martin\'s HW')
    print('finished end on ready block')


@client.event
async def on_member_join(member):
    await _channel_predplatne.send(
        f'Ahoj {member.mention}! Vítej na serveru klubu **MOSTMAGIC**!\n {random.choice(WELCOME_GIFS)}'
    )


@client.event
async def on_message(message):
    try:
        if message.author == client.user:
            return

        # print(f'{message}')
        # print(f'msg: \n{message.content}')
        # print(f'gid: {message.guild.id}')
        # print(f'g: {message.guild}')
        # print(f'aid: {message.author.id}')

        print(f'channel: {message.channel}, id: {message.channel.id}')
        print(f'author: {message.author}')
        for line in message.content.splitlines():
            print(f'line: {line}')
            msg = line.lower()
            matcher = re.search(
                "^bot[e]{0,1} (hi|hello|dobre rano|ahoj|nazdar|roll|giphy|ld|lucky drop|db|spam)(.*)",
                msg)
            matcher_v2 = re.search("^!(pp|test|psi|plist)(.*)", msg)

            if matcher_v2 is not None:
                # own security manipulation check - names
                print(f'aname: {message.author.name}')
                if message.author.name not in ALLOWED_ADMINS:
                    await message.channel.send(
                        f'{message.author} {random.choice(CATCH_YOU)}')
                    return

                cmd2 = matcher_v2.group(1)

                if cmd2 == 'pp':
                    # predplatne pridat
                    l = line.split()
                    target_member = None
                    if l[1].startswith('<'):
                        uid = utils.parse_mention_id(l[1])
                        print(f'uid {uid}')
                        target_member = await message.guild.fetch_member(uid)
                    else:
                        target_members = await message.guild.query_members(
                            query=l[1], limit=1)
                        target_member = target_members[0]
                    # print(f'target member: {target_member}')
                    d = datetime.utcnow()
                    end = utils.last_day_of_month(d)
                    add_months = int(l[2]) if len(l) >= 3 else 0

                    print(
                        f'calling predplatne pridat user: {target_member}, valid until: {end} +months {add_months}'
                    )

                    predplatne_start = datetime.utcnow().replace(day=1)
                    predplatne_end = utils.last_day_of_month(
                        utils.months_add(datetime.utcnow(), add_months))
                    predplatne_end = predplatne_end.replace(hour=23, minute=59)

                    # has user predplatne already?
                    user_query = {"userid": target_member.id}
                    u = db.users.find_one(user_query)
                    if not u:
                        await _channel_bot_logs.send(
                            f'> uzivatel ({l[1]}) nenalezen v db. Bude automaticky vlozen.'
                        )
                        post = {
                            "inserted_by_name": message.author.name,
                            "created": datetime.utcnow(),
                            "updated": datetime.utcnow(),
                            "name": target_member.name,
                            "userid": target_member.id,
                            "roleid": ROLE_PREDPLATITEL_ID,
                            "emoji": random.choice(PROFILE_EMOJIS),
                            "guild_id": GUILD_ID,
                            "predplatne_start": predplatne_start,
                            "predplatne_end": predplatne_start
                        }
                        # "predplatne_start": predplatne_start,
                        # "predplatne_end": predplatne_end }
                        print(f'post: \n{post}')
                        # await message.channel.send(f'+ user added:/n{post}')
                        db.users.insert_one(post)
                        await _channel_bot_logs.send(
                            f'+ uzivatel {target_member.name} byl pridan do db'
                        )
                        u = db.users.find_one(user_query)

                    if utils.has_valid_predplatne(
                            u) and u['predplatne_end'].strftime(
                                D_FORMAT) == predplatne_end.strftime(D_FORMAT):
                        # yes - and date is same as end of month > generate ERROR
                        # plus odesilani zprav do offtopic channel - zatim jenom do sandboxu
                        print(
                            f'user already has setuped PREDPLATNE until {predplatne_end.strftime(D_FORMAT)}'
                        )
                        await message.reply(
                            f'{target_member.name} už předplatitel je. Má předplaceno do {predplatne_end.strftime(D_FORMAT)}',
                            mention_author=False)
                    else:
                        # no - update predplatne of user to setuped datetime
                        newvalues = {
                            "$set": {
                                "updated": datetime.utcnow(),
                                "predplatne_start": predplatne_start,
                                "predplatne_end": predplatne_end
                            }
                        }
                        print(f'newvalues: {newvalues}')
                        updateResult = db.users.update_one(
                            user_query, newvalues)
                        await _channel_bot_logs.send(
                            f'✅ - Změny provedeny (upraveno predplatne #{updateResult.modified_count}, {target_member.name})'
                        )
                        if updateResult.modified_count == 1:
                            if predplatne_end < u['predplatne_end']:
                                await message.reply(
                                    f'Zkrácení předplatného uživatele',
                                    mention_author=False)
                                return
                            await update_predplatne(db, _guild,
                                                    _channel_bot_logs, True)
                            await _channel_predplatne.send(
                                f'{target_member.mention} se stal předplatilem klubu **MOSTMAGIC**! \N{PARTY POPPER}'
                            )

                elif cmd2 == 'test':
                    l = line.split()
                    if l[1].startswith('<'):
                        xid = utils.parse_mention_id(l[1])
                        print(f'xid: {xid}')
                        return

                    mm = message.mentions[0] if len(
                        message.mentions) > 0 else None
                    print(f'calling test {mm}')
                    config = db.config.find_one({"name": "predplatne_emoji"})
                    await message.channel.send(
                        f'predplatne emoji {config["value"]}')
                    if mm:
                        await mm.edit(nick=f'{mm.nick} {config["value"]}'
                                      )  # \N{ROBOT FACE}

                elif cmd2 == 'psi':
                    l = line.split()
                    print(f'calling set predplatne icon {l[1]}')
                    updateResult = db.config.update_one(
                        {"name": "predplatne_emoji"},
                        {"$set": {
                            "value": l[1]
                        }})
                    await message.reply(
                        f'✅ - Změny provedeny (#{updateResult.modified_count})',
                        mention_author=False)

            if matcher is None:
                print(f'> no match')
                return

            cmd = matcher.group(1)
            if cmd in HELLO_CMDS:
                await message.reply(
                    f'{random.choice(HELLOS)} \n {utils.get_random_giphy_url() if random.random() > 0.4 else ""}',
                    mention_author=True)

            elif cmd in ('ld', 'lucky drop'):
                max_ld = int(matcher.group(2)[1:])
                await message.reply(
                    f'Lucky drop number (between 4 and {max_ld}): {random.randint(4,max_ld)}',
                    mention_author=True)

            elif cmd == 'roll':
                try:
                    dice = matcher.group(2)[1:]
                    rolls, limit = map(int, dice.split('d'))
                except Exception:
                    await message.channel.send(
                        'Spatny format! Priklad 3x 20stenkou: bot roll 3d20')
                    return
                result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
                await message.channel.send(result)

            elif cmd == 'giphy' or cmd == 'spam':
                url = utils.get_random_giphy_url(
                    matcher.group(2)[1:]) if matcher.group(
                        2) else utils.get_random_giphy_url()
                await message.channel.send(url)

            elif cmd == 'db':
                # for member in message.mentions:
                #   print(f'mentioned - {member}')

                # g = client.get_guild(853239475773505546)
                # print(f'g: {g.id} vs mg: {message.guild.id}')
                # am = g.get_member(message.author.id)

                #    sr = message.guild.get_role(900658230286495766)
                # print(f'member = {member}')
                # print(f'author = {message.author}')
                # print(f'_role_spravce = {_role_spravce}')
                # print(f'message = {message.content}')
                # is_multiline = '\n' in message.content
                # print(f'multiline = {is_multiline}')

                # own security manipulation check - role
                # if _role_spravce not in message.author.roles:
                #   await message.channel.send(f'{message.author} nemas opravneni manipulovat s db, nemas roli {_role_spravce}')
                #   return

                # own security manipulation check - names
                if message.author.name not in ALLOWED_ADMINS:
                    await message.channel.send(
                        f'{message.author} {random.choice(CATCH_YOU)}')
                    return

                content = matcher.group(2)[1:]
                l = content.split()
                today = datetime.utcnow()
                end = today + timedelta(days=+30)
                lorig = line.split()

                if l[0] == 'insert':
                    predplatne_start = datetime.strptime(
                        l[4], '%d/%m/%Y') if len(l) > 4 else today
                    predplatne_end = datetime.strptime(
                        l[5], '%d/%m/%Y') if len(l) > 5 else end
                    #userid or name
                    target_member = None
                    if l[1].startswith('<'):
                        target_member = await message.guild.fetch_member(
                            int(l[1][3:-1]))
                    else:
                        target_members = await message.guild.query_members(
                            query=lorig[3], limit=1)
                        target_member = target_members[0]

                    print(f'member: {target_member}')

                    post = {
                        "inserted_by_name": message.author.name,
                        "created": datetime.utcnow(),
                        "name": target_member.name,
                        "userid": target_member.id,
                        "roleid": int(l[2][3:-1]),
                        "emoji": l[3],
                        "guild_id": message.guild.id,
                        "predplatne_start": predplatne_start,
                        "predplatne_end": predplatne_end
                    }
                    print(f'post: \n{post}')
                    # await message.channel.send(f'+ user added:/n{post}')
                    db.users.insert_one(post)
                    await message.channel.send(f'+ user added')

                elif l[0] == 'list':
                    # query member via ids , param cache fills get_memeber()
                    # also optimize fetched fields
                    result = db.users.find({})
                    str = ''
                    for u in result:
                        um = await message.guild.fetch_member(u['userid'])
                        str_date = f'({u["predplatne_start"].strftime(D_FORMAT_DMY)} - {u["predplatne_end"].strftime(D_FORMAT_DMY)})'
                        uname = um.nick if um.nick else um.name
                        str += f'{u["emoji"]} {uname}  {"**ANO**" if utils.has_valid_predplatne(u) else "NE"}\n   {str_date}\n'
                    await message.channel.send(f'user list:\n {str}')

                elif l[0] == 'update':
                    await update_predplatne(db, _guild, _channel_bot_logs,
                                            True)

                elif l[0] == 'set' or l[0] == 'sd':
                    #userid or name
                    target_name_or_userid_query = {
                        "userid": int(l[1][3:-1])
                    } if l[1].startswith('<') else {
                        "name": lorig[3]
                    }
                    predplatne_start = datetime.strptime(l[2], '%d/%m/%Y')
                    predplatne_end = datetime.strptime(
                        l[3], '%d/%m/%Y')  # 28/11/2021
                    # users_result = db.users.find_one({'userid': target_userid})
                    newvalues = {
                        "$set": {
                            "predplatne_start": predplatne_start,
                            "predplatne_end": predplatne_end
                        }
                    }
                    print(
                        f'target_name_or_userid_query: {target_name_or_userid_query}'
                    )
                    updateResult = db.users.update_one(
                        target_name_or_userid_query, newvalues)
                    await message.reply(
                        f'done (q: {target_name_or_userid_query}, modified_count:{updateResult.modified_count})',
                        mention_author=False)

                elif l[0] == 'f':
                    target_members = await message.guild.fetch_member(
                        int(l[1][3:-1])) if l[1].startswith(
                            '<') else await message.guild.query_members(
                                query=l[1], limit=1)
                    print(f'member: {target_members[0]}')

                else:
                    await message.reply(
                        f'Nope, nothing to do. Bad syntax probably :) ',
                        mention_author=False)

    except pymongo.errors.ConnectionFailure as ce:
        print(f'ex: {ce}')
        await _channel_bot_logs.send("⛔ - Něco se nepovedlo s databází")
    except Exception as e:
        print(f'ex: {e}')
        await _channel_bot_logs.send("⛔ - Něco se nepovedlo")


async def keep_alive_callback():
    d = datetime.utcnow()
    print(f'keep alive called at {d}')
    if db is None:
        print(f'the database is None')
        return

    if d.hour == PREDPLATNE_UPDATE_HOUR and _guild is not None:
        await update_predplatne(db, _guild, _channel_bot_logs)

    if d.hour == PREDPLATNE_UPDATE_HOUR:
        await utils.fetch_mtgi2(_channel_bot_logs)


# TODO move to own task
app = Quart(__name__)


@app.route('/')
async def home():
    await keep_alive_callback()
    return 'ok'


client.loop.create_task(app.run_task(host='0.0.0.0', port=8080, use_reloader=False, debug=True))
client.run(os.environ['BOT_TOKEN'])
