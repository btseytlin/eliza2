from confi import BaseEnvironConfig, FloatConfig, ConfigField


class BotConfig(BaseEnvironConfig):
    # Tgbot configs
    proxy_url = ConfigField()
    proxy_username = ConfigField()
    proxy_password = ConfigField()
    tg_token = ConfigField(required=True)

    # Eliza configs
    script_path = ConfigField(default='doctor.txt')

    # Emotion api
    emotion_api_url = ConfigField(default='https://apis.paralleldots.com/v4/emotion')
    emotion_key = ConfigField(required=True)
    emotion_emotion_threshold = FloatConfig(default=0.3)