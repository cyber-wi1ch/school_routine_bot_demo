# Telegram Bot Setup

[Русский](../telegram_bot_setup.md) | English

[README](../../README.en.md) | [VK setup](vk_bot_setup.md)

## Obtain a Token

Open [@BotFather](https://t.me/BotFather).

- **New bot:** send `/newbot`, enter a display name and an available username ending in `bot`, such as `school_routine_demo_bot`. Copy the token from BotFather's reply.
- **Existing bot:** send `/mybots`, select the bot, open **API Token**, and copy the current token.

## Connect It to the Project

Set the token in `.env` in the project root. For an instance that receives messages in Telegram, select `tg`:

```dotenv
bot_token="TOKEN_FROM_BOTFATHER"
messenger_tag="tg"
```

The settings also require `vk_bot_token`. To support all notifications, use a valid test VK community token. If VK is not used, a placeholder in this field lets you test only some scenarios. See [how to obtain a VK token](vk_bot_setup.md).

For initial setup, follow the [first-start instructions](../../README.en.md#first-start-with-docker-compose). If the bot is already running, [apply the `.env` changes](deployment.md#docker-compose). Then open your bot and send `/start`; it should ask for your full name.

## Replace a Token

If a token has been exposed or needs replacing:

1. Send `/revoke` to @BotFather and select the bot. The old token stops working.
2. Save the new token in `bot_token` in `.env` on every server that uses it.
3. Apply the changes from the project directory on each affected server:

```bash
docker compose up -d --no-build school-routine-bot
```

Do not publish the token or commit `.env` to Git.
