# VK Bot Setup

[Русский](../vk_bot_setup.md) | English

[README](../../README.en.md) | [Telegram setup](telegram_bot_setup.md)

The bot acts on behalf of a community and receives messages through the Long Poll API.

## Obtain a Community Token

1. In **Communities**, create a community or open an existing one that you manage.
2. In community management, enable **Community messages** and **Bot capabilities** in the bot settings so that keyboards work.
3. Open **API usage > Access tokens > Create token**. Allow access to community messages, confirm token creation, and copy the token.
4. Under **API usage > Long Poll API**, enable Long Poll. Under **Event types**, select **Incoming message (`message_new`)** and save the settings.

This project requires a community token; this type of bot is described in the [VKBottle documentation](https://vkbottle.readthedocs.io/ru/latest/tutorial/first-bot/). VK menu labels and locations may differ.

## Connect It to the Project

Set the token in `.env` in the project root. For an instance that receives messages in VK, select `vk`:

```dotenv
vk_bot_token="COMMUNITY_TOKEN"
messenger_tag="vk"
```

Also fill in `bot_token` with a real [Telegram token](telegram_bot_setup.md): the current code creates a Telegram client even when running the VK bot.

For initial setup, follow the [first-start instructions](../../README.en.md#first-start-with-docker-compose). If the bot is already running, [apply the `.env` changes](deployment.md#docker-compose). Then send `Начать` (Start) to the community; the bot should ask for your full name.

Do not publish the token. If it is exposed, delete it in the community settings, create a new one, update `.env`, and apply the changes.
