"""Crawler and link-unfurler tables."""

#: Lowercase UA substring to (display name, kind).  Ordered: first match
#: wins, so overlapping names go from most to least specific.
BOTS = {
    # Qualys SSL Labs scanner: frozen on this exact Firefox/45 string since
    # ~2016; the pinned Gecko date makes the substring distinctive.
    "mozilla/5.0 (x11; linux x86_64; rv:45.0) gecko/20100101 firefox/45.0": (
        "Qualys SSL Labs",
        "spider",
    ),
    "feedfetcher-google": ("Feedfetcher-Google", "search"),
    "google-inspectiontool": ("Google-InspectionTool", "search"),
    "google-read-aloud": ("Google-Read-Aloud", "ai"),
    "mediapartners-google": ("Mediapartners-Google", "analytics"),
    "adsbot-google": ("AdsBot-Google", "analytics"),
    "apis-google": ("APIs-Google", "spider"),
    "storebot-google": ("Storebot-Google", "search"),
    "google-extended": ("Google-Extended", "ai"),
    "googlebot": ("Googlebot", "search"),
    "googleother": ("GoogleOther", "ai"),
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
    "ahrefsbot": ("AhrefsBot", "search"),
    "mj12bot": ("MJ12bot", "analytics"),
    "facebookexternalhit": ("Facebook", "social"),
    "meta-externalagent": ("Meta-ExternalAgent", "ai"),
    "meta-externalfetcher": ("Meta-ExternalFetcher", "ai"),
    "meta-webindexer": ("Meta-WebIndexer", "search"),
    "bingpreview": ("BingPreview", "search"),
    "pinterest": ("Pinterest", "social"),
    "embedly": ("Embedly", "social"),
    "iframely": ("Iframely", "social"),
    "discordbot": ("Discord", "social"),
    "slackbot": ("Slack", "social"),
    "telegrambot": ("Telegram", "social"),
    "twitterbot": ("Twitter", "social"),
    "linkedinbot": ("LinkedIn", "social"),
    "whatsapp": ("WhatsApp", "social"),
    "headlesschrome": ("HeadlessChrome", "spider"),
    "uptimerobot": ("UptimeRobot", "analytics"),
    "pingdom": ("Pingdom", "analytics"),
}

#: Pretty suffixes for the kinds more precise than a generic spider.
KIND_LABEL = {
    "ai": "AI",
    "search": "search",
    "social": "social",
    "analytics": "analytics",
}

#: Crawler product families: provider -> the display names of its bots.
#: The kind label is kept only where it distinguishes siblings within a family.
PROVIDERS = {
    "Google": frozenset({
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
    }),
    "Anthropic": frozenset({"ClaudeBot", "Claude-User", "Claude-SearchBot"}),
    "OpenAI": frozenset({"GPTBot", "OAI-SearchBot", "ChatGPT-User"}),
    "Perplexity": frozenset({"PerplexityBot", "Perplexity-User"}),
    "Amazon": frozenset({"Amazonbot", "Amzn-SearchBot"}),
    "Microsoft": frozenset({"Bingbot", "BingPreview"}),
    "Meta": frozenset({
        "Facebook",
        "Meta-ExternalAgent",
        "Meta-ExternalFetcher",
        "Meta-WebIndexer",
    }),
}

#: Reverse lookup: bot display name -> provider.
PROVIDER_OF = {
    name: provider for provider, names in PROVIDERS.items() for name in names
}

#: Per-bot pretty overrides: the full display string, replacing the
#: name-plus-kind-label composition entirely.
PRETTY_OVERRIDE = {
    "Facebook": "Facebook",
    "Feedfetcher-Google": "Google Feedfetcher (search)",
    "Google-InspectionTool": "Google InspectionTool (search)",
    "Google-Read-Aloud": "Google Read-Aloud (AI)",
    "Mediapartners-Google": "Google Mediapartners (analytics)",
    "AdsBot-Google": "Google AdsBot (analytics)",
    "APIs-Google": "Google APIs",
    "Storebot-Google": "Google Storebot (search)",
    "Google-Extended": "Google Extended (AI)",
    "GoogleOther": "Google Other (AI)",
}

#: Reverse lookup: bot display name -> kind.
NAME_KIND = {name: kind for name, kind in BOTS.values()}

#: Bot names whose kind label is displayed: those in families with mixed kinds.
LABELED = {
    name
    for names in PROVIDERS.values()
    if len({NAME_KIND[name] for name in names}) > 1
    for name in names
}
