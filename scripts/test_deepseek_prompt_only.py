"""
Targeted test script to call real DeepSeek V4 Flash API (mock_mode=False)
and inspect the detailed Multi-Shot prompt generated for Segmind Seedance 2.0.
Does NOT call Segmind or spend any video credits.
"""

import os
import sys
import logging
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv(override=True)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.script.script_generator import ScriptGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    logger.info("Starting Real DeepSeek API Multi-Shot Prompt Test (mock_mode=False)...")
    
    script_gen = ScriptGenerator()
    script, cost = script_gen.generate_script(topic="numbers_1_to_10", mascot="dookie", mock_mode=False)

    print("\n" + "=" * 80)
    print(f"TITLE: {script.title}")
    print(f"DESCRIPTION: {script.description}")
    print(f"TAGS: {script.tags}")
    print(f"TOTAL DURATION: {script.total_duration_seconds} seconds")
    print(f"DEEPSEEK COST: ${cost:.6f} USD")
    print("=" * 80)
    print("\nSEGMIND SEEDANCE 2.0 ANIMATION PROMPT:")
    print("-" * 80)
    print(script.animation_prompt)
    print("-" * 80)
    print("\nSPOKEN NARRATION TEXT:")
    print(script.narration_text)
    print("\nSUBTITLES MAPPING:")
    for sub in script.subtitles:
        print(f"  [{sub.start:.1f}s - {sub.end:.1f}s]: {sub.text}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
