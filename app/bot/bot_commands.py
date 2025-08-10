import discord
from discord import app_commands
import os
import sys
sys.path.append(os.getcwd())
sys.path.append(os.path.abspath(os.path.dirname(__file__)))


from inventory.InventoryView import InventoryView
from inventory.InventoryPaginator import InventoryPaginator

async def setup(bot):
    @bot.tree.command(name="p", description="Pull a new Pixel Pet !")
    async def pull(interaction: discord.Interaction):
        discord_id = str(interaction.user.id)
        bot.player_service.create_account(discord_id)
        char = bot.gacha_service.pull()
        bot.player_service.add_character(discord_id, char)

        # Determine image path
        image_dir = os.path.join("assets", "characters", char.name)
        image_file = f"{char.name}_{char.element}.png"
        image_path = os.path.join(image_dir, image_file)

        if not os.path.exists(image_path):
            image_path = os.path.join("assets", "characters", "not_yet_available.png")

        # Send message with image
        file = discord.File(image_path, filename=os.path.basename(image_path))
        embed = discord.Embed(
            title="🎉 You pulled a new character!",
            description=f"**{char.name}** (Lv{char.level}, {char.element}, {char.rarity})\n❤️ {char.health} ⚔️ {char.attack}",
            color=discord.Color.gold()
        )
        embed.set_image(url=f"attachment://{os.path.basename(image_path)}")

        await interaction.response.send_message(embed=embed, file=file)

    @bot.tree.command(name="inventory", description="Show your character inventory")
    async def inventory(interaction: discord.Interaction):
        discord_id = str(interaction.user.id)
        bot.player_service.create_account(discord_id)
        inv = bot.player_service.get_inventory(discord_id)

        if not inv:
            await interaction.response.send_message(
                "📦 Your inventory is empty! Use `/p` to pull characters."
            )
            return

        paginator = InventoryPaginator(inv)
        view = InventoryView(paginator)
        embeds, files = paginator.get_embeds_and_files()

        message = await interaction.response.send_message(embeds=embeds, files=files, view=view)
        view.message = await interaction.original_response()
