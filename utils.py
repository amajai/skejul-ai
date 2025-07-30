import sys 
import time
import re

def remove_markdown_code_blocks(text: str) -> str:
    # Removes triple backtick fences (e.g., ```json ... ```)
    return re.sub(r"```(?:json|python)?\s*([\s\S]*?)\s*```", r"\1", text).strip()

def loading_animation(stop_event):
    """Display a loading animation until stop_event is set."""
    chars = ["⢿", "⣻", "⣽", "⣾", "⣷", "⣯", "⣟", "⡿"]
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f'\rGenerating timetable structure... {chars[idx % len(chars)]}')
        sys.stdout.flush()
        idx += 1
        time.sleep(0.1)
    sys.stdout.write('\rGenerating timetable structure... ✓\n')
    sys.stdout.flush()