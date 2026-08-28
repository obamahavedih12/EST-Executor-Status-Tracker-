import discord
from discord.ext import commands, tasks
from discord import Embed, Color
import aiohttp

from checker import WEAOChecker
from models import StatusReport, ExecutorResult, ExecutorStatus
from config_manager import ConfigManager
from logger import get_logger

log = get_logger("bot")


# ── Embed Builders ────────────────────────────────────────────────────────────

def _report_color(report: StatusReport) -> Color:
    if report.updating_count > 0:
        return Color.gold()
    if report.detected_count == len(report.results):
        return Color.red()
    return Color.green()


def build_report_embeds(report: StatusReport) -> list[Embed]:
    summary = (
        f"🟢 **{report.updated_count}** Updated  ·  "
        f"🟡 **{report.updating_count}** Updating  ·  "
        f"🔴 **{report.detected_count}** Detected  ·  "
        f"**{len(report.results)}** Total"
    )
    chunks = [report.results[i:i+25] for i in range(0, len(report.results), 25)]
    embeds = []
    for idx, chunk in enumerate(chunks):
        page  = f"({idx+1}/{len(chunks)})" if len(chunks) > 1 else ""
        embed = Embed(
            title       = f"⚙️ Executor Status Report {page}".strip(),
            description = summary if idx == 0 else "",
            color       = _report_color(report),
            timestamp   = report.generated_at
        )
        for result in chunk:
            field = result.to_embed_field()
            embed.add_field(name=field["name"], value=field["value"], inline=field["inline"])
        embed.set_footer(text="Source: weao.xyz  ·  UTC")
        embeds.append(embed)
    return embeds


def build_single_embed(result: ExecutorResult) -> Embed:
    color_map = {
        ExecutorStatus.UPDATED : Color.green(),
        ExecutorStatus.UPDATING: Color.gold(),
        ExecutorStatus.DETECTED: Color.red(),
        ExecutorStatus.UNKNOWN : Color.greyple(),
    }
    embed = Embed(title=f"⚙️ {result.name}", color=color_map[result.status], timestamp=result.fetched_at)
    embed.add_field(name="Status",   value=result.status.value,   inline=True)
    embed.add_field(name="Version",  value=f"`{result.version}`", inline=True)
    embed.add_field(name="Platform", value=result.platform,       inline=True)
    embed.add_field(name="Detected", value="Yes 🔴" if result.detected else "No 🟢", inline=True)
    embed.add_field(name="UNC",      value="✅" if result.unc_status else "❌",       inline=True)
    embed.add_field(name="Price",    value=result.cost,                               inline=True)

    if result.unc_percentage  is not None:
        embed.add_field(name="UNC %",  value=f"`{result.unc_percentage}%`",  inline=True)
    if result.sunc_percentage is not None:
        embed.add_field(name="sUNC %", value=f"`{result.sunc_percentage}%`", inline=True)

    features = []
    if result.decompiler   is not None: features.append(f"Decompiler: {'✅' if result.decompiler else '❌'}")
    if result.multi_inject is not None: features.append(f"Multi-Inject: {'✅' if result.multi_inject else '❌'}")
    if result.key_system   is not None: features.append(f"Key System: {'✅' if result.key_system else '❌'}")
    if features:
        embed.add_field(name="Features", value="\n".join(features), inline=False)

    links = []
    if result.website_link:  links.append(f"[Website]({result.website_link})")
    if result.discord_link:  links.append(f"[Discord]({result.discord_link})")
    if result.purchase_link: links.append(f"[Purchase]({result.purchase_link})")
    if links:
        embed.add_field(name="Links", value="  ·  ".join(links), inline=False)

    if result.updated_date:
        embed.set_footer(text=f"Last updated: {result.updated_date}  ·  weao.xyz")
    return embed


# ── Bot ───────────────────────────────────────────────────────────────────────

class StatusBot(commands.Bot):

    def __init__(self, cfg: ConfigManager):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=cfg.get("prefix", "!"), intents=intents)
        self.cfg     = cfg
        self.session: aiohttp.ClientSession | None = None

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        await self.add_cog(StatusCog(self))

    async def on_ready(self):
        log.info(f"Online as {self.user} ({self.user.id})")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="executor uptime · weao.xyz"
            )
        )

    async def close(self):
        if self.session:
            await self.session.close()
        await super().close()


class StatusCog(commands.Cog):

    def __init__(self, bot: StatusBot):
        self.bot              = bot
        self.cfg              = bot.cfg
        self._auto_channel_id = self.cfg.get("auto_refresh_channel")

        refresh = self.cfg.get("auto_refresh_seconds", 0)
        if refresh and refresh > 0:
            self.auto_refresh.change_interval(seconds=refresh)
            self.auto_refresh.start()

    def checker(self) -> WEAOChecker:
        return WEAOChecker(self.bot.session, timeout=self.cfg.get("timeout_seconds", 10))

    # ── Commands ──────────────────────────────────────────────────────────────

    @commands.command(name="status", aliases=["s"])
    async def cmd_status(self, ctx):
        msg    = await ctx.send("🔍 Fetching from **weao.xyz**...")
        report = await self.checker().fetch_all()
        if report is None:
            await msg.edit(content="❌ WEAO API unreachable or rate limited."); return
        embeds = build_report_embeds(report)
        await msg.edit(content=None, embed=embeds[0])
        for e in embeds[1:]:
            await ctx.send(embed=e)

    @commands.command(name="check", aliases=["c"])
    async def cmd_check(self, ctx, *, name: str):
        msg    = await ctx.send(f"🔍 Checking **{name}**...")
        result = await self.checker().fetch_one(name)
        if result is None:
            await msg.edit(content=f"❌ **{name}** not found or rate limited."); return
        await msg.edit(content=None, embed=build_single_embed(result))

    @commands.command(name="updated", aliases=["u"])
    async def cmd_updated(self, ctx):
        msg    = await ctx.send("🔍 Fetching updated executors...")
        report = await self.checker().fetch_all()
        if report is None:
            await msg.edit(content="❌ WEAO API unreachable or rate limited."); return
        report.results = [r for r in report.results if r.status == ExecutorStatus.UPDATED]
        if not report.results:
            await msg.edit(content="⚠️ No executors fully updated right now."); return
        embeds = build_report_embeds(report)
        await msg.edit(content=None, embed=embeds[0])
        for e in embeds[1:]: await ctx.send(embed=e)

    @commands.command(name="updating")
    async def cmd_updating(self, ctx):
        msg    = await ctx.send("🔍 Fetching updating executors...")
        report = await self.checker().fetch_all()
        if report is None:
            await msg.edit(content="❌ WEAO API unreachable or rate limited."); return
        report.results = [r for r in report.results if r.status == ExecutorStatus.UPDATING]
        if not report.results:
            await msg.edit(content="✅ No executors currently updating."); return
        embeds = build_report_embeds(report)
        await msg.edit(content=None, embed=embeds[0])
        for e in embeds[1:]: await ctx.send(embed=e)

    @commands.command(name="setrefresh")
    @commands.has_permissions(administrator=True)
    async def cmd_setrefresh(self, ctx, channel: discord.TextChannel):
        self._auto_channel_id = channel.id
        self.cfg.set("auto_refresh_channel", channel.id)
        await ctx.send(f"✅ Auto-refresh bound to {channel.mention}.")

    @commands.command(name="commands", aliases=["h"])
    async def cmd_help(self, ctx):
        embed = Embed(title="📖 Commands", color=Color.blurple(), description="Source: **weao.xyz**")
        embed.add_field(name="!status / !s",      value="Full status board",              inline=False)
        embed.add_field(name="!check [name]",     value="Detailed single executor view",  inline=False)
        embed.add_field(name="!updated / !u",     value="Only updated executors",         inline=False)
        embed.add_field(name="!updating",         value="Only updating executors",        inline=False)
        embed.add_field(name="!setrefresh #ch",   value="Auto-refresh channel (admin)",   inline=False)
        await ctx.send(embed=embed)

    # ── Auto Refresh ──────────────────────────────────────────────────────────

    @tasks.loop(seconds=300)
    async def auto_refresh(self):
        if not self._auto_channel_id:
            return
        channel = self.bot.get_channel(self._auto_channel_id)
        if not channel:
            return
        report = await self.checker().fetch_all()
        if not report:
            return
        for embed in build_report_embeds(report):
            await channel.send(embed=embed)

    @auto_refresh.before_loop
    async def before_auto_refresh(self):
        await self.bot.wait_until_ready()
