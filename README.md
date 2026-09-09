# User-Agent Parsing Done Right

Fast and accurate handling of modern browsers and crawlers. Despite its light weight, uarite identifies both browsers and crawlers more accurately than any competing implementation tested here. Despite being pure Python, it outperforms ua-parser's C++/Rust variants.

It returns structured classification, but also the thing most applications eventually need: **a short pretty description**.

Add it to your project:

```sh
uv add uarite
```

## Usage

```python
from uarite import uaparse

r = uaparse("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36")

r.pretty    # "Chrome/152 Windows"
r.engine    # "Chromium"
r.os        # "Windows"
r.kind      # "browser"
r.url       # ""

r = uaparse("Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6885.65 Mobile Safari/537.36; compatible; facebookexternalhit/1.1; +http://www.facebook.com/externalhit_uatext.php")

r.pretty    # "Facebook"
r.kind      # "social"
r.provider  # "Meta"
r.url       # "http://www.facebook.com/externalhit_uatext.php"
```

## Output

`uaparse(ua)` returns a `UA` dataclass with string fields. Any field may be empty when the information is unavailable.

| Field    | Content                                          |
| -------- | ------------------------------------------------ |
| pretty   | Compact display string; raw UA when unrecognized |
| engine   | Chromium, Gecko, Safari, ArkWeb                  |
| os       | Windows, macOS, Linux, iOS, Android, HarmonyOS   |
| kind     | browser, ai, search, social, analytics, spider   |
| url      | Crawler information URL                          |
| provider | Provider of a known crawler family               |

The pretty field is intended for UIs and logs. The url can be attached to it as a link when available.

The engine and os fields are intentionally broad. The kind field distinguishes browsers from AI collectors, search engines, social previews, monitoring tools, generic spiders, and ordinary HTTP clients. Any non-browser kind represents automated traffic.

Detection is necessarily limited by what the User-Agent reveals. Crawlers can masquerade as ordinary browsers or other crawlers, so sites that need stronger identification should use additional methods rather than relying on UA detection alone.

## Comparison

There are plenty of UA parsers for Python. This comparison includes the ua-parser family — the official port of the large upstream project, benchmarked with all three of its regex backends (Python, RE2, Rust) — plus user-agents, which builds on it with higher-level device detection, and fastuaparser, a single-file heuristic parser in the same weight class as uarite. Among those excluded: user-agent-parser crashes on real-world strings; httpagentparser misidentifies most bots and browser OSes; device-detector has a massive 26 MB install and extremely slow parsing; and crawlerdetect only distinguishes bots from non-bots. The user-agents package has been unmaintained since 2020 but is kept as a reference point.

Installed size tracks the design. The minimal heuristic parsers are tiny: fastuaparser installs in 15 kB, uarite in 30 kB. Everything built on ua-parser's regex database starts around half a megabyte, and its accelerated backends add several megabytes of native code.

The benchmark and test scripts are available in the repository's scripts folder.

### Accuracy

The table below compares representative User-Agent formats with fastuaparser and ua-parser. The user-agents wrapper produces nearly identical results to ua-parser and is left out.

| Case                         | uarite¹                   | fastuaparser²             | ua-parser³                                    |
| ---------------------------- | ------------------------- | ------------------------- | --------------------------------------------- |
| Chrome, Windows              | Chrome/152 Windows        | Chrome - Windows          | Chrome/152 Windows                            |
| Safari, macOS                | Safari/18 macOS           | Safari - Mac OS X         | Safari/18 Mac OS X Mac                        |
| Opera, Linux                 | Opera/106 Linux           | Opera - Linux             | Opera/106 Linux                               |
| Chrome, Android (no model)   | Chrome/152 Android        | Chrome - Android Mobile   | Chrome Mobile/152 Android K❌                 |
| Chrome, Android (Pixel)      | Chrome/118 Pixel 6        | Chrome - Android Mobile   | Chrome Mobile/118 Android Pixel 6             |
| Edge, Android (model code)   | Edge/110 Galaxy S7        | Edge - Android Mobile     | Edge Mobile/110 Android Samsung SM-G930P      |
| Firefox, Android             | Firefox/154 Android 15    | Firefox - Android Mobile  | Firefox Mobile/154 Android Generic Smartphone |
| Safari, iPhone               | iPhone iOS 17             | Safari - iOS Mobile       | Mobile Safari/17 iOS iPhone                   |
| Huawei HarmonyOS phone       | HuaweiBrowser/6 HarmonyOS | Chrome - Android Mobile❌ | Huawei Browser/6 Android❌ Huawei Browser     |
| GPTBot                       | GPTBot (AI)               | Bot                       | GPTBot/1 Spider                               |
| Googlebot (disguised)        | Googlebot (search)        | Bot                       | Googlebot/2 Android❌ Spider                  |
| Facebook preview (disguised) | Facebook                  | Chrome - Android Mobile❌ | FacebookBot/1 Android Pixel 7 ❌              |
| Meta crawler (disguised)     | Meta-ExternalAgent (AI)   | Bot                       | Chrome/145 Windows ❌                         |
| WhatsApp preview             | WhatsApp                  | Browser - Other❌         | WhatsApp/10 Spider                            |
| Bytespider                   | Bytespider                | Bot                       | Bytespider/ Android❌ Generic Smartphone      |
| BingPreview                  | BingPreview               | Browser - Windows❌       | BingPreview/1 Windows❌ Spider                |
| AhrefsBot                    | AhrefsBot                 | Bot                       | AhrefsBot/7 Spider                            |
| python-requests              | python-requests/2.32.5    | Other                     | Python Requests/2                             |

- ❌ marks incorrect data such as an OS from disguise, Android 10; K (compat) on modern devices, or a missed identity
- ¹ `r.pretty` shown as is
- ² `parse_ua(ua)` shown as is
- ³ `{r.user_agent.family}/{r.user_agent.major} {r.os.family} {r.device.family}`

On our modern-browser test set, scoring only fully correct results (family, version, and OS all right): **uarite 100%**, ua-parser and user-agents 79%. The fastuaparser heuristic resolves the family and OS in 91% of cases, but reports no version numbers at all, so it cannot be scored on the full criterion.

Crawler detection was tested against [real world UAs](https://github.com/monperrus/crawler-user-agents): **uarite 97%**, fastuaparser 84%, ua-parser 64%, user-agents 60%.

### Performance

Import and first parse takes about **10 ms** for uarite and effectively nothing for fastuaparser, compared with 50–90 ms for ua-parser depending on backend.

![uarite 56 thousand, ua-parser native code variants Rust 26 thousand, RE2 14 thousand, and finally plain Python ua-parser and user-agents 3 thousand](https://git.zi.fi/LeoVasanko/uarite/raw/branch/main/docs/bench-speed.svg)
_User-Agents parsed per second per CPU core, first parse of unseen strings, with equal shares of browser and crawler UAs. One-off setup costs excluded. Cached results and fastuaparser (1 million) are left out of the graph._

On raw speed fastuaparser wins: a few string searches per UA, no cache needed. The trade-off shows in the accuracy table above. All other parsers cache results. With cache hits, **uarite reaches about 36 million lookups per second**, compared with about 5 million for ua-parser and 600 000 for user-agents.

## Why yet another UA parser

Rather than relying on a large historical regex database, the parser focuses on modern UA formats and parses them directly, choosing the most specific interpretation available. This keeps the implementation small while handling today's browsers and crawler traffic well. Until now, I had been using those other modules and building my own pretty-UA formatting on top of them, fixing by post processing issues the upstream didn't care of.

Eventually it became easier to start over with a parser designed around modern traffic. The result is uarite.

Hopefully it helps you too. Star my [GitHub](https://github.com/leovasanko/uarite) if it did.
