"""
Pipeline Step 3.6: Telegram Approval Gateway for Human Verification step (<10 min daily review).
Supports sending candidate Short videos to personal Telegram chat with inline interactive buttons:
- ✅ Approve & Publish to YouTube Shorts
- ❌ Reject
- 🔄 Redo Script / Redo Video sub-menu
Uses lightweight REST API calls to Telegram Bot API (https://api.telegram.org/bot<token>/).
"""

import os
import time
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class TelegramApprovalGateway:
    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        mock_mode: bool = True,
    ):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.mock_mode = mock_mode
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else ""

    def send_video_for_review(
        self,
        video_path: str,
        title: str,
        description: str,
        cost: float = 0.85,
        mascot: str = "dookie",
        topic: str = "numbers_1_to_10",
    ) -> bool:
        """
        Sends candidate Short video to personal Telegram chat with interactive inline buttons.
        Returns True if message sent successfully.
        """
        if self.mock_mode or not self.bot_token or not self.chat_id:
            logger.info(f"[MOCK] Telegram Gateway: Sent video '{title}' for review to Telegram chat.")
            logger.info("[MOCK] Automatically approved in Mock Mode.")
            return True

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found for Telegram review: {video_path}")

        mascot_emoji = "🐶" if mascot.lower() == "dookie" else ("🐱" if mascot.lower() == "mia" else "🐰")
        caption_text = (
            f"🎬 *Dookie TV — Prévia Diária para Aprovação*\n\n"
            f"📌 *Título:* {title}\n"
            f"{mascot_emoji} *Mascote:* {mascot.capitalize()} | 🏷️ *Tópico:* {topic}\n"
            f"💰 *Custo estimado do vídeo:* ${cost:.4f} USD\n\n"
            f"📝 *Descrição:* \n{description}\n"
        )

        # Inline Keyboard Buttons
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "✅ Aprovar & Publicar no YouTube", "callback_data": "approve"},
                    {"text": "❌ Rejeitar", "callback_data": "reject"},
                ],
                [
                    {"text": "📝 Refazer Roteiro", "callback_data": "redo_script"},
                    {"text": "🎬 Refazer Animação", "callback_data": "redo_video"},
                ],
            ]
        }

        url = f"{self.base_url}/sendVideo"
        logger.info(f"Sending video '{title}' ({os.path.getsize(video_path)} bytes) to Telegram chat {self.chat_id}...")

        with open(video_path, "rb") as video_file:
            files = {"video": video_file}
            data = {
                "chat_id": self.chat_id,
                "caption": caption_text[:1024],  # Telegram max caption length 1024
                "parse_mode": "Markdown",
                "reply_markup": str(reply_markup).replace("'", '"'),
            }
            response = requests.post(url, data=data, files=files, timeout=60)
            if response.status_code != 200:
                logger.error(f"Telegram API sendVideo failed ({response.status_code}): {response.text}")
                response.raise_for_status()

        logger.info("✅ Sent video preview successfully to Telegram chat!")
        return True

    def wait_for_user_decision(self, timeout_seconds: int = 600) -> str:
        """
        Polls Telegram getUpdates for inline button callback queries (approve, reject, redo_script, redo_video).
        Returns decision string: 'approve', 'reject', 'redo_script', 'redo_video', or 'timeout'.
        """
        if self.mock_mode or not self.bot_token:
            return "approve"

        logger.info(f"Aguardando decisão de aprovação no Telegram (timeout: {timeout_seconds}s)...")
        start_time = time.time()

        # Flush old updates first
        offset = 0
        try:
            flush_res = requests.get(f"{self.base_url}/getUpdates", params={"offset": -1}, timeout=10)
            if flush_res.status_code == 200:
                updates = flush_res.json().get("result", [])
                if updates:
                    offset = updates[-1]["update_id"] + 1
        except Exception as e:
            logger.warning(f"Failed to flush old Telegram updates: {e}")

        while time.time() - start_time < timeout_seconds:
            try:
                res = requests.get(f"{self.base_url}/getUpdates", params={"offset": offset, "timeout": 5}, timeout=10)
                if res.status_code == 200:
                    updates = res.json().get("result", [])
                    for update in updates:
                        offset = update["update_id"] + 1
                        if "callback_query" in update:
                            cb = update["callback_query"]
                            cb_id = cb["id"]
                            action = cb.get("data", "")
                            user_first_name = cb.get("from", {}).get("first_name", "Usuário")

                            logger.info(f"📩 Recebido clique no botão Telegram de '{user_first_name}': {action}")

                            # Answer callback query so button stops loading spinner in Telegram app
                            confirm_text = "✅ Vídeo Aprovado!" if action == "approve" else ("❌ Vídeo Rejeitado" if action == "reject" else f"🔄 Solicitado: {action}")
                            requests.post(f"{self.base_url}/answerCallbackQuery", json={"callback_query_id": cb_id, "text": confirm_text})

                            # Send text message back to chat confirming decision
                            msg_text = f"👍 *Decisão recebida de {user_first_name}:* `{action.upper()}`"
                            requests.post(f"{self.base_url}/sendMessage", json={"chat_id": self.chat_id, "text": msg_text, "parse_mode": "Markdown"})

                            return action

            except Exception as e:
                logger.warning(f"Error polling Telegram updates ({e}). Retrying in 3s...")

            time.sleep(2)

        logger.warning(f"Tempo limite de aprovação ({timeout_seconds}s) expirou sem resposta.")
        return "timeout"
