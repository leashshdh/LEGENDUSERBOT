from datetime import datetime

from telethon.utils import get_display_name

from userbot import legend
from userbot.core.logger import logging

from ..Config import Config
from ..core import CMD_INFO, PLG_INFO
from ..core.data import _sudousers_list, sudo_enabled_cmds
from ..core.managers import eod, eor
from ..helpers.utils import get_user_from_event, mentionuser
from ..sql_helper import global_collectionjson as sql
from ..sql_helper import global_list as sqllist
from ..sql_helper.globals import addgvar, delgvar, gvarstatus

menu_category = "tools"

LOGS = logging.getLogger(__name__)


async def _init() -> None:
    sudousers = _sudousers_list()
    Config.SUDO_USERS.clear()
    for user_d in sudousers:
        Config.SUDO_USERS.add(user_d)


def get_key(val):
    for key, value in PLG_INFO.items():
        for cmd in value:
            if val == cmd:
                return key
    return None


@legend.legend_cmd(
    pattern="sudo (on|off)$",
    command=("sudo", menu_category),
    info={
        "header": "To enable or disable sudo of your Legenduserbot.",
        "description": "Initially all sudo commands are disabled, you need to enable them by addscmd\n Check `{tr}help -c addscmd`",
        "usage": "{tr}sudo <on/off>",
    },
)
async def chat_blacklist(event):
    "To enable or disable sudo of your LegendUserBot."
    input_str = event.pattern_match.group(1)
    sudousers = _sudousers_list()
    if input_str == "on":
        if gvarstatus("sudoenable") is not None:
            return await eod(event, "__Sudo is already enabled.__")
        addgvar("sudoenable", "true")
        text = "__Enabled sudo successfully.__\n"
        if len(sudousers) != 0:
            text += (
                "**Bot is reloading to apply the changes. Please wait for a minute**"
            )
            msg = await eor(
                event,
                text,
            )
            return await event.client.reload(msg)
        text += "**You haven't added anyone to your sudo yet.**"
        return await eor(
            event,
            text,
        )
    if gvarstatus("sudoenable") is not None:
        delgvar("sudoenable")
        text = "__Disabled sudo successfully.__"
        if len(sudousers) != 0:
            text += (
                "**Bot is reloading to apply the changes. Please wait for a minute**"
            )
            msg = await eor(
                event,
                text,
            )
            return await event.client.reload(msg)
        text += "**You haven't added any chat to blacklist yet.**"
        return await eor(
            event,
            text,
        )
    await eod(event, "It was turned off already")


@legend.legend_cmd(
    pattern="addsudo(?:\s|$)([\s\S]*)",
    command=("addsudo", menu_category),
    info={
        "header": "To add user as your sudo.",
        "usage": "{tr}addsudo <username/reply/mention>",
    },
)
async def add_sudo_user(event):
    "To add user to sudo."
    replied_user, error_i_a = await get_user_from_event(event)
    if replied_user is None:
        return
    if replied_user.id == event.client.uid:
        return await eod(event, "__You can't add yourself to sudo.__.")
    if replied_user.id in _sudousers_list():
        return await eod(
            event,
            f"{mentionuser(get_display_name(replied_user),replied_user.id)} __is already in your sudo list.__",
        )
    date = str(datetime.now().strftime("%B %d, %Y"))
    userdata = {
        "chat_id": replied_user.id,
        "chat_name": get_display_name(replied_user),
        "chat_username": replied_user.username,
        "date": date,
    }
    try:
        sudousers = sql.get_collection("sudousers_list").json
    except AttributeError:
        sudousers = {}
    sudousers[str(replied_user.id)] = userdata
    sql.del_collection("sudousers_list")
    sql.add_collection("sudousers_list", sudousers, {})
    sudocmds = sudo_enabled_cmds()
    totalcmds = CMD_INFO.keys()
    typecmds = (
        PLG_INFO["botcontrols"]
        + PLG_INFO["autoprofile"]
        + PLG_INFO["evaluators"]
        + PLG_INFO["execmod"]
        + PLG_INFO["heroku"]
        + PLG_INFO["profile"]
        + PLG_INFO["pmpermit"]
        + PLG_INFO["custom"]
        + PLG_INFO["blacklistchats"]
        + PLG_INFO["corecmds"]
        + PLG_INFO["groupactions"]
        + PLG_INFO["sudo"]
        + PLG_INFO["transfer_channel"]
        + ["gauth"]
        + ["greset"]
    )
    loadcmds = list(set(totalcmds) - set(typecmds))
    if len(sudocmds) > 0:
        sqllist.del_keyword_list("sudo_enabled_cmds")
    for cmd in loadcmds:
        sqllist.add_to_list("sudo_enabled_cmds", cmd)
    output = f"{mentionuser(userdata['chat_name'],userdata['chat_id'])} __is Added to your sudo users.__\n"
    output += "**Bot is reloading to apply the changes. Please wait for a minute**"
    msg = await eor(event, output)
    await event.client.reload(msg)


@legend.legend_cmd(
    pattern="delsudo(?:\s|$)([\s\S]*)",
    command=("delsudo", menu_category),
    info={
        "header": "To remove user from your sudo.",
        "usage": "{tr}delsudo <username/reply/mention>",
    },
)
async def _(event):
    "To del user from sudo."
    replied_user, error_i_a = await get_user_from_event(event)
    if replied_user is None:
        return
    try:
        sudousers = sql.get_collection("sudousers_list").json
    except AttributeError:
        sudousers = {}
    if str(replied_user.id) not in sudousers:
        return await eod(
            event,
            f"{mentionuser(get_display_name(replied_user),replied_user.id)} __is not in your sudo__.",
        )
    del sudousers[str(replied_user.id)]
    sql.del_collection("sudousers_list")
    sql.add_collection("sudousers_list", sudousers, {})
    output = f"{mentionuser(get_display_name(replied_user),replied_user.id)} __is removed from your sudo users.__\n"
    output += "**Bot is reloading to apply the changes. Please wait for a minute**"
    msg = await eor(event, output)
    await event.client.reload(msg)


@legend.legend_cmd(
    pattern="listsudo$",
    command=("listsudo", menu_category),
    info={
        "header": "To list users for whom you are sudo.",
        "usage": "{tr}listsudo",
    },
)
async def _(event):
    "To list Your sudo users"
    sudochats = _sudousers_list()
    try:
        sudousers = sql.get_collection("sudousers_list").json
    except AttributeError:
        sudousers = {}
    if len(sudochats) == 0:
        return await eod(event, "__There are no sudo users for your Legenduserbot.__")
    result = "**The list of sudo users for your LegendUserbot are :**\n\n"
    for chat in sudochats:
        result += f"☞ **Name:** {mentionuser(sudousers[str(chat)]['chat_name'],sudousers[str(chat)]['chat_id'])}\n"
        result += f"**Chat Id :** `{chat}`\n"
        username = f"@{sudousers[str(chat)]['chat_username']}" or "__None__"
        result += f"**Username :** {username}\n"
        result += f"Added on {sudousers[str(chat)]['date']}\n\n"
    await eor(event, result)


@legend.legend_cmd(
    pattern="addscmd(s)?(?:\s|$)([\s\S]*)",
    command=("addscmd", menu_category),
    info={
        "header": "To enable cmds for sudo users.",
        "flags": {
            "-all": "Will enable all cmds for sudo users. (except few like eval, exec, profile).",
            "-full": "Will add all cmds including eval,exec...etc. compelete sudo.",
            "-p": "Will add all cmds from the given plugin names.",
        },
        "usage": [
            "{tr}addscmd -all",
            "{tr}addscmd -full",
            "{tr}addscmd -p <plugin names>",
            "{tr}addscmd <commands>",
        ],
        "examples": [
            "{tr}addscmd -p autoprofile botcontrols i.e, for multiple names use space between each name",
            "{tr}addscmd ping alive i.e, for multiple names use space between each name",
        ],
    },
)
async def _(event):  # sourcery no-metrics
    "To enable cmds for sudo users."
    input_str = event.pattern_match.group(2)
    errors = ""
    sudocmds = sudo_enabled_cmds()
    if not input_str:
        return await eor(event, "__Which command should i enable for sudo users . __")
    input_str = input_str.split()
    if input_str[0] == "-all":
        legendevent = await eor(event, "__Enabling all safe cmds for sudo....__")
        totalcmds = CMD_INFO.keys()
        typecmds = (
            PLG_INFO["botcontrols"]
            + PLG_INFO["autoprofile"]
            + PLG_INFO["evaluators"]
            + PLG_INFO["execmod"]
            + PLG_INFO["heroku"]
            + PLG_INFO["profile"]
            + PLG_INFO["pmpermit"]
            + PLG_INFO["custom"]
            + PLG_INFO["blacklistchats"]
            + PLG_INFO["corecmds"]
            + PLG_INFO["groupactions"]
            + PLG_INFO["sudo"]
            + PLG_INFO["transfer_channel"]
            + ["gauth"]
            + ["greset"]
        )
        loadcmds = list(set(totalcmds) - set(typecmds))
        if len(sudocmds) > 0:
            sqllist.del_keyword_list("sudo_enabled_cmds")
    elif input_str[0] == "-full":
        legendevent = await eor(event, "__Enabling compelete sudo for users....__")
        loadcmds = CMD_INFO.keys()
        if len(sudocmds) > 0:
            sqllist.del_keyword_list("sudo_enabled_cmds")
    elif input_str[0] == "-p":
        legendevent = event
        input_str.remove("-p")
        loadcmds = []
        for plugin in input_str:
            if plugin not in PLG_INFO:
                errors += (
                    f"`{plugin}` __There is no such plugin in your LegendUserBot__.\n"
                )
            else:
                loadcmds += PLG_INFO[plugin]
    else:
        legendevent = event
        loadcmds = []
        for cmd in input_str:
            if cmd not in CMD_INFO:
                errors += (
                    f"`{cmd}` __There is no such command in your LegendUserBot__.\n"
                )
            elif cmd in sudocmds:
                errors += f"`{cmd}` __Is already enabled for sudo users__.\n"
            else:
                loadcmds.append(cmd)
    for cmd in loadcmds:
        sqllist.add_to_list("sudo_enabled_cmds", cmd)
    result = (
        f"__Successfully enabled __ `{len(loadcmds)}` __ for LegendUserBot sudo.__\n"
    )
    output = (
        result + "**Bot is reloading to apply the changes. Please wait for a minute**\n"
    )
    if errors != "":
        output += "\n**Errors:**\n" + errors
    msg = await eor(legendevent, output)
    await event.client.reload(msg)


@legend.legend_cmd(
    pattern="rmscmd(s)?(?:\s|$)([\s\S]*)?",
    command=("rmscmd", menu_category),
    info={
        "header": "To disable given cmds for sudo.",
        "flags": {
            "-all": "Will disable all enabled cmds for sudo users.",
            "-type": "Will disable all typeed cmds like eval, exec...etc.",
            "-p": "Will disable all cmds from the given plugin names.",
        },
        "usage": [
            "{tr}rmscmd -all",
            "{tr}rmscmd -type",
            "{tr}rmscmd -p <plugin names>",
            "{tr}rmscmd <commands>",
        ],
        "examples": [
            "{tr}rmscmd -p autoprofile botcontrols i.e, for multiple names use space between each name",
            "{tr}rmscmd ping alive i.e, for multiple commands use space between each name",
        ],
    },
)
async def _(event):  # sourcery no-metrics
    "To disable cmds for sudo users."
    input_str = event.pattern_match.group(2)
    errors = ""
    sudocmds = sudo_enabled_cmds()
    if not input_str:
        return await eor(event, "__Which command should I disable for sudo users . __")
    input_str = input_str.split()
    if input_str[0] == "-all":
        legendevent = await eor(event, "__Disabling all enabled cmds for sudo....__")
        typecmds = sudocmds
    elif input_str[0] == "-type":
        legendevent = await eor(event, "__Disabling all typeged cmds for sudo.....__")
        typecmds = (
            PLG_INFO["botcontrols"]
            + PLG_INFO["autoprofile"]
            + PLG_INFO["evaluators"]
            + PLG_INFO["execmod"]
            + PLG_INFO["heroku"]
            + PLG_INFO["profile"]
            + PLG_INFO["pmpermit"]
            + PLG_INFO["custom"]
            + PLG_INFO["blacklistchats"]
            + PLG_INFO["corecmds"]
            + PLG_INFO["groupactions"]
            + PLG_INFO["sudo"]
            + PLG_INFO["transfer_channel"]
            + ["gauth"]
            + ["greset"]
        )
    elif input_str[0] == "-p":
        legendevent = event
        input_str.remove("-p")
        typecmds = []
        for plugin in input_str:
            if plugin not in PLG_INFO:
                errors += (
                    f"`{plugin}` __There is no such plugin in your LegendUserBot__.\n"
                )
            else:
                typecmds += PLG_INFO[plugin]
    else:
        legendevent = event
        typecmds = []
        for cmd in input_str:
            if cmd not in CMD_INFO:
                errors += (
                    f"`{cmd}` __There is no such command in your LegendUserBot__.\n"
                )
            elif cmd not in sudocmds:
                errors += f"`{cmd}` __Is already disabled for sudo users__.\n"
            else:
                typecmds.append(cmd)
    count = 0
    for cmd in typecmds:
        if sqllist.is_in_list("sudo_enabled_cmds", cmd):
            count += 1
            sqllist.rm_from_list("sudo_enabled_cmds", cmd)
    result = f"__Successfully disabled __ `{count}` __ for LegendUserBot sudo.__\n"
    output = (
        result + "**Bot is reloading to apply the changes. Please wait for a minute**\n"
    )
    if errors != "":
        output += "\n**Errors:**\n" + errors
    msg = await eor(legendevent, output)
    await event.client.reload(msg)


@legend.legend_cmd(
    pattern="vscmds( -d)?$",
    command=("vscmds", menu_category),
    info={
        "header": "To show list of enabled cmds for sudo.",
        "description": "will show you the list of all enabled commands",
        "flags": {"-d": "To show disabled cmds instead of enabled cmds."},
        "usage": [
            "{tr}vscmds",
            "{tr}vscmds -d",
        ],
    },
)
async def _(event):  # sourcery no-metrics
    "To show list of enabled cmds for sudo."
    input_str = event.pattern_match.group(1)
    sudocmds = sudo_enabled_cmds()
    clist = {}
    error = ""
    if not input_str:
        text = "**The list of sudo enabled commands are :**"
        result = "**SUDO ENABLED COMMANDS**"
        if len(sudocmds) > 0:
            for cmd in sudocmds:
                plugin = get_key(cmd)
                if plugin in clist:
                    clist[plugin].append(cmd)
                else:
                    clist[plugin] = [cmd]
        else:
            error += "__You haven't enabled any sudo cmd for sudo users.__"
        count = len(sudocmds)
    else:
        text = "**The list of sudo disabled commands are :**"
        result = "**SUDO DISABLED COMMANDS**"
        totalcmds = CMD_INFO.keys()
        cmdlist = list(set(totalcmds) - set(sudocmds))
        if cmdlist:
            for cmd in cmdlist:
                plugin = get_key(cmd)
                if plugin in clist:
                    clist[plugin].append(cmd)
                else:
                    clist[plugin] = [cmd]
        else:
            error += "__You have enabled every cmd as sudo for sudo users.__"
        count = len(cmdlist)
    if error != "":
        return await eod(event, error, 10)
    pkeys = clist.keys()
    n_pkeys = [i for i in pkeys if i is not None]
    pkeys = sorted(n_pkeys)
    output = ""
    for plugin in pkeys:
        output += f"• {plugin}\n"
        for cmd in clist[plugin]:
            output += f"`{cmd}` "
        output += "\n\n"
    finalstr = (
        result
        + f"\n\n**SUDO TRIGGER: **`{Config.SUDO_HANDLER}`\n**Commands:** {count}\n\n"
        + output
    )
    await eor(event, finalstr, aslink=True, linktext=text)


legend.loop.create_task(_init())
