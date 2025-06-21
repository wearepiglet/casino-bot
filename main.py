import asyncio
import os
from bot import GamblingBot
from dotenv import load_dotenv
load_dotenv()

async def main():
    """Main entry point for the Discord gambling bot."""
    # Get bot token from environment variable
    token = os.getenv("DISCORD_TOKEN")
    
    if not token:
        print("Error: DISCORD_TOKEN environment variable not set!")
        print("Please set your Discord bot token as an environment variable.")
        return
    
    # Create and run the bot
    bot = GamblingBot()
    
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        print("\nBot shutdown requested...")
    except Exception as e:
        print(f"Error starting bot: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
