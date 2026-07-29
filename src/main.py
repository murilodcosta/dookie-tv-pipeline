"""
Main entrypoint for Dookie TV Automated Pipeline (Sprint 0 Baseline / Mock Pipeline).
Runs full end-to-end flow from script generation to approval and upload.
"""

import os
import json
import logging
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

from src.db.database import DatabaseManager
from src.script.script_generator import ScriptGenerator
from src.media.media_generator import MediaGenerator
from src.editor.video_editor import VideoEditor
from src.upload.telegram_bot import TelegramApprovalGateway
from src.upload.youtube_uploader import YouTubeUploader
from src.storage.r2_client import CloudflareR2Client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("dookie_tv_pipeline")


def load_topics_and_mascots(config_path: str = "config/topics.json"):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    topics = [t["id"] for t in data.get("topics", [])]
    mascots = [m["id"] for m in data.get("mascots", [])]
    return topics, mascots


def run_pipeline():
    mock_mode = os.getenv("ENABLE_MEDIA_MOCK", "false").lower() in ("true", "1", "yes")
    target_mascot_override = os.getenv("TARGET_MASCOT", "").strip() or None

    logger.info("🎬 Starting Dookie TV Automated Pipeline...")
    logger.info(f"⚙️ Configuration: ENABLE_MEDIA_MOCK={mock_mode}, TARGET_MASCOT={target_mascot_override}")

    # 1. Initialize Services
    db = DatabaseManager(db_path="data/pipeline.db")
    script_gen = ScriptGenerator()
    media_gen = MediaGenerator(mock_mode=mock_mode)
    editor = VideoEditor(mock_mode=mock_mode)
    telegram = TelegramApprovalGateway(mock_mode=mock_mode)
    uploader = YouTubeUploader(mock_mode=mock_mode)
    r2_client = CloudflareR2Client(mock_mode=mock_mode)

    # 2. Topic & Mascot Selection (7-day rule)
    available_topics, available_mascots = load_topics_and_mascots()
    mascot, topic = db.select_next_mascot_and_topic(
        available_topics=available_topics,
        available_mascots=available_mascots,
        override_mascot=target_mascot_override,
    )
    logger.info(f"✨ Selected Mascot: '{mascot}', Topic: '{topic}'")

    # 3. Generate Script & Metadata (3.1)
    script, deepseek_cost = script_gen.generate_script(topic=topic, mascot=mascot, mock_mode=mock_mode)
    logger.info(f"📝 Script generated: '{script.title}' ({len(script.scenes)} scene/one-shot). DeepSeek Cost: ${deepseek_cost:.6f}")

    # 4. Generate Media Assets (3.2 & 3.3)
    generated_video_clips = []
    generated_audio_clips = []
    segmind_tts_cost = 0.0
    
    mascot_asset_path = media_gen.get_mascot_asset(mascot)
    
    for scene in script.scenes:
        video_path = f"data/output/temp/scene_{scene.scene_number}.mp4"
        audio_path = f"data/output/temp/scene_{scene.scene_number}.mp3"

        media_gen.animate_video(image_path=mascot_asset_path, prompt=scene.animation_prompt, output_path=video_path)
        audio_path, tts_cost = editor.generate_narration(text=scene.narration_text, output_audio_path=audio_path)
        segmind_tts_cost += tts_cost

        generated_video_clips.append(video_path)
        generated_audio_clips.append(audio_path)

    segmind_video_cost = 0.85  # 10s 1080p Seedance 2.0 one-shot
    total_estimated_cost = deepseek_cost + segmind_video_cost + segmind_tts_cost

    # 5. Final Video Assembly (3.4 & 3.5)
    final_video_path = "data/output/final_short.mp4"
    subtitles = [s.narration_text for s in script.scenes]
    editor.assemble_video(
        video_clips=generated_video_clips,
        audio_clips=generated_audio_clips,
        subtitles=subtitles,
        output_video_path=final_video_path,
    )

    # 6. Standardized Upload copy to Cloudflare R2
    today_str = datetime.now().strftime("%Y-%m-%d")
    r2_destination_key = f"shorts/{today_str}_{mascot}_{topic}.mp4"
    r2_url = r2_client.upload_file(local_path=final_video_path, destination_key=r2_destination_key)

    # 7. Human Review Gate via Telegram (3.6)
    approved = telegram.send_video_for_review(
        video_path=final_video_path,
        title=script.title,
        description=script.description,
    )

    if not approved:
        logger.warning("❌ Video rejected during human review gate.")
        video_id = db.log_video(
            topic=topic,
            mascot=mascot,
            title=script.title,
            description=script.description,
            status="rejected",
            r2_url=r2_url,
            r2_key=r2_destination_key,
        )
        db.log_metrics(video_id=video_id, estimated_cost=total_estimated_cost)
        return

    # 8. YouTube Publishing (3.7)
    youtube_url = uploader.upload_short(
        video_path=final_video_path,
        title=script.title,
        description=script.description,
        tags=script.tags,
    )

    # 9. Log History & Cost Metrics in SQLite (3.8)
    video_id = db.log_video(
        topic=topic,
        mascot=mascot,
        title=script.title,
        description=script.description,
        status="approved",
        r2_url=r2_url,
        r2_key=r2_destination_key,
        youtube_url=youtube_url,
    )
    db.log_metrics(video_id=video_id, estimated_cost=total_estimated_cost)

    logger.info(f"🚀 Pipeline executed successfully! Video ID #{video_id} published at: {youtube_url}")
    logger.info(f"📊 Observability Report: Video ID #{video_id} | Total Estimated Cost: ${total_estimated_cost:.4f} USD")


if __name__ == "__main__":
    run_pipeline()
