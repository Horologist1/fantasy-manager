# remove_joy_interactions.py - Remove all interactions with category "Joy" from interactions_structured.json

import json
import os

JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "game", "data", "interactions", "interactions_structured.json")

def main():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    original = len(data)
    filtered = [i for i in data if "Joy" not in (i.get("categories") or [])]
    removed = original - len(filtered)
    
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)
    
    print(f"Removed {removed} Joy interactions. Remaining: {len(filtered)}")

if __name__ == "__main__":
    main()
