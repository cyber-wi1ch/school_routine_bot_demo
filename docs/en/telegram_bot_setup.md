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

A valid `vk_bot_token` is needed to send VK notifications when the morning duty role is assigned or revoked. If users in the current database have only Telegram IDs, these notifications are sent only to Telegram. The settings still require the `vk_bot_token` field: if VK is not used, set `vk_bot_token="unused"`. To send messages to VK, replace the placeholder with a [real token](vk_bot_setup.md).

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
