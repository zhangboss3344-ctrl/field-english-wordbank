#!/usr/bin/env python3
"""Build a compact Field English CSV from ECDICT plus curated project vocabulary.

The Android V1.3.1 client enforces <= 20,000 parsed entries and <= 8 MiB per CSV.
This script keeps a maximum of 15,000 ECDICT-derived entries plus the curated list.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

MAX_ECDICT_ENTRIES = 15000
MAX_TOTAL_ENTRIES = 19999
MAX_FILE_BYTES = 8 * 1024 * 1024
HEADER = ["index", "英文", "中文", "分类", "备注"]
ECDICT_URL = "https://raw.githubusercontent.com/skywind3000/ECDICT/master/ecdict.csv"
PUBLISHED_URL = "https://raw.githubusercontent.com/zhangboss3344-ctrl/field-english-wordbank/main/field_english_words.csv"
MANIFEST_URL = "https://raw.githubusercontent.com/zhangboss3344-ctrl/field-english-wordbank/main/manifest.json"
WORD_RE = re.compile(r"^[A-Za-z][A-Za-z0-9'’./&+()\- ]{0,79}$")
EXAM_TAGS = {"cet4", "cet6", "ielts", "toefl", "gre", "gk", "zk", "kaoyan", "考研", "高考", "中考"}


def norm(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value or "").split()).casefold()


def clean(value: str, limit: int) -> str:
    parts = [" ".join(x.split()) for x in (value or "").replace("\r", "\n").split("\n")]
    text = "；".join(x for x in parts if x)
    return text[:limit].strip()


def rank_value(row: dict[str, str]) -> int:
    values = []
    for field in ("frq", "bnc"):
        raw = (row.get(field) or "").strip()
        try:
            n = int(float(raw))
            if n > 0:
                values.append(n)
        except (TypeError, ValueError):
            pass
    return min(values) if values else 999999


def category_for(word: str, tags: str) -> str:
    tagset = set(re.split(r"[\s,;/|]+", (tags or "").lower()))
    if tagset & EXAM_TAGS:
        return "考试英语"
    if " " in word.strip():
        return "常用短语"
    return "通用英语"


def make_notes(row: dict[str, str]) -> str:
    pieces = []
    phonetic = clean(row.get("phonetic", ""), 100)
    pos = clean(row.get("pos", ""), 100)
    definition = clean(row.get("definition", ""), 420)
    exchange = clean(row.get("exchange", ""), 160)
    if phonetic:
        pieces.append("音标: " + phonetic)
    if pos:
        pieces.append("词性: " + pos)
    if definition:
        pieces.append("英文释义: " + definition)
    if exchange:
        pieces.append("词形变化: " + exchange)
    return "；".join(pieces)[:800]


def read_curated(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != HEADER:
            raise ValueError(f"Curated CSV header must be exactly: {HEADER}")
        rows = []
        seen = set()
        for row in reader:
            word = clean(row.get("英文", ""), 300)
            meaning = clean(row.get("中文", ""), 500)
            key = norm(word)
            if not word or not meaning or key in seen:
                continue
            seen.add(key)
            rows.append({
                "index": str(row.get("index", len(rows))),
                "英文": word,
                "中文": meaning,
                "分类": clean(row.get("分类", ""), 90) or "工程英语",
                "备注": clean(row.get("备注", ""), 800),
            })
        return rows


def build_candidates(source: Path, curated_keys: set[str]) -> list[tuple[int, str, dict[str, str]]]:
    candidates: list[tuple[int, str, dict[str, str]]] = []
    seen = set(curated_keys)
    with source.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"word", "translation", "phonetic", "definition", "pos", "tag", "bnc", "frq", "oxford", "exchange"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError("ECDICT CSV missing fields: " + ", ".join(sorted(missing)))
        for row in reader:
            word = clean(row.get("word", ""), 300)
            meaning = clean(row.get("translation", ""), 500)
            if not word or not meaning or not WORD_RE.fullmatch(word):
                continue
            if len(word.split()) > 4:
                continue
            if len(word) == 1 and word.lower() not in {"a", "i"}:
                continue
            key = norm(word)
            if key in seen:
                continue
            tags = row.get("tag", "") or ""
            rank = rank_value(row)
            oxford = (row.get("oxford") or "").strip().lower() in {"1", "true", "yes"}
            tagset = set(re.split(r"[\s,;/|]+", tags.lower()))
            exam = bool(tagset & EXAM_TAGS)
            if rank > 50000 and not oxford and not exam:
                continue
            entry = {
                "index": "",
                "英文": word,
                "中文": meaning,
                "分类": category_for(word, tags),
                "备注": make_notes(row),
            }
            candidates.append((rank, key, entry))
            seen.add(key)

    candidates.sort(key=lambda x: (x[0], x[1]))
    return candidates[:MAX_ECDICT_ENTRIES]


def bump_patch(version: str) -> str:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version or "")
    if not match:
        return "1.0.1"
    major, minor, patch = map(int, match.groups())
    return f"{major}.{minor}.{patch + 1}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Path to upstream ECDICT CSV")
    parser.add_argument("--curated", default="curated/field_english_professional.csv")
    parser.add_argument("--output", default="field_english_words.csv")
    parser.add_argument("--manifest", default="manifest.json")
    args = parser.parse_args()

    source = Path(args.source)
    curated_path = Path(args.curated)
    output_path = Path(args.output)
    manifest_path = Path(args.manifest)

    curated = read_curated(curated_path)
    curated_keys = {norm(row["英文"]) for row in curated}
    candidates = build_candidates(source, curated_keys)

    generated = []
    for i, (_, _, entry) in enumerate(candidates, start=100000):
        entry["index"] = str(i)
        generated.append(entry)

    rows = curated + generated
    if len(rows) > MAX_TOTAL_ENTRIES:
        raise ValueError(f"Total rows exceed Android client limit: {len(rows)}")
    keys = [norm(row["英文"]) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate English headwords detected after merge.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)

    payload = output_path.read_bytes()
    if len(payload) > MAX_FILE_BYTES:
        raise ValueError(f"Generated CSV exceeds Android 8 MiB limit: {len(payload)} bytes")
    if len(rows) + 1 > 20000:
        raise ValueError("Generated CSV exceeds Android CSV parser row limit.")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    previous_hash = manifest.get("content", {}).get("sha256", "")
    digest = hashlib.sha256(payload).hexdigest()
    if digest != previous_hash:
        manifest["version"] = bump_patch(manifest.get("version", "1.0.0"))
        manifest["version_code"] = int(manifest.get("version_code", 0)) + 1
        manifest["updated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    manifest["description"] = "Field English 工程专业词库 + ECDICT 高频英汉词库"
    manifest["sources"] = [
        {
            "name": "ECDICT",
            "repository": "https://github.com/skywind3000/ECDICT",
            "license": "MIT (upstream repository license; see licenses/ECDICT-MIT-LICENSE.txt)",
            "selection": "最多 15,000 条高频词，按 BNC/当代词频、Oxford 标记及考试标签筛选",
        },
        {
            "name": "Field English curated professional vocabulary",
            "path": "curated/field_english_professional.csv",
            "license": "Field English project content",
        },
    ]
    content = manifest.setdefault("content", {})
    content.update({
        "type": "csv",
        "file_name": "field_english_words.csv",
        "url": PUBLISHED_URL,
        "encoding": "UTF-8",
        "delimiter": ",",
        "header": HEADER,
        "count": len(rows),
        "size_bytes": len(payload),
        "sha256": digest,
    })
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Curated professional entries: {len(curated)}")
    print(f"ECDICT-derived entries: {len(generated)}")
    print(f"Total entries: {len(rows)}")
    print(f"CSV bytes: {len(payload)}")
    print(f"SHA-256: {digest}")
    print(f"Manifest version: {manifest.get('version')} ({manifest.get('version_code')})")


if __name__ == "__main__":
    main()
