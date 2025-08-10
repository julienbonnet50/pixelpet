import os
import discord
from discord.ui import View, Button

CHARS_PER_PAGE = 5

class InventoryPaginator:
    def __init__(self, characters):
        rarity_order = ["Legendary", "Rare", "Uncommon", "Common"]
        # Sort by rarity on init
        self.characters = sorted(characters, key=lambda c: rarity_order.index(c.rarity))
        self.page = 0
        self.max_page = (len(self.characters) - 1) // CHARS_PER_PAGE

    def get_page_characters(self):
        start = self.page * CHARS_PER_PAGE
        end = start + CHARS_PER_PAGE
        return self.characters[start:end]

    def next_page(self):
        if self.page < self.max_page:
            self.page += 1

    def prev_page(self):
        if self.page > 0:
            self.page -= 1

    def is_first_page(self):
        return self.page == 0

    def is_last_page(self):
        return self.page == self.max_page

    def get_embeds_and_files(self):
        embeds = []
        files = []
        start_index = self.page * CHARS_PER_PAGE
        page_chars = self.get_page_characters()

        for i, char in enumerate(page_chars, start=start_index + 1):
            img_path = os.path.join("assets", "characters", char.name, f"{char.name}_{char.element}.png")
            if not os.path.exists(img_path):
                img_path = os.path.join("assets", "characters", "not_yet_available.png")

            file_name = f"{char.name}_{i}.png"
            files.append(discord.File(img_path, filename=file_name))

            embed = discord.Embed(
                title=f"{i}. {char.name}",
                description=f"Lv{char.level} • {char.element} • {char.rarity}\n❤️ {char.health} ⚔️ {char.attack}",
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url=f"attachment://{file_name}")
            embeds.append(embed)

        return embeds, files
