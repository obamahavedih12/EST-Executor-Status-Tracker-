import asyncio
from bot import StatusBot
from config_manager import ConfigManager
from errors import handle_error
from logger import get_logger

log = get_logger("main")


async def main():
    cfg   = ConfigManager()
    token = cfg.token   # reads from BOT_TOKEN environment variable

    if not token:
        log.error(
            "No BOT_TOKEN environment variable set.\n"
            "  Railway: Settings → Variables → Add BOT_TOKEN\n"
            "  Local:   export BOT_TOKEN=your_token_here"
        )
        return

    bot = StatusBot(cfg)
    bot.on_command_error = handle_error

    log.info("Launching Executor Status Bot...")
    async with bot:
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
