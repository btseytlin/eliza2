from confi import BaseEnvironConfig, IntConfig, ConfigField


class BotConfig(BaseEnvironConfig):
    # Tgbot configs
    proxy_url = ConfigField()
    proxy_username = ConfigField()
    proxy_password = ConfigField()
    tg_token = ConfigField(required=True)

    # Eliza configs
    script_path = ConfigField(default='doctor.txt')