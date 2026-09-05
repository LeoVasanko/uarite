# User-Agent parsed Right

User-Agent parsing in Python has a long lineage. ua-parser is the official Python implementation of the ua-parser project, built around uap-core: the regex database extracted from BrowserScope's original parser and shared by implementations in many languages. user-agents wraps ua-parser with higher-level device and capability detection but its last release was in 2020. user-agent-parser is a separate implementation first released in 2022 and substantially updated in 2026, taking its own approach rather than building on uap-core. None of the three has further dependencies, but the regex databases weigh something: ua-parser and user-agents each install about half a megabyte, while user-agent-parser installs at 166 kB. We are merely 29 kB and yet perform better especially with the new crawlers of the AI boom.

This module is another take on the same problem: a small, dependency-free, compact pure-Python parser. It returns structured classifications, but also the thing most applications eventually need: **a short human-readable pretty description**.

Add to your project:

```sh
uv add uarite
```

We correctly detect disguised crawlers and distinguish traffic of AI learning from search engines and social media share previews. We handle HarmonyOS and bots without calling them Android, resolve common device model codes to phone models like Galaxy Z Fold8, and fall back to reasonable output even when all else fails.

## Usage

```python
from uarite import uaparse

r = uaparse("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36")

r.pretty    # "Chrome/152 Windows"
r.engine    # "Chromium"
r.os        # "Windows"
r.kind      # "browser"
r.bot       # ""
r.url       # ""

r = uaparse("Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6885.65 Mobile Safari/537.36; compatible; facebookexternalhit/1.1; +http://www.facebook.com/externalhit_uatext.php")

r.pretty    # "Facebook"
r.kind      # "preview"
r.bot       # "Facebook"
r.url       # "http://www.facebook.com/externalhit_uatext.php"
```

## Output

`uaparse(ua)` returns a `UA` dataclass with string values:

| Field  | Content                                                                                           |
| ------ | ------------------------------------------------------------------------------------------------- |
| pretty | Compact display string (below); empty for empty/missing UAs, the raw UA when unrecognized         |
| engine | Chromium, Gecko, Safari, ArkWeb (HarmonyOS), or empty                                             |
| os     | Windows, macOS, Linux, iOS, Android, HarmonyOS, or empty                                          |
| bot    | Crawler/previewer display name, or empty                                                          |
| kind   | browser, ai, search, preview, spider, or empty (scripts/HTTP libraries)                           |
| url    | The crawler's info URL (the +https://… pointer), or empty; not part of pretty — link it in the UI |

The pretty field is intended to be shown in UI and logging as a conscise description. The url may be included as a link on that text when found, mainly to allow finding out what the bot is used for.

The engine and os fields are meant for broad selection of operation, like which OS installer to offer, or which compatibility hacks are needed. Operating System is the major OS only, no version. Every recognized browser is Chromium except Firefox derivatives (Gecko), Safari (macOS, anything on iOS) and Harmony Browser (ArkWeb).

The kind field describes our detection of visitor type: browser for actual browsers, ai for training data collectors (GPTBot, ClaudeBot, Google-Extended, ...), search for search-engine indexing (Googlebot, Bingbot, ...), preview for social link previews (Facebook, WhatsApp, Slack, ...), spider for generic or unknown crawlers, and empty for scripts and HTTP libraries. Any value other than browser means the visitor is automated.

We deliberately ignore masquerading as browser-compatible (common with crawlers) and fake information like the frozen Android 10; K values that appear on all new mobiles, when the UA provides extra hints of it being something else. These are not reported as engine, os etc., and the pretty field aims to accurately explain only what it actually is.

Obviously all information is limited to that of the User-Agent string given. There are crawlers that masquerade using exact browser strings, or even strings indicating other crawlers than what they actually are, to bypass website protections (e.g. Google bots can often avoid paywalls given to ordinary browsers). You will require other methods to detect them because UA based detection is impossible.

## Accuracy

The table below compares various representative User-Agent formats with the two main contenders. We note that user-agents produces virtually identical results to ua-parser and is thus left out from the comparison, like other worse performing parsers.

| Case                         | uarite¹                   | ua-parser²                                    |
| ---------------------------- | ------------------------- | --------------------------------------------- |
| Chrome, Windows              | Chrome/152 Windows        | Chrome/152 Windows                            |
| Safari, macOS                | Safari/18 macOS           | Safari/18 Mac OS X Mac                        |
| Opera, Linux                 | Opera/106 Linux           | Opera/106 Linux                               |
| Chrome, Android (no model)   | Chrome/152 Android        | Chrome Mobile/152 Android K❌                 |
| Chrome, Android (Pixel)      | Chrome/118 Pixel 6        | Chrome Mobile/118 Android Pixel 6             |
| Edge, Android (model code)   | Edge/110 Galaxy S7        | Edge Mobile/110 Android Samsung SM-G930P      |
| Firefox, Android             | Firefox/154 Android 15    | Firefox Mobile/154 Android Generic Smartphone |
| Safari, iPhone               | iPhone iOS 17             | Mobile Safari/17 iOS iPhone                   |
| Huawei HarmonyOS phone       | HuaweiBrowser/6 HarmonyOS | Huawei Browser/6 Android❌ Huawei Browser     |
| GPTBot                       | GPTBot (AI)               | GPTBot/1 Spider                               |
| Googlebot (disguised)        | Googlebot (search)        | Googlebot/2 Android❌ Spider                  |
| Facebook preview (disguised) | Facebook                  | FacebookBot/1 Android Pixel 7 ❌              |
| Meta crawler (disguised)     | Meta                      | Chrome/145 Windows ❌                         |
| WhatsApp preview             | WhatsApp                  | WhatsApp/10 Spider                            |
| Bytespider                   | Bytespider                | Bytespider/ Android❌ Generic Smartphone      |
| BingPreview                  | BingPreview (preview)     | BingPreview/1 Windows❌ Spider                |
| AhrefsBot                    | AhrefsBot                 | AhrefsBot/7 Spider                            |
| python-requests              | python-requests/2.32.5    | Python Requests/2                             |

- ❌ marks an incorrect browser, OS, or device interpretation.
- ¹ r.pretty shown as is
- ² {user_agent.family}/{user_agent.major} {os.family} {device.family}

Measured on modern browser UAs, **uarite resolves family, version and OS at 100%**. ua-parser and user-agents land at 80%, while user-agent-parser does slightly better at 92%.

Crawler detection was also tested against real-world crawler UAs from [monperrus/crawler-user-agents](https://github.com/monperrus/crawler-user-agents). Here user-agent-parser got only 32% right and worse, crashed on 5 UAs. A slight difference was found with the other contenders, user-agents coming at 60% and ua-parser at 64% correct. Our module **uarite scores 95%**, and could detect _which_ crawler it is for 80% (bot field set).

## Performance

All compared parsers cache repeated User-Agents, making cache hits effectively free. The useful difference is therefore the first parse of a new string.

In our benchmarks, uncached uarite parses take roughly **3–7 µs**. user-agent-parser is in the same general range at **~7 µs**, while the pure-Python ua-parser/user-agents path takes roughly **130–250 µs**, which can be a considerable slowdown.

## Design

Rather than a large regex database trying to match any possible UA to given fields, we actually parse the modern forms of UA strings, and take the most specific interpretation of them to avoid the mess of compatibility tags they usually contain. This is built against modern traffic, including the AI crawlers that make up a large part of today's traffic, and for modern browsers — purposefully ignoring the decades of history other UA parser frameworks carry.

The most important feature, absent from others, are the built-in pretty UA strings suitable for user interfaces and logging. Hopefully you will find use for that. And in case something could be better, please report an issue.

Until now I had been using those other modules, building my own pretty UA formatting on top of them. Where the modules had misdetections, I have tried reporting bugs but the upstream didn't have any interest in fixing their database. Therefore, I found it easier to write my own completely from a modern starting point, and uarite is that thing, done right, as I think. Hopefully this helps you too.
