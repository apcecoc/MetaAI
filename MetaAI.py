__version__ = (1, 0, 0)

#       █████  ██████   ██████ ███████  ██████  ██████   ██████ 
#       ██   ██ ██   ██ ██      ██      ██      ██    ██ ██      
#       ███████ ██████  ██      █████   ██      ██    ██ ██      
#       ██   ██ ██      ██      ██      ██      ██    ██ ██      
#       ██   ██ ██       ██████ ███████  ██████  ██████   ██████

#              © Copyright 2025
#           https://t.me/apcecoc
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta developer: @apcecoc
# scope: hikka_only
# scope: hikka_min 1.2.10

from telethon.tl.types import Message
from .. import loader, utils
import aiohttp
import asyncio

@loader.tds
class MetaAIModule(loader.Module):
    """Интерактивный модуль общения с ИИ"""
    strings = {
        "name": "MetaAI",
        "api_error": "🚨 An error occurred while accessing the service: {}",
        "response_error": "🚨 Invalid response received: {}",
        "ai_response": "🤖 AI Response:\n{}",
        "id_cleared": "✅ Conversation ID cleared. A new conversation has started.",
        "missing_param": "❌ Missing required parameter: {}",
        "generating_response": "Generating response",
    }

    strings_ru = {
        "name": "MetaAI",
        "api_error": "🚨 Произошла ошибка при обращении к сервису: {}",
        "response_error": "🚨 Получен ошибочный ответ: {}",
        "ai_response": "🤖 Ответ ИИ:\n{}",
        "id_cleared": "✅ Идентификатор диалога очищен. Начат новый диалог.",
        "missing_param": "❌ Отсутствует обязательный параметр: {}",
        "generating_response": "Генерирую ответ",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "conversation_id", None, "Идентификатор диалога для продолжения беседы"
        )

    async def client_ready(self, client, db):
        self.client = client

    async def _animate_loading(self, message: Message):
        """Анимация из точек во время ожидания ответа"""
        dots = ""
        while not self.animation_done:
            dots = dots + "." if len(dots) < 4 else ""
            await message.edit(f"{self.strings['generating_response']}{dots}")
            await asyncio.sleep(0.5)

    @loader.command(
        ru_doc="<текст> - Отправить сообщение ИИ и получить ответ",
        en_doc="<text> - Send a message to AI and get a response"
    )
    async def metaaicmd(self, message: Message):
        args = utils.get_args_raw(message)

        if not args:
            await utils.answer(message, self.strings["missing_param"].format("text"))
            return

        url = "https://api.paxsenix.biz.id/ai/metaai"
        params = {"text": args}

        if self.config["conversation_id"]:
            params["conversation_id"] = self.config["conversation_id"]

        self.animation_done = False
        animation_task = asyncio.create_task(self._animate_loading(message))

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if not data.get("ok"):
                            await utils.answer(message, self.strings["response_error"].format(data.get("message", "Unknown error")))
                            return

                        self.config["conversation_id"] = data.get("external_conversation_id")

                        # Удаление лишней части текста из ответа
                        ai_message = data.get("message", "No response available.")
                        if "I am still improving my command of other languages" in ai_message:
                            ai_message = ai_message.split("\n\nI am still improving my command of other languages")[0]

                        self.animation_done = True
                        await utils.answer(message, self.strings["ai_response"].format(ai_message))
                    else:
                        await utils.answer(message, self.strings["api_error"].format(f"HTTP {response.status}"))
        except Exception as e:
            await utils.answer(message, self.strings["api_error"].format(str(e)))
        finally:
            self.animation_done = True
            animation_task.cancel()

    @loader.command(
        ru_doc="Очистить сохранённый идентификатор диалога для нового общения",
        en_doc="Clear the saved conversation ID for a new interaction"
    )
    async def clearidcmd(self, message: Message):
        self.config["conversation_id"] = None
        await utils.answer(message, self.strings["id_cleared"])
