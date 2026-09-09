# User-Agent Parsing Done Right

Fast and accurate handling of modern browsers and crawlers. Despite its light weight and no dependencies, uarite identifies both browsers and crawlers more accurately than any competing implementation tested here. We also provide a [Python uarite](https://pypi.org/project/uarite/) with exact same output.

It returns structured classification, but also the thing most applications eventually need: **a short pretty description**.

## Usage

Add it to your project:

```sh
npm install @vasanko/uarite
```

```js
import { uaparse } from "@vasanko/uarite"

const { pretty, engine, os, kind } = uaparse(
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
)
// Chrome/152 Windows, Chromium, Windows, browser

const { pretty, kind, url, provider } = uaparse(
  "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.2; +https://openai.com/gptbot",
)
// GPTBot (AI), ai, https://openai.com/gptbot, OpenAI
```

Plain HTML? A prebuilt minified ESM bundle you can host yourself or link from CDN:

```html
<script type="module">
  import { uaparse } from "https://cdn.jsdelivr.net/npm/@vasanko/uarite/dist/uarite.min.js"
  console.log(uaparse(navigator.userAgent))
</script>
```

## Output

`uaparse(ua)` returns a `UA` object with string fields. Any field may be empty string when the information is unavailable.

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

The popular npm options for this task are bowser and ua-parser-js. The table below compares representative User-Agent formats.

| Case                         | uarite¹                   | ua-parser-js²                        | bowser³                              |
| ---------------------------- | ------------------------- | ------------------------------------ | ------------------------------------ |
| Chrome, Windows              | Chrome/152 Windows        | Chrome/152 Windows                   | Chrome/152.0.0.0 Windows             |
| Chrome, Android (no model)   | Chrome/152 Android        | Mobile Chrome/152 Android K❌        | Chrome/152.0.0.0 Android             |
| Edge, Android (model code)   | Edge/110 Galaxy S7        | Edge/110 Android SM-G930P            | Microsoft Edge/110.0.1587.66 Android |
| Safari, iPhone               | iPhone iOS 17             | Mobile Safari/17 iOS iPhone          | Safari/17.0 iOS iPhone               |
| Huawei HarmonyOS phone       | HuaweiBrowser/6 HarmonyOS | Huawei Browser/6 HarmonyOS ALN-AL00  | Android Browser/ Android ❌          |
| GPTBot                       | GPTBot (AI)               | WebKit/537 ❌                        | GPTBot/1.2                           |
| Googlebot (disguised)        | Googlebot (search)        | Mobile Chrome/122 Android Nexus 5 ❌ | Googlebot/2.1 Android❌              |
| Facebook preview (disguised) | Facebook                  | Mobile Chrome/134 Android Pixel 7 ❌ | FacebookExternalHit/ Android❌       |
| WhatsApp preview             | WhatsApp                  | (nothing) ❌                         | WhatsApp/2.23.20.0                   |
| python-requests              | python-requests/2.32.5    | (nothing) ❌                         | (nothing) ❌                         |

- ❌ marks incorrect data such as an OS from a crawler's disguise, a frozen compat placeholder reported as a device, or a missed identity
- ¹ `uaparse(ua).pretty` shown as is
- ² `{browser.name??''}/{browser.major??''} {os.name??''} {device.model??''}`; free MIT tier of v2
- ³ `{browser.name??''}/{browser.version??''} {os.name??''} {platform.model??''}`

Parsing a mixed set of 316 real-world browser and crawler UAs, parses per second: **uarite 580 000**, bowser 130 000 and ua-parser-js 18 000. The other parsers don't appear to implement caching. For previously seen UA strings, however, uarite reaches **5.6 million**, while all others remain at the rates quoted above.

All are relatively small: **uarite minifies to 9 kB**, bowser to 37 kB and ua-parser-js to 28 kB.

## Why yet another UA parser

Rather than relying on a large historical regex database, the parser focuses on modern UA formats and parses them directly, choosing the most specific interpretation available. This keeps the implementation small while handling today's browsers and crawler traffic well. Until now, I had been using those other modules and building my own pretty-UA formatting on top of them, fixing by post processing issues the upstream didn't care of.

Eventually it became easier to start over with a parser designed around modern traffic. The result is uarite.

Hopefully it helps you too. Star my [GitHub](https://github.com/leovasanko/uarite) if it did.
