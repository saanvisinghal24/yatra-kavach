from abc import ABC, abstractmethod
from typing import Optional
import httpx
from app.config import get_settings

settings = get_settings()

class Notifier(ABC):
    @abstractmethod
    async def send_alert(self, title: str, message: str, severity: str, target: Optional[str] = None) -> bool:
        pass

class ConsoleNotifier(Notifier):
    async def send_alert(self, title: str, message: str, severity: str, target: Optional[str] = None) -> bool:
        # Personal information is never written to application logs.
        return True

class TelegramNotifier(Notifier):
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or settings.TELEGRAM_CHAT_ID

    async def send_alert(self, title: str, message: str, severity: str, target: Optional[str] = None) -> bool:
        if not self.bot_token or not self.chat_id:
            # Fall back to console if not configured
            return await ConsoleNotifier().send_alert(title, message, severity, target)

        telegram_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        text = f"*[{severity.upper()}] {title}*\n\n{message}\n\n_Yatra Kavach Safety System_"
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.post(telegram_url, json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": "Markdown"
                })
                return resp.status_code == 200
        except Exception:
            return False

def get_notifier() -> Notifier:
    if settings.NOTIFIER_CHANNEL == "telegram" and settings.TELEGRAM_BOT_TOKEN:
        return TelegramNotifier()
    return ConsoleNotifier()
