import requests
from config import BotConfig


def get_emotion(text):
    req = requests.post(
        BotConfig.emotion_api_url,
        data={
            'text': text,
            'lang_code': 'en',
            'api_key': BotConfig.emotion_key
        },
    )
    assert req.status_code == 200, 'Invalid status code from emotion API ' + req.text
    emotions = req.json()['emotion']
    return emotions