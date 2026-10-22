"""Reproducible, checksum-verified downloads. No reference data enters the production corpus."""

import argparse
from hashlib import sha256
from pathlib import Path
import sys
import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.astro.ephemeris import KERNELS

ASSETS = [
    (f"data/ephe/{name}", f"https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/{name}", digest)
    for name, digest in KERNELS.items()
]
ORACLE = (
    "refdata/kernels/de440s.bsp",
    "https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de440s.bsp",
    "c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2",
)
BOOK = (
    "refdata/books/pvr-integrated-approach.pdf",
    "https://www.vedicastrologer.org/articles/vedic_astro_textbook.pdf",
    "1cafa828f34764ed5e85816882df2e8f0bc014c5c57ccdb27169416e117fd4db",
)


def fetch(relative, url, expected):
    path = ROOT / relative
    if path.exists() and sha256(path.read_bytes()).hexdigest() == expected:
        print(f"verified {relative}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(follow_redirects=True, timeout=120) as client:
        response = client.get(url)
        response.raise_for_status()
    if sha256(response.content).hexdigest() != expected:
        raise SystemExit(
            f"Checksum mismatch: {relative}; investigate upstream changes, do not update blindly."
        )
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_bytes(response.content)
    temporary.replace(path)
    print(f"downloaded and verified {relative}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle", action="store_true", help="Download JPL DE440s for independent tests")
    parser.add_argument(
        "--book", action="store_true", help="Download author-hosted textbook for local study only"
    )
    args = parser.parse_args()
    for asset in ASSETS + ([ORACLE] if args.oracle else []) + ([BOOK] if args.book else []):
        fetch(*asset)
