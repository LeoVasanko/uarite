import assert from "node:assert/strict"
import { test } from "node:test"
import { uaparse } from "../dist/index.js"

test("empty and missing UAs", () => {
  for (const ua of ["", "   ", "-", "null", null, undefined]) {
    assert.deepEqual(uaparse(ua), {
      pretty: "",
      engine: "",
      os: "",
      kind: "",
      url: "",
      provider: "",
    })
  }
})

test("Chrome on Windows", () => {
  const r = uaparse(
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
  )
  assert.equal(r.pretty, "Chrome/152 Windows")
  assert.equal(r.engine, "Chromium")
  assert.equal(r.os, "Windows")
  assert.equal(r.kind, "browser")
  assert.equal(r.url, "")
})

test("Safari on macOS", () => {
  const r = uaparse(
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
  )
  assert.equal(r.pretty, "Safari/18 macOS")
  assert.equal(r.engine, "Safari")
})

test("Firefox on Android keeps the OS version", () => {
  const r = uaparse(
    "Mozilla/5.0 (Android 15; Mobile; rv:154.0) Gecko/154.0 Firefox/154.0",
  )
  assert.equal(r.pretty, "Firefox/154 Android 15")
  assert.equal(r.engine, "Gecko")
  assert.equal(r.os, "Android")
})

test("Chrome on Android with a Pixel model", () => {
  const r = uaparse(
    "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
  )
  assert.equal(r.pretty, "Chrome/118 Pixel 6")
  assert.equal(r.os, "Android")
})

test("Samsung model codes resolve to marketing names", () => {
  const r = uaparse(
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
  )
  assert.equal(r.pretty, "Chrome/118 Galaxy S23 Ultra")
})

test("Chrome reduced UA (Android 10; K)", () => {
  const r = uaparse(
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Mobile Safari/537.36",
  )
  assert.equal(r.pretty, "Chrome/152 Android")
})

test("iPhone", () => {
  const r = uaparse(
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
  )
  assert.equal(r.pretty, "iPhone iOS 17")
  assert.equal(r.engine, "Safari")
  assert.equal(r.os, "iOS")
})

test("HarmonyOS before Android", () => {
  const r = uaparse(
    "Mozilla/5.0 (Linux; Android 12; HarmonyOS; ALN-AL00; HMSCore 6.13.0.312) AppleWebKit/537.36 (KHTML, like Gecko) HuaweiBrowser/6.0.1.311 Mobile Safari/537.36",
  )
  assert.equal(r.pretty, "HuaweiBrowser/6 HarmonyOS")
  assert.equal(r.engine, "ArkWeb")
  assert.equal(r.os, "HarmonyOS")
})

test("ancient browser versions are marked spoofed", () => {
  const r = uaparse(
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.0.0 Safari/537.36",
  )
  assert.equal(r.pretty, "Chrome/60 Windows (spoofed)")
  assert.equal(r.kind, "")
})

test("HTTP clients", () => {
  assert.equal(
    uaparse("python-requests/2.32.5").pretty,
    "python-requests/2.32.5",
  )
  assert.equal(uaparse("curl/8.0").pretty, "curl/8.0")
})

test("GPTBot", () => {
  const r = uaparse(
    "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.2; +https://openai.com/gptbot",
  )
  assert.equal(r.pretty, "GPTBot (AI)")
  assert.equal(r.kind, "ai")
  assert.equal(r.provider, "OpenAI")
  assert.equal(r.url, "https://openai.com/gptbot")
})

test("Facebook external hit, disguised as Chrome on Android", () => {
  const r = uaparse(
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6885.65 Mobile Safari/537.36; compatible; facebookexternalhit/1.1; +http://www.facebook.com/externalhit_uatext.php",
  )
  assert.equal(r.pretty, "Facebook")
  assert.equal(r.kind, "social")
  assert.equal(r.provider, "Meta")
  assert.equal(r.url, "http://www.facebook.com/externalhit_uatext.php")
})

test("unknown bot from product token", () => {
  const r = uaparse("NewBot/1.0 (+https://example.com/bot)")
  assert.equal(r.pretty, "NewBot")
  assert.equal(r.kind, "spider")
})

test("named from compatible token", () => {
  const r = uaparse(
    "Mozilla/5.0 (compatible; Page2RSS/0.7; +http://page2rss.com/)",
  )
  assert.equal(r.pretty, "Page2RSS")
  assert.equal(r.kind, "spider")
})

test("unrecognized Mozilla UA falls back to the raw string", () => {
  const ua = "Mozilla/5.0 (something entirely unknown)"
  assert.equal(uaparse(ua).pretty, ua)
})

test("results are cached", () => {
  const ua =
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"
  assert.equal(uaparse(ua), uaparse(ua))
})
