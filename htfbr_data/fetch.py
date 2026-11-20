"""Cached, provenance-recording downloads.

Every fetched file is stored under data/raw/<source_id>/ and registered in the
`artifact` table with its URL, zip member, SHA-256, size and retrieval time.
Members of large remote zip archives are read with HTTP range requests, so a
single ENDF evaluation can be pulled from a 300 MB library archive.
"""
from __future__ import annotations

import hashlib
import io
import re
import sqlite3
import time
import zipfile
from pathlib import Path

import requests

from .db import ROOT, utcnow

RAW_DIR = ROOT / "data" / "raw"
USER_AGENT = "htfbr-data/0.1 (research database builder)"
_session = requests.Session()
_session.headers["User-Agent"] = USER_AGENT


def _get(url: str, *, headers: dict | None = None, retries: int = 4, timeout: int = 120) -> requests.Response:
    delay = 2.0
    for attempt in range(retries):
        try:
            r = _session.get(url, headers=headers or {}, timeout=timeout)
            if r.status_code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                raise requests.HTTPError(f"HTTP {r.status_code}")
            r.raise_for_status()
            return r
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError):
            if attempt == retries - 1:
                raise
            time.sleep(delay)
            delay *= 2
    raise RuntimeError("unreachable")


def _safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", text)[-120:]


def _register(con: sqlite3.Connection, source_id: str, url: str, member: str, data: bytes, name: str) -> tuple[int, Path]:
    sha = hashlib.sha256(data).hexdigest()
    row = con.execute(
        "SELECT artifact_id, local_path FROM artifact WHERE url=? AND member=? AND sha256=?", (url, member, sha)
    ).fetchone()
    if row:
        return row["artifact_id"], Path(row["local_path"])
    path = RAW_DIR / source_id / f"{sha[:12]}_{_safe_name(name)}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    cur = con.execute(
        "INSERT INTO artifact (source_id, url, member, sha256, bytes, retrieved_at, local_path) VALUES (?,?,?,?,?,?,?)",
        (source_id, url, member, sha, len(data), utcnow(), str(path)),
    )
    con.commit()
    return cur.lastrowid, path


def cached(con: sqlite3.Connection, url: str, member: str = "") -> tuple[int, Path] | None:
    """Most recent artifact for (url, member), if one was fetched before."""
    row = con.execute(
        "SELECT artifact_id, local_path FROM artifact WHERE url=? AND member=? ORDER BY artifact_id DESC LIMIT 1",
        (url, member),
    ).fetchone()
    if row and Path(row["local_path"]).exists():
        return row["artifact_id"], Path(row["local_path"])
    return None


def fetch(con: sqlite3.Connection, source_id: str, url: str, *, refresh: bool = False) -> tuple[int, Path]:
    """Download `url` (or reuse the cached copy) and return (artifact_id, local_path)."""
    if not refresh and (hit := cached(con, url)):
        return hit
    data = _get(url).content
    return _register(con, source_id, url, "", data, url.rsplit("/", 1)[-1] or "index")


class HTTPRangeFile(io.RawIOBase):
    """Read-only, seekable view of a remote file using HTTP Range requests."""

    def __init__(self, url: str):
        self.url, self.pos = url, 0
        head = _session.head(url, timeout=60, allow_redirects=True)
        head.raise_for_status()
        self.size = int(head.headers["Content-Length"])

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, offset: int, whence: int = 0) -> int:
        self.pos = {0: offset, 1: self.pos + offset, 2: self.size + offset}[whence]
        return self.pos

    def readinto(self, buf) -> int:
        if self.pos >= self.size:
            return 0
        end = min(self.pos + len(buf), self.size) - 1
        r = _get(self.url, headers={"Range": f"bytes={self.pos}-{end}"})
        if r.status_code != 206:
            raise IOError(f"server ignored Range request for {self.url}")
        n = len(r.content)
        buf[:n] = r.content
        self.pos += n
        return n


class RemoteZip:
    """List and extract members of a remote zip without downloading the whole archive."""

    def __init__(self, url: str):
        self.url = url
        self._zip = zipfile.ZipFile(io.BufferedReader(HTTPRangeFile(url), buffer_size=1 << 20))

    def names(self) -> list[str]:
        return self._zip.namelist()

    def read(self, member: str) -> bytes:
        return self._zip.read(member)


def fetch_member(con: sqlite3.Connection, source_id: str, rz: RemoteZip, member: str, *, refresh: bool = False) -> tuple[int, Path]:
    if not refresh and (hit := cached(con, rz.url, member)):
        return hit
    return _register(con, source_id, rz.url, member, rz.read(member), member.rsplit("/", 1)[-1])
