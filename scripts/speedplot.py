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
# fastuaparser (~1 µs, 1M parses/s) and cached results are too far off
# this scale to draw meaningfully and are only mentioned in the README.
US = {
    "uarite": 18.0,
    "ua-parser (Rust)": 38.1,
    "ua-parser (RE2)": 71.7,
    "ua-parser": 304.7,
    "user-agents": 324.6,
}

#: Readable on both white and dark backgrounds.
OUTSIDE = "#767676"

data = sorted(((n, 1e6 / us) for n, us in US.items()), key=lambda t: -t[1])
names = [n for n, _ in data][::-1]
values = [v for _, v in data][::-1]
colors = ["#6e6e6e"] * len(data)
colors[names.index("uarite")] = "#2b6cb0"

fig, ax = plt.subplots(figsize=(12, 1.5), dpi=100)
bars = ax.barh(names, values, color=colors, height=0.82)
xmax = max(values)
ax.set_xlim(0, xmax)
ax.axis("off")

for bar, name, v in zip(bars, names, values):
    # Round to two significant digits: 121951 -> "120 000".
    rounded = round(v, 1 - int(f"{v:.0e}".split("e")[1]))
    label = f"{rounded:,.0f}  {name}".replace(",", " ")
    # va="center" centers the font bbox incl. descender space, which leaves
    # the glyphs slightly high; nudge down to optically center on the bar.
    y = bar.get_y() + bar.get_height() / 2 - 0.09
    # All labels after the bar: theme-neutral gray, number before name.
    # The longest bar's label overflows the axes; bbox_inches="tight"
    # below expands the canvas to include it, so no dead space remains.
    ax.text(bar.get_width() + xmax * 0.012, y, label,
            va="center", color=OUTSIDE, fontsize=11)

out = Path("docs/bench-speed.svg")
out.parent.mkdir(exist_ok=True)
fig.savefig(out, transparent=True, bbox_inches="tight", pad_inches=0.02)
print("wrote", out)
