import logging
import os
from telegram.ext import Updater, MessageHandler, Filters
from eliza import Eliza

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

proxy_url = os.environ.get('proxy_url')
proxy_username = os.environ.get('proxy_username')
proxy_password = os.environ.get('proxy_password')

tg_token = os.environ.get('tg_token')

REQUEST_KWARGS={
    # "USERNAME:PASSWORD@" is optional, if you need authentication:
    # 'proxy_url': 'socks5://HOST:port',
    'proxy_url': proxy_url, 
     'urllib3_proxy_kwargs': {
        'username': proxy_username, #'frater',
        'password': proxy_password, #'385qDKJ734NKKrr9',
    }
}


updater = Updater(token=tg_token, #'1021957106:AAHzslts_jHpZ4j2sw4IWPNrmU1_1TnqJWM', 
    request_kwargs=REQUEST_KWARGS,
    use_context=True)
dispatcher = updater.dispatcher

def echo(update, context):
    eliza = Eliza()
    eliza.load('doctor.txt')
    memory = context.user_data.get('memory')
    if memory:
        eliza.memory = memory 
    eliza_response = eliza.respond(update.message.text)
    context.user_data['memory'] = eliza.memory
    context.bot.send_message(chat_id=update.effective_chat.id, text=eliza_response)

echo_handler = MessageHandler(Filters.text, echo)
dispatcher.add_handler(echo_handler)

updater.start_polling()