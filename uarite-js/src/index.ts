import {
  BOTS,
  BROWSERS,
  KIND_LABEL,
  LABELED,
  PRETTY_OVERRIDE,
  PROVIDER_OF,
  SAMSUNG,
  SAMSUNG_SERIES,
} from "./tables.js"

/** Result of parsing a User-Agent string. Any field may be empty. */
export interface UA {
  /** Compact display string; raw UA when unrecognized. */
  pretty: string
  /** Chromium, Gecko, Safari, ArkWeb. */
  engine: string
  /** Windows, macOS, Linux, iOS, Android, HarmonyOS. */
  os: string
  /** browser, ai, search, social, analytics, spider. */
  kind: string
  /** Crawler information URL. */
  url: string
  /** Provider of a known crawler family. */
  provider: string
}

const EMPTY: UA = {
  pretty: "",
  engine: "",
  os: "",
  kind: "",
  url: "",
  provider: "",
}

/** Fallback for unknown crawlers: a product token whose name says so. */
const BOT_TOKEN = /[^\s();/]*(?:bot|spider|crawl|scan|verif|check)[^\s();/]*/i

/** A "+https://…" pointer is a crawler tell; real browsers carry no URL. */
const URL = /\+\s*(https?:\/\/[^\s;)]+)/
const ANY_URL = /(https?:\/\/[^\s;)]+)/

/** Crawler name next to the info URL: "compatible; Page2RSS/0.7; +http://…". */
const COMPATIBLE_NAME = /compatible;\s*([^;/()]+?)(?:\/[\d.vx]+)?\s*;/

/** Name from an info URL's host when no product token is available. */
const HOST = /https?:\/\/(?:www\.)?([^/\s;)]+)/

/** Android model token: "Android 15; SM-S918B)", "Android 12; Pixel 6; Build/…". */
const ANDROID_MODEL = /Android [\d.]+; ([^;()]+?)(?:;|\)| Build\/)/

/** All known-bot substrings in one compiled pass. */
const BOTS_RE = new RegExp(
  Object.keys(BOTS)
    .map((s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
    .join("|"),
)

/** The crawler's info URL from the UA, or "" (mailto: is not a URL). */
export function url(ua: string): string {
  const m = URL.exec(ua) ?? ANY_URL.exec(ua)
  return m ? m[1] : ""
}

/** (display name, kind) of the crawler/unfurler the UA claims. */
export function bot(ua: string): readonly [string, string] {
  const low = ua.toLowerCase()
  const m = BOTS_RE.exec(low)
  if (m) return BOTS[m[0]]
  // Cheap keyword gates keep the regexes off the hot path.
  if (/(?:bot|spider|crawl|scan|verif|check)/.test(low)) {
    const t = BOT_TOKEN.exec(ua)
    if (t) {
      const name = t[0].replace(/^;+|;+$/g, "")
      return [name[0].toUpperCase() + name.slice(1), "spider"]
    }
  }
  // An info URL in the UA is a crawler convention.  Name it from the
  // "compatible; Name/x" token, else the first product token, else the
  // URL's host.
  if (ua.includes("://")) {
    let name = ""
    const cm = COMPATIBLE_NAME.exec(ua)
    if (cm) {
      name = cm[1].trim()
    } else if (!ua.startsWith("Mozilla")) {
      name = ua.split(" ")[0].split("/")[0]
    }
    const nl = name.toLowerCase()
    if (!name || nl.startsWith("mozilla") || nl.startsWith("msie")) {
      const hm = HOST.exec(ua)
      name = hm ? hm[1] : ""
    }
    if (name) return [name[0].toUpperCase() + name.slice(1), "spider"]
  }
  return ["", ""]
}

/** Major version of a `token/x.y` product in the UA, or "". */
export function version(ua: string, token: string): string {
  const m = new RegExp(
    `${token.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}/(\\d+)`,
  ).exec(ua)
  return m ? m[1] : ""
}

/** `Browser/major` for the browsers we care to distinguish. */
export function browser(ua: string): string {
  for (const [token, name] of BROWSERS) {
    const ver = version(ua, token)
    if (ver) return `${name}/${ver}`
  }
  if (ua.includes("Safari/")) {
    const ver = version(ua, "Version")
    return ver ? `Safari/${ver}` : "Safari"
  }
  return ""
}

/** Engines that differ from the Chromium default for recognized browsers. */
const ENGINES: Readonly<Record<string, string>> = {
  Firefox: "Gecko",
  LibreWolf: "Gecko",
  Safari: "Safari",
}

/** Oldest plausible major versions (≈2023 releases); see the Python source. */
const ANCIENT: Readonly<Record<string, number>> = {
  Firefox: 108,
  Chrome: 108,
  Edge: 108,
  Opera: 95,
}

/** True when a `Browser/major` claims an impossibly old version. */
export function spoofed(b: string): boolean {
  const i = b.indexOf("/")
  const name = i < 0 ? b : b.slice(0, i)
  const ver = i < 0 ? "" : b.slice(i + 1)
  const floor = ANCIENT[name]
  return floor !== undefined && /^\d+$/.test(ver) && Number(ver) < floor
}

/** Engine for a `Browser/major` result; Chromium is the modern default. */
export function engine(b: string): string {
  const name = b.split("/")[0]
  return ENGINES[name] ?? (name ? "Chromium" : "")
}

/** Desktop OS name, or "" when not recognizable. */
export function os(ua: string): string {
  if (ua.includes("Windows NT")) return "Windows"
  if (ua.includes("Mac OS X")) return "macOS"
  if (ua.includes("Linux") || ua.includes("X11")) return "Linux"
  if (ua.includes("Windows")) return "Windows"
  if (ua.includes("Darwin")) return "macOS"
  return ""
}

/**
 * Human-readable phone name for an Android model code.
 *
 * Returns the input unchanged when nothing is known about it (Pixel and
 * most other brands already send readable names).
 */
export function modelName(model: string): string {
  if (model.startsWith("SM-")) {
    // Strip the region/carrier suffix: SM-S918B -> SM-S918, and the
    // Chinese/HK variant's trailing zero: SM-S9370 -> SM-S937.
    let code = model.replace(/[A-Z]{1,2}$/, "")
    if (!(code in SAMSUNG) && code.endsWith("0")) code = code.slice(0, -1)
    if (code in SAMSUNG) return SAMSUNG[code]
    const series = SAMSUNG_SERIES[code.slice(0, 4)]
    if (series) return series
  }
  return model
}

const CACHE_MAX = 1024
const cache = new Map<string, UA>()

/** Parse a User-Agent string into a compact {@link UA} record. */
export function uaparse(ua: string | null | undefined): UA {
  if (!ua || !ua.trim() || ua === "-" || ua === "null") return EMPTY
  const hit = cache.get(ua)
  if (hit) {
    // Refresh recency, mirroring Python's lru_cache.
    cache.delete(ua)
    cache.set(ua, hit)
    return hit
  }
  const r = parse(ua)
  if (cache.size >= CACHE_MAX) {
    cache.delete(cache.keys().next().value as string)
  }
  cache.set(ua, r)
  return r
}

function parse(ua: string): UA {
  const [name, kind] = bot(ua)
  if (name) {
    // The browser/OS in crawler UAs is a disguise; the bot identity is
    // the relevant information, so `engine` and `os` are left empty.
    let pretty = PRETTY_OVERRIDE[name]
    if (pretty === undefined) {
      const label = LABELED.has(name) ? (KIND_LABEL[kind] ?? "") : ""
      pretty = label ? `${name} (${label})` : name
    }
    return {
      ...EMPTY,
      pretty,
      kind,
      url: url(ua),
      provider: PROVIDER_OF[name] ?? "",
    }
  }
  return parseClient(ua)
}

function parseClient(ua: string): UA {
  const r = client(ua)
  // Frozen ancient browser strings are scanners/scripts, not users: show
  // the claimed browser, but mark it and drop the fake engine/os/kind.
  if (r.kind === "browser" && spoofed(browser(ua))) {
    return { ...EMPTY, pretty: `${r.pretty} (spoofed)` }
  }
  return r
}

function client(ua: string): UA {
  // Non-browser HTTP clients ("python-requests/2.32.5", "curl/8.0",
  // "pip/24.3.1 {json…}"): the first product token, plus the OS when
  // their payload mentions one in free text.
  if (!ua.startsWith("Mozilla")) {
    const token = ua.split(" ")[0]
    let pretty = token.includes("/") ? token : ua
    const osName = os(ua)
    if (osName && !pretty.includes(osName)) pretty = `${pretty} ${osName}`
    return { ...EMPTY, pretty, os: osName }
  }

  // HarmonyOS carries an "Android" compatibility token, so it must be
  // detected before Android.
  if (
    ua.includes("OpenHarmony") ||
    ua.includes("HarmonyOS") ||
    ua.includes("ArkWeb")
  ) {
    const b = browser(ua)
    return {
      ...EMPTY,
      pretty: b ? `${b} HarmonyOS` : "HarmonyOS",
      engine: "ArkWeb",
      os: "HarmonyOS",
      kind: "browser",
    }
  }

  if (ua.includes("iPhone") || ua.includes("iPad")) {
    const device = ua.includes("iPhone") ? "iPhone" : "iPad"
    const m = /OS (\d+)/.exec(ua)
    return {
      ...EMPTY,
      pretty: m ? `${device} iOS ${m[1]}` : device,
      engine: "Safari",
      os: "iOS",
      kind: "browser",
    }
  }

  const am = /Android ([\d.]+)/.exec(ua)
  if (am) {
    const b = browser(ua)
    const mm = ANDROID_MODEL.exec(ua)
    const token = mm ? mm[1].trim() : ""
    let parts: string[]
    if (token === "K") {
      // Chrome's reduced UA freezes both: "Android 10; K".  Neither
      // is real — report just the OS.
      parts = [b, "Android"].filter(Boolean)
    } else {
      // Firefox sends the form factor ("Mobile"/"Tablet") in the model
      // slot.  A known model replaces the OS.
      let model = ""
      if (token && !["wv", "Mobile", "Tablet"].includes(token)) {
        model = modelName(token)
      }
      parts = [b, model || `Android ${am[1]}`].filter(Boolean)
    }
    return {
      ...EMPTY,
      pretty: parts.join(" "),
      engine: engine(b),
      os: "Android",
      kind: "browser",
    }
  }

  const b = browser(ua)
  const osName = os(ua)
  const pretty = `${b} ${osName}`.trim()
  return {
    ...EMPTY,
    pretty: pretty || ua,
    engine: engine(b),
    os: osName,
    kind: "browser",
  }
}
