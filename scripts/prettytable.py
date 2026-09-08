"""Print the README's accuracy-comparison table as markdown.

uarite's column is simply `r.pretty`.  The reference modules have no
display format; their columns use one plain format string each on their
structured output (footnotes ²³ in the README).  Requires uarite (installed)
plus the benchmark-only reference parsers:

    uv run --with ua-parser --with user-agents python scripts/prettytable.py
"""

from ua_parser import parse as ua_parse
from user_agents import parse as uas_parse

from uarite import uaparse

CASES = [
    (
        "Chrome, Windows",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
    ),
    (
        "Safari, macOS",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Safari/605.1.15",
    ),
    (
        "Opera, Linux",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
    ),
    (
        "Chrome, Android (no model)",
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Mobile Safari/537.36",
    ),
    (
        "Chrome, Android (Pixel)",
        "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
    ),
    (
        "Edge, Android (model code)",
        "Mozilla/5.0 (Linux; Android 15; SM-G930P; Build/AP4A.190211.226) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.1587.89 Mobile Safari/537.36 EdgA/110.0.1587.89",
    ),
    (
        "Firefox, Android",
        "Mozilla/5.0 (Android 15; Mobile; rv:154.0) Gecko/154.0 Firefox/154.0",
    ),
    (
        "Safari, iPhone",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    ),
    (
        "Huawei HarmonyOS phone",
        "Mozilla/5.0 (Phone; OpenHarmony 6.1; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36  ArkWeb/6.1.0.120 Mobile HuaweiBrowser/6.1.6.310",
    ),
    ("GPTBot", "Mozilla/5.0 (compatible; GPTBot/1.2; +https://openai.com/gptbot)"),
    (
        "Googlebot (disguised)",
        "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    ),
    (
        "Facebook preview (disguised)",
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6885.65 Mobile Safari/537.36; compatible; facebookexternalhit/1.1; +http://www.facebook.com/externalhit_uatext.php",
    ),
    (
        "Meta crawler (disguised)",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 (compatible; meta-externalagent/1.1 (+https://developers.facebook.com/docs/sharing/webmasters/crawler))",
    ),
    ("WhatsApp preview", "Mozilla/5.0 (compatible; WhatsApp/10.0.2.1)"),
    (
        "Bytespider",
        "Mozilla/5.0 (Linux; Android 5.0) AppleWebKit/537.36 (KHTML, like Gecko) Mobile Safari/537.36 (compatible; Bytespider; https://zhanzhang.toutiao.com/)",
    ),
    (
        "BingPreview",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534+ (KHTML, like Gecko) BingPreview/1.0b",
    ),
    ("AhrefsBot", "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)"),
    ("python-requests", "python-requests/2.32.5"),
]


def imitate_uaparser(ua):
    r = ua_parse(ua)
    fam = (r.user_agent.family if r.user_agent else "") or ""
    maj = (r.user_agent.major if r.user_agent else "") or ""
    osf = (r.os.family if r.os else "") or ""
    dev = (r.device.family if r.device else "") or ""
    return f"{fam}/{maj} {osf} {dev}"


def imitate_useragents(ua):
    r = uas_parse(ua)
    fam = r.browser.family or ""
    maj = str(r.browser.version[0]) if r.browser.version else ""
    return f"{fam}/{maj} {r.os.family or ''} {r.device.family or ''}"


print("| Case | uarite¹ | ua-parser² | user-agents³ |")
print("|---|---|---|---|")
for name, ua in CASES:
    ours = uaparse(ua).pretty or "—"
    print(f"| {name} | {ours} | {imitate_uaparser(ua)} | {imitate_useragents(ua)} |")
