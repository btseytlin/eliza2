from functools import wraps
import logging
from telegram import ParseMode
from telegram.utils.helpers import mention_html
import sys
import traceback
from telegram import ChatAction
from telegram.ext import Updater, MessageHandler, Filters
from eliza import Eliza
from config import BotConfig

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.DEBUG)

tg_token = BotConfig.tg_token

REQUEST_KWARGS={
    # "USERNAME:PASSWORD@" is optional, if you need authentication:
    # 'proxy_url': 'socks5://HOST:port',
    'proxy_url': BotConfig.proxy_url,
     'urllib3_proxy_kwargs': {
        'username': BotConfig.proxy_username,
        'password': BotConfig.proxy_password,
    }
}


updater = Updater(token=tg_token,
    request_kwargs=REQUEST_KWARGS,
    use_context=True)
dispatcher = updater.dispatcher


def send_typing_action(func):
    """Sends typing action while processing func command."""
    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context,  *args, **kwargs)

    return command_func


@send_typing_action
def respond(update, context):
    eliza = Eliza()
    eliza.load(BotConfig.script_path)
    memory = context.user_data.get('memory')
    if memory:
        eliza.memory = memory 
    eliza_response = eliza.respond(update.message.text)
    context.user_data['memory'] = eliza.memory
    response_lines = eliza_response.split('\n')
    for line in response_lines:
        context.bot.send_message(chat_id=update.effective_chat.id, text=line.capitalize())



respond_handler = MessageHandler(Filters.text, respond)
dispatcher.add_handler(respond_handler)


def error_handler(update, context):
    devs = BotConfig.admin_ids
    if update.effective_message:
        text = "Hey. I'm sorry to inform you that an error happened while I tried to handle your update. " \
               "My developer(s) will be notified."
        update.effective_message.reply_text(text)

    trace = "".join(traceback.format_tb(sys.exc_info()[2]))
    payload = ""
    if update.effective_user:
        payload += f' with the user {mention_html(update.effective_user.id, update.effective_user.first_name)}'
    if update.effective_chat:
        payload += f' within the chat <i>{update.effective_chat.title}</i>'
        if update.effective_chat.username:
            payload += f' (@{update.effective_chat.username})'
    if update.poll:
        payload += f' with the poll id {update.poll.id}.'
    text = f"Hey.\n The error <code>{context.error}</code> happened{payload}. The full traceback:\n\n<code>{trace}" \
           f"</code>"
    for dev_id in devs:
        context.bot.send_message(dev_id, text, parse_mode=ParseMode.HTML)
    raise
dispatcher.add_error_handler(error_handler)


updater.start_polling()