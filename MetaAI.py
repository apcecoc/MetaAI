__version__ = (1, 0, 1)

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
import re


@loader.tds
class MetaAIModule(loader.Module):
    """Interactive AI Communication Module"""
    strings = {
        "name": "MetaAI",
        "api_error": "<b>🚨 An error occurred while accessing the service:</b> {}",
        "response_error": "<b>🚨 Invalid response received:</b> {}",
        "ai_response": "<b>🤖 AI Response:</b><br>{}",
        "id_cleared": "<b>✅ Conversation ID cleared.</b> A new conversation has started.",
        "missing_param": "<b>❌ Missing required parameter:</b> {}",
        "generating_response": "<b>Generating response</b>",
    }

    strings_ru = {
        "name": "MetaAI",
        "api_error": "<b>🚨 Произошла ошибка при обращении к сервису:</b> {}",
        "response_error": "<b>🚨 Получен ошибочный ответ:</b> {}",
        "ai_response": "<b>🤖 Ответ ИИ:</b><br>{}",
        "id_cleared": "<b>✅ Идентификатор диалога очищен.</b> Начат новый диалог.",
        "missing_param": "<b>❌ Отсутствует обязательный параметр:</b> {}",
        "generating_response": "<b>Генерирую ответ</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "conversation_id", None, "Conversation ID for continuing chats"
        )

    async def client_ready(self, client, db):
        self.client = client

    async def _animate_loading(self, message: Message):
        """Animation while waiting for a response"""
        dots = ""
        while not self.animation_done:
            dots = dots + "." if len(dots) < 4 else ""
            await message.edit(f"{self.strings['generating_response']}{dots}")
            await asyncio.sleep(0.5)

    def _markdown_to_html(self, text: str) -> str:
        """
        Convert Markdown to HTML manually.
        """
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"_(.+?)_", r"<i>\1</i>", text)
        text = re.sub(r"^# (.+)", r"<h1>\1</h1>", text, flags=re.MULTILINE)
        text = re.sub(r"^## (.+)", r"<h2>\1</h2>", text, flags=re.MULTILINE)
        text = re.sub(r"^### (.+)", r"<h3>\1</h3>", text, flags=re.MULTILINE)
        text = re.sub(
            r"```(\w+)?\n([\s\S]*?)```",
            lambda m: f"<pre><code class='{m.group(1) or 'plaintext'}'>{utils.escape_html(m.group(2))}</code></pre>",
            text,
        )
        text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
        return text

    @loader.command(
        ru_doc="<текст> - Отправить сообщение ИИ и получить ответ",
        en_doc="<text> - Send a message to AI and get a response"
    )
    async def metaai(self, message: Message):
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
                            await utils.answer(
                                message, self.strings["response_error"].format(data.get("message", "Unknown error"))
                            )
                            return

                        self.config["conversation_id"] = data.get("external_conversation_id")
                        ai_message = data.get("message", "No response available.")
                        if "I am still improving my command of other languages" in ai_message:
                            ai_message = ai_message.split("\n\nI am still improving my command of other languages")[0]

                        ai_message_html = self._markdown_to_html(ai_message)
                        self.animation_done = True
                        await utils.answer(message, self.strings["ai_response"].format(ai_message_html))
                    else:
                        await utils.answer(
                            message, self.strings["api_error"].format(f"HTTP {response.status}")
                        )
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
