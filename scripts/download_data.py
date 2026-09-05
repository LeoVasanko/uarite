"""Download the external datasets used by the benchmark scripts.

- data/top-user-agents.json — 100 current real-browser UAs, from the
  top-user-agents npm package (src/index.json inside the tarball).
- data/crawler-user-agents.json — crawler patterns with sample UAs, from
  github.com/monperrus/crawler-user-agents.

data/ua.txt is not downloaded: it is a real traffic sample (unique
User-Agent strings seen by one site), committed alongside this script.
"""

import json
import tarfile
import urllib.request
from io import BytesIO
from pathlib import Path

DATA = Path(__file__).parent / "data"

CRAWLERS_URL = (
    "https://raw.githubusercontent.com/monperrus/crawler-user-agents/"
    "master/crawler-user-agents.json"
)
NPM_REGISTRY = "https://registry.npmjs.org/top-user-agents/latest"


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=120) as r:
        return r.read()


def main() -> None:
    DATA.mkdir(exist_ok=True)

    crawlers = DATA / "crawler-user-agents.json"
    print(f"downloading {CRAWLERS_URL}")
    crawlers.write_bytes(fetch(CRAWLERS_URL))

    print("resolving latest top-user-agents from the npm registry")
    meta = json.loads(fetch(NPM_REGISTRY))
    tarball = fetch(meta["dist"]["tarball"])
    with tarfile.open(fileobj=BytesIO(tarball), mode="r:gz") as tar:
        top = tar.extractfile("package/src/index.json").read()
    (DATA / "top-user-agents.json").write_bytes(top)

    for f in ("crawler-user-agents.json", "top-user-agents.json"):
        n = len(json.loads((DATA / f).read_text()))
        print(f"{f}: {n} entries")


if __name__ == "__main__":
    main()
