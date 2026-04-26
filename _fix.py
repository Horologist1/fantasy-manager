import os, sys

fp = os.path.join("C:", os.sep, "Users", "Usuario", "Desktop", "SNS", "FantasyManager", "fantasy-manager", "game", "data", "interactions", "interactions_training.json")
with open(fp, "r", encoding="utf-8") as f:
    content = f.read()

print("File loaded")
