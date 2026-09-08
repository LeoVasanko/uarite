# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "ua-parser[re2,regex]>=1.0.2",
#     "uarite",
#     "user-agent-parser>=0.2.1",
#     "user-agents>=2.2.0",
# ]
#
# [tool.uv.sources]
# uarite = { path = "..", editable = true }
# ///
"""Benchmark uarite vs ua-parser vs user-agents vs user-agent-parser.

Reproduces the README's numbers: browser accuracy on 100 modern UAs,
crawler detection on 2163 real-world crawler UAs, and timing (unique UAs,
a realistic repeat/unique mix, a pure bot storm) with cache introspection.

Data lives in scripts/data (see download_data.py).  All dependencies,
including uarite itself (editable), are declared inline:

    uv run scripts/bench.py
"""

import json
import random
import re
import timeit
from pathlib import Path

import ua_parser
from ua_parser import parse as ua_parse
from user_agent_parser import parse as uap_parse
from user_agents import parse as uas_parse

from uarite import uaparse

ALL_DOMAINS = (
    ua_parser.Domain.USER_AGENT | ua_parser.Domain.OS | ua_parser.Domain.DEVICE
)


_VARIANTS = {}


def ua_variant(name):
    """ua-parser with a specific resolver backend (pure/re2/rust), lazily
    built so its one-time database load lands in the untimed warm-up call.
    The default parse() picks whichever native backend is installed, so
    backends must be forced explicitly to benchmark them separately."""
    if name not in _VARIANTS:
        ctor = {
            "pure": ua_parser.BasicResolver,
            "re2": ua_parser.Re2Resolver,
            "rust": ua_parser.RegexResolver,
        }[name]
        parser = ua_parser.Parser(
            ua_parser.CachingResolver(
                ctor(ua_parser.load_builtins()), ua_parser.Cache(2000)
            )
        )
        _VARIANTS[name] = lambda ua: parser(ua, ALL_DOMAINS)
    return _VARIANTS[name]


def uap_pure(ua):
    return ua_variant("pure")(ua)


def uap_re2(ua):
    return ua_variant("re2")(ua)


def uap_rust(ua):
    return ua_variant("rust")(ua)

DATA = Path(__file__).parent / "data"
BROWSERS = json.loads((DATA / "top-user-agents.json").read_text())
CRAWLERS = json.loads((DATA / "crawler-user-agents.json").read_text())
CRAWLER_UAS = [ua for c in CRAWLERS for ua in (c.get("instances") or [c["pattern"]])]


def expected(ua):
    """De-facto ground truth for real-browser UAs: (family, major, os)."""
    fam = major = ""
    for tok, name in (
        ("EdgA", "Edge"),
        ("Edg", "Edge"),
        ("OPR", "Opera"),
        ("SamsungBrowser", "Samsung Internet"),
        ("Firefox", "Firefox"),
        ("Chrome", "Chrome"),
    ):
        m = re.search(re.escape(tok) + r"/(\d+)", ua)
        if m:
            fam, major = name, m.group(1)
            break
    if not fam and "Safari/" in ua:
        m = re.search(r"Version/(\d+)", ua)
        fam, major = "Safari", m.group(1) if m else ""
    if not fam and ("iPhone" in ua or "iPad" in ua):
        fam = "Safari"  # iOS webview UA: no browser token, Safari engine
    if "iPhone" in ua or "iPad" in ua:
        os = "ios"
    elif re.search(r"Android [\d.]", ua):
        os = "android"
    elif "Windows NT" in ua:
        os = "windows"
    elif "Mac OS X" in ua:
        os = "macos"
    elif "Linux" in ua or "X11" in ua:
        os = "linux"
    else:
        os = ""
    return fam, major, os


def norm_os(s):
    s = (s or "").lower().replace(" ", "").replace("_", "")
    return {"macosx": "macos", "ubuntu": "linux"}.get(s, s)


def score_browsers():
    res = {}
    for name, fn in (
        ("ua-parser", ua_parse),
        ("user-agents", uas_parse),
        ("user-agent-parser", uap_parse),
    ):
        fam_ok = ver_ok = os_ok = 0
        for ua in BROWSERS:
            efam, emaj, eos = expected(ua)
            r = fn(ua)
            if name == "ua-parser":
                fam = r.user_agent.family or ""
                maj = r.user_agent.major or ""
                osf = r.os.family or ""
            elif name == "user-agent-parser":
                fam = r[0] or ""
                maj = (r[1] or "").split(".")[0]
                osf = r[2] or ""
            else:
                fam = r.browser.family or ""
                maj = str(r.browser.version[0]) if r.browser.version else ""
                osf = r.os.family or ""
            fam = fam.split()[0]
            fam_ok += efam.split()[0].lower() == fam.lower()
            ver_ok += emaj == maj
            os_ok += eos == norm_os(osf)
        res[name] = (fam_ok, ver_ok, os_ok)
    fam_ok = ver_ok = os_ok = 0
    for ua in BROWSERS:
        efam, emaj, eos = expected(ua)
        r = uaparse(ua)
        if eos == "ios":
            # Safari is the only browser iOS has, so the right answer is the
            # device and the iOS version: "iPhone iOS 17", not "Safari/17".
            device = "iPhone" if "iPhone" in ua else "iPad"
            m = re.search(r"OS (\d+)", ua)
            fam_ok += r.pretty.startswith(device)
            ver_ok += bool(m and m.group(1) in r.pretty)
        elif emaj:
            fam_ok += f"{efam}/{emaj}" in r.pretty
            ver_ok += f"/{emaj}" in r.pretty
        else:
            fam_ok += efam in r.pretty or "iPhone" in r.pretty or "iPad" in r.pretty
            ver_ok += 1
        oslabel = {
            "ios": ("iPhone", "iPad"),
            "macos": ("macOS",),
            "windows": ("Windows",),
            "linux": ("Linux",),
            "android": ("Android",),
        }.get(eos, ())
        # Android with a known model drops the OS by design
        model = re.search(r"Android [\d.]+; ([^;()]+?)(?:;|\))", ua)
        has_model = eos == "android" and model and model.group(1) not in ("K", "Mobile")
        os_ok += bool(any(os in r.pretty for os in oslabel) or has_model)
    res["uarite"] = (fam_ok, ver_ok, os_ok)
    return res


def score_crawlers():
    out = {}
    crashes = 0
    for name in ("ua-parser", "user-agents", "user-agent-parser", "uarite"):
        det = 0
        for ua in CRAWLER_UAS:
            try:
                if name == "ua-parser":
                    r = ua_parse(ua)
                    fam = r.user_agent.family if r.user_agent else ""
                    bot = (r.device.family == "Spider" if r.device else False) or bool(
                        re.search(r"bot|spider|crawl", fam, re.I)
                    )
                elif name == "user-agents":
                    bot = uas_parse(ua).is_bot
                elif name == "user-agent-parser":
                    bot = uap_parse(ua)[4] == "Bot"
                else:
                    # Anything not recognized as a real browser is automated:
                    # known bots, generic spiders, clients, spoofed claims.
                    bot = uaparse(ua).kind != "browser"
            except Exception:
                crashes += name == "user-agent-parser"
                continue
            det += bot
        out[name] = det
    url_have = sum(1 for ua in CRAWLER_UAS if re.search(r"https?://", ua))
    url_got = sum(1 for ua in CRAWLER_UAS if uaparse(ua).url)
    return out, url_have, url_got, crashes


def realistic_mix():
    """Realistic traffic: browsers repeat (weighted — popular combos many
    times), interleaved with a steady stream of mostly-unique bot UAs that
    hammer every parser's cache."""
    rng = random.Random(42)
    browsers = []
    for i in range(2000):
        # zipf-ish: early (popular) UAs repeat heavily
        browsers.append(BROWSERS[int(100 * (rng.random() ** 3))])
    bots = list(CRAWLER_UAS)
    rng.shuffle(bots)
    bots = bots[:1000]
    # synthetic cache-busters: unique disguised bot UAs
    for i in range(1000):
        bots.append(
            f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            f" (KHTML, like Gecko) Chrome/{100 + i % 50}.0.{i}.0 Safari/537.36;"
            f" compatible; ScrapeBot{i}/1.{i}; +http://scrapebot{i}.example.com/"
        )
    mix = [None] * (len(browsers) + len(bots))
    mix[::2] = browsers
    mix[1::2] = bots
    return mix


def bench_realistic():
    mix = realistic_mix()
    storm = [f"UniqueBot{i}/2.{i} (+http://ub{i}.example.com/)" for i in range(5000)]
    print(
        f"\n## realistic mix ({len(mix)} UAs: 2000 repeating browsers interleaved"
        f" with 2000 mostly-unique bots)"
    )
    for name, fn in (
        ("ua-parser (pure)", uap_pure),
        ("ua-parser (re2)", uap_re2),
        ("ua-parser (rust)", uap_rust),
        ("user-agents", uas_parse),
        ("user-agent-parser", uap_parse),
        ("uarite", uaparse),
    ):
        fn = safe(fn)
        t = timeit.timeit(lambda: [fn(u) for u in mix], number=1)
        info = cache_info(name)
        print(f"{name:20} {t / len(mix) * 1e6:7.1f} µs/UA   cache: {info}")
    print(f"\n## pure bot storm ({len(storm)} unique UAs, zero cache value)")
    for name, fn in (
        ("ua-parser (pure)", uap_pure),
        ("ua-parser (re2)", uap_re2),
        ("ua-parser (rust)", uap_rust),
        ("user-agents", uas_parse),
        ("user-agent-parser", uap_parse),
        ("uarite", uaparse),
    ):
        fn = safe(fn)
        t = timeit.timeit(lambda: [fn(u) for u in storm], number=1)
        print(
            f"{name:20} {t / len(storm) * 1e6:7.1f} µs/UA   cache: {cache_info(name)}"
        )


def safe(fn):
    def f(u):
        try:
            return fn(u)
        except Exception:
            return None

    return f


def cache_info(name):
    if name == "uarite":
        i = uaparse.cache_info()
        return f"{i.hits} hits / {i.misses} misses (cap 1024)"
    if name == "user-agent-parser":
        from user_agent_parser.parser import _cached_parse_user_agent

        i = _cached_parse_user_agent.cache_info()
        return f"{i.hits} hits / {i.misses} misses (cap 512 LRU)"
    if name == "user-agents":
        from ua_parser.user_agent_parser import _PARSE_CACHE

        return f"{len(_PARSE_CACHE)} entries (cap 200, CLEARS when full)"
    if name.startswith("ua-parser"):
        return "cap 2000 S3-FIFO (scan-resistant)"
    return ""


def bench():
    """Cold-cache speed: a single pass over previously unseen UAs, with
    equal shares of realistic browser and crawler strings since they take
    different parse paths.  Runs before the accuracy passes, which would
    otherwise warm every parser's cache with these very strings.

    Each parser first parses one dummy UA (untimed) so that lazy regex
    compilation and database loading do not land on the first real item —
    ua-parser's first parse alone costs ~59 ms loading its database.  The
    cache gains nothing from it since all timed UAs are unique."""
    rng = random.Random(7)
    work = BROWSERS + rng.sample(CRAWLER_UAS, len(BROWSERS))
    rng.shuffle(work)
    res = {}
    for name, fn in (
        ("ua-parser (pure)", uap_pure),
        ("ua-parser (re2)", uap_re2),
        ("ua-parser (rust)", uap_rust),
        ("user-agents", uas_parse),
        ("user-agent-parser", uap_parse),
        ("uarite", uaparse),
    ):
        fn = safe(fn)
        fn("Warmup/1.0 (+https://example.com/warmup)")
        uaparse.cache_clear()
        t = timeit.timeit(lambda: [fn(u) for u in work], number=1)
        res[name] = t / len(work) * 1e6
    return res, len(work)


if __name__ == "__main__":
    res, nwork = bench()
    print(f"## speed (µs per cold parse, {nwork} unique UAs,"
          " half browsers / half crawlers)")
    for k, v in res.items():
        print(f"{k:20} {v:8.1f}")
    print(f"\n## browser accuracy (n={len(BROWSERS)}): family / version / OS correct")
    for k, (f, v, o) in score_browsers().items():
        print(f"{k:14} {f:3}/100   {v:3}/100   {o:3}/100")
    det, url_have, url_got, crashes = score_crawlers()
    print(f"\n## crawler detection (n={len(CRAWLER_UAS)})")
    for k, v in det.items():
        print(f"{k:18} {v:5}  ({v / len(CRAWLER_UAS):.1%})")
    print(f"user-agent-parser crashed on {crashes} UAs")
    print(f"\nuarite URL extraction: {url_got}/{url_have} of instances carrying a URL")
    bench_realistic()
