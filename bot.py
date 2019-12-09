import logging
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


def echo(update, context):
    eliza = Eliza()
    eliza.load(BotConfig.script_path)
    memory = context.user_data.get('memory')
    if memory:
        eliza.memory = memory 
    eliza_response = eliza.respond(update.message.text)
    context.user_data['memory'] = eliza.memory
    context.bot.send_message(chat_id=update.effective_chat.id, text=eliza_response)


echo_handler = MessageHandler(Filters.text, echo)
dispatcher.add_handler(echo_handler)

updater.start_polling()