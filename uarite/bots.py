"""Crawler and link-preview tables."""

#: Lowercase UA substring to (display name, kind).  Ordered: first match
#: wins, so overlapping names go from most to least specific.
BOTS = {
    "feedfetcher-google": ("Feedfetcher-Google", "search"),
    "google-inspectiontool": ("Google-InspectionTool", "search"),
    "google-read-aloud": ("Google-Read-Aloud", "search"),
    "mediapartners-google": ("Mediapartners-Google", "spider"),
    "adsbot-google": ("AdsBot-Google", "spider"),
    "apis-google": ("APIs-Google", "spider"),
    "storebot-google": ("Storebot-Google", "spider"),
    "duplexweb-google": ("DuplexWeb-Google", "spider"),
    "google-extended": ("Google-Extended", "ai"),
    "googlebot": ("Googlebot", "search"),
    "googleother": ("GoogleOther", "spider"),
    "bingbot": ("Bingbot", "search"),
    "applebot": ("Applebot", "search"),
    "gptbot": ("GPTBot", "ai"),
    "oai-searchbot": ("OAI-SearchBot", "search"),
    "chatgpt-user": ("ChatGPT-User", "ai"),
    "claude-searchbot": ("Claude-SearchBot", "search"),
    "claudebot": ("ClaudeBot", "ai"),
    "claude-user": ("Claude-User", "ai"),
    "perplexity-user": ("Perplexity-User", "ai"),
    "perplexitybot": ("PerplexityBot", "search"),
    "grokbot": ("GrokBot", "ai"),
    "bytespider": ("Bytespider", "ai"),
    "reflectionbot": ("Reflectionbot", "ai"),
    "amzn-searchbot": ("Amzn-SearchBot", "search"),
    "amazonbot": ("Amazonbot", "search"),
    "ahrefsbot": ("AhrefsBot", "spider"),
    "mj12bot": ("MJ12bot", "spider"),
    "facebookexternalhit": ("Facebook", "preview"),
    "meta-externalagent": ("Meta", "preview"),
    "skypeuripreview": ("Skype", "preview"),
    "bingpreview": ("BingPreview", "preview"),
    "pinterest": ("Pinterest", "preview"),
    "embedly": ("Embedly", "preview"),
    "iframely": ("Iframely", "preview"),
    "discordbot": ("Discord", "preview"),
    "slackbot": ("Slack", "preview"),
    "telegrambot": ("Telegram", "preview"),
    "twitterbot": ("Twitter", "preview"),
    "linkedinbot": ("LinkedIn", "preview"),
    "whatsapp": ("WhatsApp", "preview"),
    "headlesschrome": ("HeadlessChrome", "spider"),
    "phantomjs": ("PhantomJS", "spider"),
    "uptimerobot": ("UptimeRobot", "spider"),
    "pingdom": ("Pingdom", "spider"),
}

#: Pretty suffixes for the kinds more precise than a generic spider.
KIND_LABEL = {"ai": "AI", "search": "search", "preview": "preview"}

#: Providers with more than one crawler product; the kind label is kept
#: only where it distinguishes siblings within the group.
PROVIDERS = [
    (
        "Googlebot",
        "Google-Extended",
        "GoogleOther",
        "Feedfetcher-Google",
        "Google-InspectionTool",
        "Google-Read-Aloud",
        "Mediapartners-Google",
        "AdsBot-Google",
        "APIs-Google",
        "Storebot-Google",
        "DuplexWeb-Google",
    ),
    ("ClaudeBot", "Claude-User", "Claude-SearchBot"),
    ("GPTBot", "OAI-SearchBot", "ChatGPT-User"),
    ("PerplexityBot", "Perplexity-User"),
    ("Amazonbot", "Amzn-SearchBot"),
    ("Bingbot", "BingPreview"),
]

#: Bot names whose kind label is displayed, computed from the groups.
LABELED = {
    name
    for group in PROVIDERS
    if len({kind for n, kind in BOTS.values() if n in group}) > 1
    for name in group
}
