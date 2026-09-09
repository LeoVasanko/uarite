# Benchmark scripts

Recreate every statistic and table quoted in the top-level README.
`uarite` must be importable (e.g. `pip install -e .` or run with
`PYTHONPATH` pointing at the repo root); the reference parsers are
benchmark-only dependencies, pulled ad hoc via `uv run --with`.

- `download_data.py` — fetch the external datasets into `data/`:
  the 100 modern browser UAs (top-user-agents npm package) and the
  crawler corpus (monperrus/crawler-user-agents). `data/ua.txt` is a
  committed real-traffic sample, not downloaded.

  ```
  uv run scripts/download_data.py
  ```

- `prettytable.py` — prints the accuracy-comparison markdown table:

  ```
  uv run --with ua-parser --with fastuaparser python scripts/prettytable.py
  ```

- `bench.py` — prints browser-accuracy counts, crawler-detection rates,
  URL-extraction coverage, and the timing tables (unique UAs, realistic
  mix, bot storm) with cache statistics:

  ```
  uv run --with ua-parser --with user-agents --with fastuaparser \
      python scripts/bench.py
  ```
