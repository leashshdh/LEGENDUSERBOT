import re

from telethon.utils import get_display_name

from userbot import legend

from ..core.managers import eor
from ..sql_helper import blacklist_sql as sql
from ..utils import is_admin

menu_category = "admin"


@legend.legend_cmd(incoming=True, groups_only=True)
async def on_new_message(event):
    name = event.raw_text
    snips = sql.get_chat_blacklist(event.chat_id)
    legendadmin = await is_admin(event.client, event.chat_id, event.client.uid)
    if not legendadmin:
        return
    for snip in snips:
        pattern = f"( |^|[^\\w]){re.escape(snip)}( |$|[^\\w])"
        if re.search(pattern, name, types=re.IGNORECASE):
            try:
                await event.delete()
            except Exception:
                await event.client.send_message(
                    BOTLOG_CHATID,
                    f"I do not have DELETE permission in {get_display_name(await event.get_chat())}.\
                     So removing blacklist words from this group",
                )
                for word in snips:
                    sql.rm_from_blacklist(event.chat_id, word.lower())
            break


@legend.legend_cmd(
    pattern="addblacklist ((.|\n)*)",
    command=("addblacklist", menu_category),
    info={
        "header": "To add blacklist words to database",
        "description": "The given word or words will be added to blacklist in that specific chat if any user sends then the message gets deleted.",
        "note": "if you are adding more than one word at time via this, then remember that new word must be given in a new line that is not [hi hello]. It must be as\
            \n[hi \n hello]",
        "usage": "{tr}addblacklist <word(s)>",
        "examples": ["{tr}addblacklist fuck", "{tr}addblacklist fuck\nsex"],
    },
    groups_only=True,
    require_admin=True,
)
async def _(event):
    "To add blacklist words to database"
    text = event.pattern_match.group(1)
    to_blacklist = list(
        {trigger.strip() for trigger in text.split("\n") if trigger.strip()}
    )

    for trigger in to_blacklist:
        sql.add_to_blacklist(event.chat_id, trigger.lower())
    await eor(
        event,
        "Added {} triggers to the blacklist in the current chat".format(
            len(to_blacklist)
        ),
    )


@legend.legend_cmd(
    pattern="rmblacklist ((.|\n)*)",
    command=("rmblacklist", menu_category),
    info={
        "header": "To remove blacklist words from database",
        "description": "The given word or words will be removed from blacklist in that specific chat",
        "note": "if you are removing more than one word at time via this, then remember that new word must be given in a new line that is not [hi hello]. It must be as\
            \n[hi \n hello]",
        "usage": "{tr}rmblacklist <word(s)>",
        "examples": ["{tr}rmblacklist fuck", "{tr}rmblacklist fuck\nsex"],
    },
    groups_only=True,
    require_admin=True,
)
async def _(event):
    "To Remove Blacklist Words from Database."
    text = event.pattern_match.group(1)
    to_unblacklist = list(
        {trigger.strip() for trigger in text.split("\n") if trigger.strip()}
    )
    successful = sum(
        bool(sql.rm_from_blacklist(event.chat_id, trigger.lower()))
        for trigger in to_unblacklist
    )
    await eor(event, f"Removed {successful} / {len(to_unblacklist)} from the blacklist")


@legend.legend_cmd(
    pattern="listblacklist$",
    command=("listblacklist", menu_category),
    info={
        "header": "To show the black list words",
        "description": "Shows you the list of blacklist words in that specific chat",
        "usage": "{tr}listblacklist",
    },
    groups_only=True,
    require_admin=True,
)
async def _(event):
    "To show the blacklist words in that specific chat"
    all_blacklisted = sql.get_chat_blacklist(event.chat_id)
    OUT_STR = "Blacklists in the Current Chat:\n"
    if len(all_blacklisted) > 0:
        for trigger in all_blacklisted:
            OUT_STR += f"👉 {trigger} \n"
    else:
        OUT_STR = "No Blacklists found. Start saving using `.addblacklist`"
    await eor(event, OUT_STR)
