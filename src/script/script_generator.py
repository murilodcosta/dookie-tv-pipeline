"""
Pipeline Step 3.1: DeepSeek Script & Metadata Generator
Calls DeepSeek V4 Flash API to generate structured JSON scripts for YouTube Shorts.
"""

import os
import json
import logging
import requests
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"


@dataclass
class ScenePrompt:
    scene_number: int
    animation_prompt: str
    narration_text: str
    duration_seconds: float = 5.0


@dataclass
class ShortScript:
    title: str
    description: str
    tags: List[str]
    mascot: str
    topic: str
    scenes: List[ScenePrompt]


class ScriptGenerator:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")

    def _build_system_prompt(self) -> str:
        return (
            "You are an expert children's content creator writing short, engaging scripts for YouTube Shorts.\n"
            "Channel: Dookie Tv. Audience: Toddlers and young kids (2-6 years old).\n"
            "Rule 1: Narration must use very simple words, short sentences (2-4 words max per caption screen).\n"
            "Rule 2: Title must be catchy, fun, under 100 characters, ending with '| Dookie Tv'.\n"
            "Rule 3: Produce exactly 2 to 3 scenes per video, totaling 15-30 seconds.\n"
            "Rule 4: Output valid JSON ONLY adhering to the requested schema."
        )

    def _build_user_prompt(self, topic: str, mascot: str) -> str:
        return (
            f"Generate a Short script featuring mascot '{mascot.capitalize()}' teaching/demonstrating topic '{topic}'.\n"
            "Respond ONLY with a JSON object containing the following keys:\n"
            "{\n"
            '  "title": "Short title under 100 chars | Dookie Tv",\n'
            '  "description": "Short description with #hashtags",\n'
            '  "tags": ["tag1", "tag2", "tag3"],\n'
            '  "scenes": [\n'
            "    {\n"
            '      "scene_number": 1,\n'
            '      "animation_prompt": "Action description for 3D animation (e.g. Mascot smiling and jumping happily)",\n'
            '      "narration_text": "Short 2-4 word sentence for narration",\n'
            '      "duration_seconds": 5.0\n'
            "    }\n"
            "  ]\n"
            "}"
        )

    def generate_script(self, topic: str, mascot: str, mock_mode: bool = True) -> ShortScript:
        """
        Generates a structured video script using DeepSeek API or mock fallback.
        """
        if mock_mode or not self.api_key:
            logger.info(f"[MOCK] ScriptGenerator: Generating mock script for mascot '{mascot}' & topic '{topic}'")
            return ShortScript(
                title=f"{mascot.capitalize()} Learns {topic.replace('_', ' ').capitalize()}! 🎨 | Dookie Tv",
                description=f"Join {mascot.capitalize()} on Dookie Tv as we learn about {topic}! #kids #dookietv #{topic}",
                tags=["kids", "learning", mascot.lower(), topic.lower(), "shorts", "dookietv"],
                mascot=mascot,
                topic=topic,
                scenes=[
                    ScenePrompt(
                        scene_number=1,
                        animation_prompt=f"3D mascot {mascot} smiling and waving happily in a sunny room",
                        narration_text=f"Hello friends! Today {mascot} learns {topic.replace('_', ' ')}!",
                        duration_seconds=5.0,
                    ),
                    ScenePrompt(
                        scene_number=2,
                        animation_prompt=f"Mascot {mascot} pointing excitedly at colorful objects",
                        narration_text="Look how wonderful! Can you count with me?",
                        duration_seconds=5.0,
                    ),
                ],
            )

        logger.info(f"Connecting to DeepSeek API for mascot '{mascot}' & topic '{topic}'...")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user", "content": self._build_user_prompt(topic, mascot)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7,
        }

        try:
            response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            res_data = response.json()
            content = res_data["choices"][0]["message"]["content"]
            parsed_json = json.loads(content)

            scenes = [
                ScenePrompt(
                    scene_number=s.get("scene_number", idx + 1),
                    animation_prompt=s.get("animation_prompt", ""),
                    narration_text=s.get("narration_text", ""),
                    duration_seconds=float(s.get("duration_seconds", 5.0)),
                )
                for idx, s in enumerate(parsed_json.get("scenes", []))
            ]

            return ShortScript(
                title=parsed_json.get("title", f"{mascot.capitalize()} Short | Dookie Tv"),
                description=parsed_json.get("description", ""),
                tags=parsed_json.get("tags", ["kids", "dookietv"]),
                mascot=mascot,
                topic=topic,
                scenes=scenes,
            )
        except Exception as e:
            logger.error(f"Error calling DeepSeek API: {e}. Falling back to mock script.")
            raise e
