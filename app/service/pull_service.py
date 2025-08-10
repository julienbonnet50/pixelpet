import random
import csv
import os
from app.model.Character import Character

class PullService:
    def __init__(self):
        base_dir = os.path.dirname(__file__)  # location of pull_service.py
        csv_path = os.path.join(base_dir, "..", "data", "characters.csv")
        csv_path = os.path.abspath(csv_path)
        self.gacha_pool = []
        self.load_characters(csv_path)

    def load_characters(self, csv_path):
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Character data file not found: {csv_path}")
        
        with open(csv_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    char = Character(
                        name=row["name"],
                        level=int(row["level"]),
                        element=row["element"],
                        attack=int(row["attack"]),
                        health=int(row["health"]),
                        rarity=row["rarity"],
                        star=int(row["star"])
                    )
                    self.gacha_pool.append(char)
                except KeyError as e:
                    raise ValueError(f"Missing expected column in CSV: {e}")
                except ValueError:
                    raise ValueError(f"Invalid data format in row: {row}")

    def pull(self):
        if not self.gacha_pool:
            raise RuntimeError("No characters loaded in gacha pool.")
        return random.choice(self.gacha_pool)
