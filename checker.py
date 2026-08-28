import aiohttp
from models import ExecutorResult, StatusReport
from logger import get_logger

log = get_logger("checker")

WEAO_ALL     = "https://weao.xyz/api/status/exploits"
WEAO_SINGLE  = "https://weao.xyz/api/status/exploits/{name}"
WEAO_HEADERS = {"User-Agent": "WEAO-3PService"}


class WEAOChecker:

    def __init__(self, session: aiohttp.ClientSession, timeout: int = 10):
        self.session = session
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    async def _get(self, url: str):
        try:
            async with self.session.get(
                url, headers=WEAO_HEADERS, timeout=self.timeout, ssl=True
            ) as resp:
                if resp.status == 429:
                    data      = await resp.json()
                    remaining = data.get("rateLimitInfo", {}).get("remainingTime", "?")
                    log.warning(f"Rate limited. Retry in {remaining}s.")
                    return {"__rate_limited": True, "remaining": remaining}
                if resp.status != 200:
                    log.error(f"WEAO HTTP {resp.status} for {url}")
                    return None
                return await resp.json()
        except aiohttp.ClientError as e:
            log.error(f"WEAO request failed: {e}")
            return None

    async def fetch_all(self) -> StatusReport | None:
        raw = await self._get(WEAO_ALL)
        if raw is None or (isinstance(raw, dict) and raw.get("__rate_limited")):
            return None
        if not isinstance(raw, list):
            log.error(f"Unexpected shape: {type(raw)}")
            return None

        results = []
        for entry in raw:
            try:
                results.append(ExecutorResult.from_api(entry))
            except Exception as e:
                log.warning(f"Parse fail '{entry.get('title','?')}': {e}")

        results.sort(key=lambda r: (
            {"Updated": 0, "Updating": 1, "Detected": 2}.get(
                r.status.value.split()[-1], 9
            ),
            r.name.lower()
        ))
        log.info(f"Fetched {len(results)} executors.")
        return StatusReport(results=results)

    async def fetch_one(self, name: str) -> ExecutorResult | None:
        url = WEAO_SINGLE.format(name=name.lower().replace(" ", "%20"))
        raw = await self._get(url)
        if not raw or not isinstance(raw, dict) or raw.get("__rate_limited"):
            return None
        try:
            return ExecutorResult.from_api(raw)
        except Exception as e:
            log.error(f"Parse fail '{name}': {e}")
            return None
