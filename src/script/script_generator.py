"""
Script Generator module calling DeepSeek API for structured Short scripts.
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class ScenePrompt:
    scene_number: int
    image_prompt: str
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
        self.api_key = api_key

    def generate_script(self, topic: str, mascot: str) -> ShortScript:
        """
        Generates a structured video script using DeepSeek API or mock data.
        """
        return ShortScript(
            title=f"{mascot.capitalize()} Learns {topic.replace('_', ' ').capitalize()}! 🎨 | Dookie Tv",
            description=f"Join {mascot.capitalize()} on Dookie Tv as we learn about {topic}!",
            tags=["kids", "learning", mascot.lower(), topic.lower(), "shorts"],
            mascot=mascot,
            topic=topic,
            scenes=[
                ScenePrompt(
                    scene_number=1,
                    image_prompt=f"Cute 3D mascot {mascot} smiling in a bright room, high quality 3d render",
                    narration_text=f"Hello friends! Today {mascot} is learning about {topic}!",
                    duration_seconds=5.0,
                ),
                ScenePrompt(
                    scene_number=2,
                    image_prompt=f"Mascot {mascot} pointing happily at vibrant colors, 3d animation style",
                    narration_text="Look at how wonderful this is! Can you count with me?",
                    duration_seconds=5.0,
                ),
            ],
        )
