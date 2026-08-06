"""
Targeted test script to call real DeepSeek V4 Flash API (mock_mode=False)
and inspect the detailed One-Shot prompt generated for Segmind Seedance 2.0 / Nano Banana Pro.
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
    mascot = sys.argv[1] if len(sys.argv) > 1 else "mia"
    topic = sys.argv[2] if len(sys.argv) > 2 else "colors"

    logger.info(f"Starting Real DeepSeek API One-Shot Prompt Test for mascot '{mascot}' & topic '{topic}'...")
    
    script_gen = ScriptGenerator()
    script, cost = script_gen.generate_script(topic=topic, mascot=mascot, mock_mode=False)

    print("\n" + "=" * 80)
    print(f"TITLE: {script.title}")
    print(f"MASCOT: {script.mascot} | TOPIC: {script.topic}")
    print(f"TOTAL DURATION: {script.total_duration_seconds} seconds")
    print(f"DEEPSEEK COST: ${cost:.6f} USD")
    print("=" * 80)
    print("\nPROMPT GERADO (PRONTO PARA COPIAR E COLAR NO NANO BANANA PRO):")
    print("-" * 80)
    print(script.animation_prompt)
    print("-" * 80)
    print("\nDESCRIPTION:")
    print(script.description)
    print("\nSPOKEN NARRATION TEXT:")
    print(script.narration_text)
    print("\nSUBTITLES MAPPING:")
    for sub in script.subtitles:
        print(f"  [{sub.start:.1f}s - {sub.end:.1f}s]: {sub.text}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
