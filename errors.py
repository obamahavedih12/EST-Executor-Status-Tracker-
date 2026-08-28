from discord.ext import commands
from logger import get_logger

log = get_logger("errors")


async def handle_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 Insufficient permissions.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ Missing `{error.param.name}`. Use `!commands` for help.")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        log.error(f"Unhandled [{ctx.command}]: {error}", exc_info=error)
        await ctx.send("💥 Unexpected error. Check logs.")
