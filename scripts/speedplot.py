# /// script
# requires-python = ">=3.14"
# dependencies = ["matplotlib"]
# ///
"""Bar chart of cold-parse throughput for the README's Performance section.

Numbers are pasted from `uv run scripts/bench.py` (the cold 50/50
browser/crawler mix, µs per parse) and shown as parses per second.
Transparent SVG, text baked to paths, neutral grays: renders the same
on light and dark themes.  All labels sit on the bars themselves.
Very wide aspect ratio: forges render images at full content width,
so height alone controls how tall it appears.

    uv run scripts/speedplot.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "path"  # text as paths: renders anywhere
import matplotlib.pyplot as plt  # noqa: E402

# µs per cold parse, from scripts/bench.py.
US = {
    "user-agent-parser": 8.2,
    "uarite": 17.7,
    "ua-parser (Rust)": 46.6,
    "ua-parser (RE2)": 77.1,
    "ua-parser": 321.5,
    "user-agents": 334.4,
}

#: Readable on both white and dark backgrounds.
OUTSIDE = "#767676"

data = sorted(((n, 1e6 / us) for n, us in US.items()), key=lambda t: -t[1])
names = [n for n, _ in data][::-1]
values = [v for _, v in data][::-1]
colors = ["#6e6e6e"] * len(data)
colors[names.index("uarite")] = "#2b6cb0"

fig, ax = plt.subplots(figsize=(12, 1.7), dpi=100)
bars = ax.barh(names, values, color=colors, height=0.82)
ax.set_xlim(0, max(values))
ax.axis("off")

for bar, name, v in zip(bars, names, values):
    # Round to two significant digits: 121951 -> "120 000".
    rounded = round(v, 1 - int(f"{v:.0e}".split("e")[1]))
    label = f"{name}  {rounded:,.0f}".replace(",", " ")
    # va="center" centers the font bbox incl. descender space, which leaves
    # the glyphs slightly high; nudge down to optically center on the bar.
    y = bar.get_y() + bar.get_height() / 2 - 0.09
    if bar.get_width() > max(values) * 0.28:
        # Long bar: white text inside, right-aligned at the bar end.
        ax.text(bar.get_width() - max(values) * 0.012, y, label,
                va="center", ha="right", color="white", fontsize=11)
    else:
        # Short bar: theme-neutral gray text just past the bar end.
        ax.text(bar.get_width() + max(values) * 0.012, y, label,
                va="center", color=OUTSIDE, fontsize=11)

fig.tight_layout(pad=0.2)
out = Path("docs/bench-speed.svg")
out.parent.mkdir(exist_ok=True)
fig.savefig(out, transparent=True)
print("wrote", out)
