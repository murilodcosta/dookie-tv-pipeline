"""
Telegram Approval Gateway for Human Verification step (<10 min daily review).
Supports inline buttons: Approve, Reject, Redo (with sub-menu).
"""

import logging

logger = logging.getLogger(__name__)


class TelegramApprovalGateway:
    def __init__(self, bot_token: str | None = None, chat_id: str | None = None, mock_mode: bool = True):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.mock_mode = mock_mode

    def send_video_for_review(self, video_path: str, title: str, description: str) -> bool:
        """
        Sends the candidate Short to the Telegram chat with inline approval buttons.
        In mock mode, automatically logs approval.
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Telegram Gateway: Sent video '{title}' for review to Telegram chat.")
            logger.info("[MOCK] Automatically approved in Mock Mode.")
            return True

        raise NotImplementedError("Real Telegram bot sending not configured yet.")
