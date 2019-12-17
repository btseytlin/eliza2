from confi import BaseEnvironConfig, FloatConfig, ConfigField, BooleanConfig


class BotConfig(BaseEnvironConfig):
    # Tgbot configs
    proxy_url = ConfigField()
    proxy_username = ConfigField()
    proxy_password = ConfigField()
    tg_token = ConfigField(required=True)

    admin_ids = ConfigField(processor=lambda s: [int(id_) for id_ in s.split(',')])

    # Eliza configs
    script_path = ConfigField(default='doctor.txt')

    # Emotion API
    use_emotion = BooleanConfig(default=True)
    emotion_api_url = ConfigField(default='https://apis.paralleldots.com/v4/emotion')
    emotion_key = ConfigField(required=True)
    emotion_threshold = FloatConfig(default=0.45)

    # NER API
    use_ner = BooleanConfig(default=True)
    ner_api_url = ConfigField(
        default='https://apis.paralleldots.com/v4/ner')
    ner_key = ConfigField(required=True)
    ner_threshold = FloatConfig(default=0.4)

    use_paraphrase = BooleanConfig(default=False)
    paraphrase_url = ConfigField(default='https://quillbot.com/api/singleFlip')