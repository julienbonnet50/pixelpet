class Character:
    def __init__(self, 
            name: str,
            level: int, 
            element: str,
            star: int,
            attack: int, 
            health: int,
            rarity: str
        ):
        
        # Basic attributes
        self.name = name
        self.element = element
        self.rarity = rarity

        # Stats
        self.level = level
        self.star = star
        self.health = health
        self.attack = attack


    def level_up(self):
        self.level += 1
        print(f"{self.name} has leveled up to level {self.level}!")

    def __str__(self):
        return f"{self.name} (Lv{self.level} | {self.element} | {self.rarity}) ❤️ {self.health} ⚔️ {self.attack}"
