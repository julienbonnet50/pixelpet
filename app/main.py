#!/usr/bin/env python3
"""
Scalable Tamagotchi Discord Bot
Main entry point and bot initialization
"""

import asyncio
import logging
import sys
from pathlib import Path

import discord
from discord.ext import commands

from config.settings import Settings
from config.database import DatabaseManager
from services.pet_service import PetService
from services.notification_service import NotificationService
from tasks.background_tasks import TaskScheduler
from utils.helpers import setup_logging

# Import command cogs
from commands.pet_commands import PetCommands
from commands.game_commands import GameCommands  
from commands.shop_commands import ShopCommands
from commands.info_commands import InfoCommands

class TamagotchiBot(commands.Bot):
    """Main bot class with initialization and cleanup"""
    
    def __init__(self):
        # Configure intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        super().__init__(
            command_prefix=self.get_prefix,
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        
        # Initialize core components
        self.settings = Settings()
        self.db_manager = None
        self.pet_service = None
        self.notification_service = None
        self.task_scheduler = None
        
        # Setup logging
        self.logger = setup_logging()
        
    async def get_prefix(self, bot, message):
        """Dynamic prefix support"""
        return ["/", "!tm ", "tamagotchi "]
    
    async def setup_hook(self):
        """Initialize services and load cogs"""
        try:
            self.logger.info("Starting bot initialization...")
            
            # Initialize database
            self.db_manager = DatabaseManager(self.settings.DATABASE_URL)
            await self.db_manager.initialize()
            
            # Initialize services
            self.pet_service = PetService(self.db_manager)
            self.notification_service = NotificationService(self)
            
            # Initialize task scheduler
            self.task_scheduler = TaskScheduler(
                self.pet_service, 
                self.notification_service
            )
            
            # Load command cogs
            await self.load_cogs()
            
            # Start background tasks
            await self.task_scheduler.start()
            
            self.logger.info("Bot initialization completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize bot: {e}")
            await self.close()
            sys.exit(1)
    
    async def load_cogs(self):
        """Load all command cogs"""
        cogs = [
            PetCommands(self),
            GameCommands(self),
            ShopCommands(self),
            InfoCommands(self)
        ]
        
        for cog in cogs:
            try:
                await self.add_cog(cog)
                self.logger.info(f"Loaded cog: {cog.__class__.__name__}")
            except Exception as e:
                self.logger.error(f"Failed to load cog {cog.__class__.__name__}: {e}")
    
    async def on_ready(self):
        """Bot ready event"""
        self.logger.info(f"Bot is ready! Logged in as {self.user}")
        self.logger.info(f"Connected to {len(self.guilds)} guilds")
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="over digital pets 🐣"
        )
        await self.change_presence(activity=activity)
    
    async def on_error(self, event, *args, **kwargs):
        """Global error handler"""
        self.logger.error(f"Error in event {event}", exc_info=True)
    
    async def on_command_error(self, ctx, error):
        """Command error handler"""
        if isinstance(error, commands.CommandNotFound):
            return
        
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Command on cooldown. Try again in {error.retry_after:.1f}s")
            return
        
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param}")
            return
        
        # Log unexpected errors
        self.logger.error(f"Command error in {ctx.command}: {error}", exc_info=True)
        await ctx.send("❌ An unexpected error occurred. Please try again later.")
    
    async def close(self):
        """Cleanup on bot shutdown"""
        self.logger.info("Shutting down bot...")
        
        if self.task_scheduler:
            await self.task_scheduler.stop()
        
        if self.db_manager:
            await self.db_manager.close()
        
        await super().close()
        self.logger.info("Bot shutdown complete")

async def main():
    """Main entry point"""
    bot = TamagotchiBot()
    
    try:
        await bot.start(bot.settings.DISCORD_TOKEN)
    except KeyboardInterrupt:
        await bot.close()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        await bot.close()
        sys.exit(1)

if __name__ == "__main__":
    # Ensure we're using the right event loop policy on Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())