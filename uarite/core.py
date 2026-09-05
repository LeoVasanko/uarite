"""User-Agent parsing."""

import re
from dataclasses import dataclass
from functools import lru_cache

from .bots import BOTS, KIND_LABEL, LABELED
from .clients import BROWSERS, SAMSUNG, SAMSUNG_SERIES


@dataclass(frozen=True)
class UA:
    pretty: str
    engine: str
    os: str
    bot: str
    kind: str
    url: str


#: Fallback for unknown crawlers: a product token whose name says so.
BOT_TOKEN = re.compile(
    r"[^\s();/]*(?:bot|spider|crawl|scan|verif|check)[^\s();/]*", re.IGNORECASE
)

#: A "+https://…" pointer is a crawler tell; real browsers carry no URL.
URL = re.compile(r"\+\s*(https?://[^\s;)]+)")
ANY_URL = re.compile(r"(https?://[^\s;)]+)")

#: Crawler name next to the info URL: "compatible; Page2RSS/0.7; +http://…".
COMPATIBLE_NAME = re.compile(r"compatible;\s*([^;/()]+?)(?:/[\d.vx]+)?\s*;")

#: Name from an info URL's host when no product token is available.
HOST = re.compile(r"https?://(?:www\.)?([^/\s;)]+)")

#: Android model token: "Android 15; SM-S918B)", "Android 12; Pixel 6; Build/…".
ANDROID_MODEL = re.compile(r"Android [\d.]+; ([^;()]+?)(?:;|\)| Build/)")

#: All known-bot substrings in one compiled pass — much faster than 50
#: individual ``in`` checks on long UAs.
BOTS_RE = re.compile("|".join(map(re.escape, BOTS)))


def url(ua: str) -> str:
    """The crawler's info URL from the UA, or "" (mailto: is not a URL)."""
    m = URL.search(ua) or ANY_URL.search(ua)
    return m.group(1) if m else ""


def bot(ua: str) -> tuple[str, str]:
    """(display name, kind) of the crawler/previewer the UA claims."""
    low = ua.lower()
    m = BOTS_RE.search(low)
    if m:
        return BOTS[m.group(0)]
    # Cheap keyword gates keep the regexes off the hot path.
    if any(k in low for k in ("bot", "spider", "crawl", "scan", "verif", "check")):
        m = BOT_TOKEN.search(ua)
        if m:
            name = m.group(0).strip(";")
            return name[:1].upper() + name[1:], "spider"
    # An info URL in the UA is a crawler convention.  Name it from the
    # "compatible; Name/x" token, else the first product token, else the
    # URL's host.
    if "://" in ua:
        name = ""
        m = COMPATIBLE_NAME.search(ua)
        if m:
            name = m.group(1).strip()
        elif not ua.startswith("Mozilla"):
            name = ua.split()[0].split("/")[0]
        if not name or name.lower().startswith(("mozilla", "msie")):
            m = HOST.search(ua)
            name = m.group(1) if m else ""
        if name:
            return name[:1].upper() + name[1:], "spider"
    return "", ""


def version(ua: str, token: str) -> str:
    """Major version of a ``token/x.y`` product in the UA, or ""."""
    m = re.search(re.escape(token) + r"/(\d+)", ua)
    return m.group(1) if m else ""


def browser(ua: str) -> str:
    """``Browser/major`` for the browsers we care to distinguish."""
    for token, name in BROWSERS:
        ver = version(ua, token)
        if ver:
            return f"{name}/{ver}"
    if "Safari/" in ua:
        ver = version(ua, "Version")
        return f"Safari/{ver}" if ver else "Safari"
    return ""


#: Engines that differ from the Chromium default for recognized browsers.
ENGINES = {"Firefox": "Gecko", "LibreWolf": "Gecko", "Safari": "Safari"}


def engine(b: str) -> str:
    """Engine for a ``Browser/major`` result; Chromium is the modern default."""
    name = b.split("/")[0]
    return ENGINES.get(name, "Chromium" if name else "")


def os(ua: str) -> str:
    """Desktop OS name, or "" when not recognizable."""
    if "Windows NT" in ua:
        return "Windows"
    if "Mac OS X" in ua:
        return "macOS"
    if "Linux" in ua or "X11" in ua:
        return "Linux"
    if "Windows" in ua:
        return "Windows"
    if "Darwin" in ua:
        return "macOS"
    return ""


def model_name(model: str) -> str:
    """Human-readable phone name for an Android model code.

    Returns the input unchanged when nothing is known about it (Pixel and
    most other brands already send readable names).
    """
    if model.startswith("SM-"):
        # Strip the region/carrier suffix: SM-S918B -> SM-S918, and the
        # Chinese/HK variant's trailing zero: SM-S9370 -> SM-S937.
        code = re.sub(r"[A-Z]{1,2}$", "", model)
        if code not in SAMSUNG and code.endswith("0"):
            code = code[:-1]
        if code in SAMSUNG:
            return SAMSUNG[code]
        series = SAMSUNG_SERIES.get(code[:4])
        if series:
            return series
    return model


def uaparse(ua: str) -> UA:
    """Parse a User-Agent string into a compact ``UA`` record.

    ``pretty`` is "" for empty/missing UAs and the original string when
    nothing is recognized.

    Only the browser path is cached: real visitors repeat (cache hits),
    while crawlers and scripts are mostly one-hit wonders whose entries
    would just flush the cache.
    """
    if not ua or not ua.strip() or ua in ("-", "null"):
        return UA("", "", "", "", "", "")
    name, kind = bot(ua)
    if name:
        # The browser/OS in crawler UAs is a disguise; the bot identity is
        # the relevant information, so ``engine`` and ``os`` are left empty.
        label = KIND_LABEL.get(kind, "") if name in LABELED else ""
        pretty = f"{name} ({label})" if label else name
        return UA(pretty, "", "", name, kind, url(ua))
    return _parse_client(ua)


@lru_cache(maxsize=1024)
def _parse_client(ua: str) -> UA:
    """Browser/client parsing behind the cache; ``uaparse`` filters bots out."""

    # Non-browser HTTP clients ("python-requests/2.32.5", "curl/8.0",
    # "pip/24.3.1 {json…}"): the first product token, plus the OS when
    # their payload mentions one in free text.
    if not ua.startswith("Mozilla"):
        token = ua.split()[0]
        pretty = token if "/" in token else ua
        os_name = os(ua)
        if os_name and os_name not in pretty:
            pretty = f"{pretty} {os_name}"
        return UA(pretty, "", os_name, "", "", "")

    # HarmonyOS carries an "Android" compatibility token, so it must be
    # detected before Android.
    if "OpenHarmony" in ua or "HarmonyOS" in ua or "ArkWeb" in ua:
        b = browser(ua)
        return UA(
            f"{b} HarmonyOS" if b else "HarmonyOS", "ArkWeb", "HarmonyOS",
            "", "browser", "",
        )

    if "iPhone" in ua or "iPad" in ua:
        device = "iPhone" if "iPhone" in ua else "iPad"
        m = re.search(r"OS (\d+)", ua)
        pretty = f"{device} iOS {m.group(1)}" if m else device
        return UA(pretty, "Safari", "iOS", "", "browser", "")

    m = re.search(r"Android ([\d.]+)", ua)
    if m:
        b = browser(ua)
        mm = ANDROID_MODEL.search(ua)
        token = mm.group(1).strip() if mm else ""
        if token == "K":
            # Chrome's reduced UA freezes both: "Android 10; K".  Neither
            # is real — report just the OS.
            parts = [p for p in (b, "Android") if p]
        else:
            # Firefox sends the form factor ("Mobile"/"Tablet") in the
            # model slot.  A known model replaces the OS.
            model = ""
            if token and token not in ("wv", "Mobile", "Tablet"):
                model = model_name(token)
            parts = [p for p in (b, model or f"Android {m.group(1)}") if p]
        return UA(" ".join(parts), engine(b), "Android", "", "browser", "")

    b = browser(ua)
    os_name = os(ua)
    pretty = f"{b} {os_name}".strip()
    return UA(pretty or ua, engine(b), os_name, "", "browser", "")


def is_bot(ua: str) -> bool:
    """True when the UA claims a crawler or link-preview identity."""
    return bool(uaparse(ua).bot)
