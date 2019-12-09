from functools import wraps
import logging

from telegram import ChatAction
from telegram.ext import Updater, MessageHandler, Filters
from eliza import Eliza
from config import BotConfig

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

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
        context.bot.send_message(chat_id=update.effective_chat.id, text=line)



respond_handler = MessageHandler(Filters.text, respond)
dispatcher.add_handler(respond_handler)

updater.start_polling()