
import discord
from discord.ui import View, Button
import sys
import os
sys.path.append(os.getcwd())
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.abspath(os.path.dirname(__file__))))


from app.bot.inventory.InventoryPaginator import InventoryPaginator
class InventoryView(View):
    def __init__(self, paginator: InventoryPaginator):
        super().__init__(timeout=120)
        self.paginator = paginator

        # Disable buttons initially as needed
        self.prev_button.disabled = self.paginator.is_first_page()
        self.next_button.disabled = self.paginator.is_last_page()

    async def update_message(self, interaction: discord.Interaction):
        embeds, files = self.paginator.get_embeds_and_files()
        await interaction.message.edit(embeds=embeds, files=files, view=self)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: Button):
        self.paginator.prev_page()
        self.prev_button.disabled = self.paginator.is_first_page()
        self.next_button.disabled = self.paginator.is_last_page()
        await self.update_message(interaction)
        await interaction.response.defer()

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        self.paginator.next_page()
        self.prev_button.disabled = self.paginator.is_first_page()
        self.next_button.disabled = self.paginator.is_last_page()
        await self.update_message(interaction)
        await interaction.response.defer()

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)