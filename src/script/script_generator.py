"""
Pipeline Step 3.1: DeepSeek Script & Metadata Generator
Calls DeepSeek V4 Flash API to generate structured JSON scripts for YouTube Shorts (One-Shot continuous scene).
"""

import os
import json
import logging
import requests
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"


@dataclass
class ScenePrompt:
    scene_number: int
    animation_prompt: str
    narration_text: str
    duration_seconds: float = 10.0


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
            "Rule 1: Narration must use simple words, short sentences (2-4 words max per caption screen).\n"
            "Rule 2: Title must be catchy, fun, under 100 characters, ending with MAX 2 video-relevant hashtags (e.g. #learning #topic). Must NOT contain '| Dookie Tv'.\n"
            "Rule 3: Description can contain a short summary and more hashtags (e.g. #topic #learning #kids #shorts #dookietv).\n"
            "Rule 4: Produce EXACTLY 1 continuous one-shot scene per video (10 to 12 seconds total duration).\n"
            "Rule 5: Mascots NEVER speak human words. Dookie (dog) makes barks/woofs; Mia (cat) makes meows/purrs; Carrot (rabbit) makes squeaks/crunching. Narration text is spoken ONLY by an off-screen friendly child narrator voice.\n"
            "Rule 6: Animation prompt MUST start by referencing image 1 and image 2 (e.g. '[Mascot], the mascot character from image 1 and image 2, is sitting happily...'), mandating 3D Pixar animated cartoon style, smooth 3D render, NO realistic photo animals.\n"
            "Rule 7: Audio Prompt Details: Describe the full audio track clearly inside animation_prompt:\n"
            "  - Spoken Narration: Off-screen friendly child narrator voice speaking the narration text.\n"
            "  - Background Music: Upbeat, cheerful children's background music playing softly throughout.\n"
            "  - Mascot SFX: Mascot makes species-specific animal SFX (barks/meows/squeaks). NO mascot human words.\n"
            "Rule 8: Output valid JSON ONLY adhering to the requested schema."
        )

    def _build_user_prompt(self, topic: str, mascot: str) -> str:
        clean_topic = topic.replace("_", " ")
        mascot_cap = mascot.capitalize()
        sfx_desc = "happy barks and puppy woofs" if mascot.lower() == "dookie" else ("sweet meows and purrs" if mascot.lower() == "mia" else "soft squeaks and carrot crunching")

        return (
            f"Generate a continuous one-shot Short script featuring mascot '{mascot_cap}' teaching/demonstrating topic '{clean_topic}'.\n"
            "Respond ONLY with a JSON object containing the following keys:\n"
            "{\n"
            '  "title": "Fun Title Under 100 Chars #learning #' + topic.split("_")[0] + '",\n'
            '  "description": "Short friendly video summary. #' + topic + ' #learning #kids #shorts #dookietv",\n'
            '  "tags": ["kids", "shorts", "learning", "' + topic + '", "dookietv"],\n'
            '  "scenes": [\n'
            "    {\n"
            '      "scene_number": 1,\n'
            '      "animation_prompt": "Shot 1: ' + mascot_cap + ', the mascot character from image 1 and image 2, is sitting happily in a bright colorful room with a sunshine yellow background (#FFD166). ' + mascot_cap + ' waves excitedly with a big smile while demonstrating ' + clean_topic + '. Audio: Off-screen friendly child voice narrates clearly: \'Look! ' + mascot_cap + ' learns ' + clean_topic + '!\'. Background Music: Upbeat cheerful children\'s background music playing consistently throughout. Mascot SFX: ' + mascot_cap + ' makes ' + sfx_desc + '. Smooth 3D Pixar animation, cute 3D character style.",\n'
            '      "narration_text": "Look! ' + mascot_cap + ' learns ' + clean_topic + '!",\n'
            '      "duration_seconds": 10.0\n'
            "    }\n"
            "  ]\n"
            "}"
        )

    def calculate_cost(self, usage: Dict[str, Any]) -> float:
        """
        Calculates exact DeepSeek V4 Flash API cost:
        - 1M Input Tokens (Cache Hit): $0.0028 ($0.0000000028/token)
        - 1M Input Tokens (Cache Miss): $0.14 ($0.00000014/token)
        - 1M Output Tokens: $0.28 ($0.00000028/token)
        """
        if not usage:
            return 0.0005  # Fallback estimate

        prompt_cache_hit = usage.get("prompt_cache_hit_tokens", 0)
        prompt_cache_miss = usage.get("prompt_cache_miss_tokens", usage.get("prompt_tokens", 0) - prompt_cache_hit)
        completion_tokens = usage.get("completion_tokens", 0)

        hit_cost = prompt_cache_hit * (0.0028 / 1_000_000)
        miss_cost = max(0, prompt_cache_miss) * (0.14 / 1_000_000)
        output_cost = completion_tokens * (0.28 / 1_000_000)

        return hit_cost + miss_cost + output_cost

    def generate_script(self, topic: str, mascot: str, mock_mode: bool = True) -> Tuple[ShortScript, float]:
        """
        Generates a structured video script using DeepSeek API or mock fallback, returning (script, cost).
        """
        clean_topic = topic.replace("_", " ")
        topic_tag = topic.replace("_", "")
        mascot_cap = mascot.capitalize()
        sfx_desc = "happy barks and puppy woofs" if mascot.lower() == "dookie" else ("sweet meows and purrs" if mascot.lower() == "mia" else "soft squeaks and carrot crunching")

        if mock_mode or not self.api_key:
            logger.info(f"[MOCK] ScriptGenerator: Generating one-shot mock script for mascot '{mascot}' & topic '{topic}'")
            mock_script = ShortScript(
                title=f"{mascot_cap} Learns {clean_topic.capitalize()}! 🎨 #learning #{topic_tag}",
                description=f"Join {mascot_cap} on Dookie Tv as we learn about {clean_topic}! #{topic_tag} #learning #kids #shorts #dookietv",
                tags=["kids", "shorts", "learning", mascot.lower(), topic.lower()],
                mascot=mascot,
                topic=topic,
                scenes=[
                    ScenePrompt(
                        scene_number=1,
                        animation_prompt=f"Shot 1: {mascot_cap}, the mascot character from image 1 and image 2, is sitting happily in a bright colorful room with a sunshine yellow background (#FFD166). {mascot_cap} smiles and demonstrates {clean_topic}. Audio: Off-screen friendly child voice narrates: 'Look! {mascot_cap} learns {clean_topic}!'. Background Music: Upbeat cheerful children's background music playing consistently throughout. Mascot SFX: {mascot_cap} makes {sfx_desc}. Smooth 3D Pixar animation, cute 3D character style.",
                        narration_text=f"Look! {mascot_cap} learns {clean_topic}!",
                        duration_seconds=10.0,
                    ),
                ],
            )
            return mock_script, 0.0005

        logger.info(f"Connecting to DeepSeek API for mascot '{mascot}' & topic '{topic}' (One-Shot mode)...")
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
            
            usage = res_data.get("usage", {})
            real_cost = self.calculate_cost(usage)

            scenes = [
                ScenePrompt(
                    scene_number=s.get("scene_number", 1),
                    animation_prompt=s.get("animation_prompt", ""),
                    narration_text=s.get("narration_text", ""),
                    duration_seconds=float(s.get("duration_seconds", 10.0)),
                )
                for idx, s in enumerate(parsed_json.get("scenes", []))
            ]

            if not scenes:
                scenes = [
                    ScenePrompt(
                        scene_number=1,
                        animation_prompt=f"Shot 1: {mascot_cap}, the mascot character from image 1 and image 2, is dancing happily and teaching {clean_topic}. Audio: Off-screen friendly child voice narrates: 'Let's learn {clean_topic}!'. Background Music: Upbeat cheerful children's background music. Mascot SFX: {mascot_cap} makes {sfx_desc}. Smooth 3D Pixar animation, cute 3D character style.",
                        narration_text=f"Let's learn {clean_topic} together!",
                        duration_seconds=10.0,
                    )
                ]

            raw_title = parsed_json.get("title", f"{mascot_cap} Short")
            clean_title = raw_title.replace("| Dookie Tv", "").replace("| Dookie TV", "").strip()

            script = ShortScript(
                title=clean_title,
                description=parsed_json.get("description", f"Join {mascot_cap} for fun learning! #{topic_tag} #learning #kids #shorts #dookietv"),
                tags=parsed_json.get("tags", ["kids", "shorts", "learning"]),
                mascot=mascot,
                topic=topic,
                scenes=scenes,
            )
            return script, real_cost
        except Exception as e:
            logger.error(f"Error calling DeepSeek API: {e}. Falling back to mock script.")
            raise e
