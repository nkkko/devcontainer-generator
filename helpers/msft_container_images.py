import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, Optional
from urllib.request import urlopen


DEFAULT_IMAGES_REPO = "devcontainers/images"
DEFAULT_IMAGES_REF = "main"
DEFAULT_DB_PATH = Path("data/msft_container_images.db")
GITHUB_API_ROOT = "https://api.github.com/repos"
RAW_GITHUB_ROOT = "https://raw.githubusercontent.com"
DEFAULT_REQUEST_TIMEOUT = 20


@dataclass
class ContainerImageRecord:
    path: str
    name: str
    title: str
    summary: str
    published_images: list[str]
    categories: list[str]
    source_url: str
    source_sha: Optional[str]

    @property
    def search_text(self):
        parts = [
            self.name,
            self.title,
            self.summary,
            " ".join(self.categories),
            " ".join(self.published_images),
        ]
        return normalize_space(" ".join(part for part in parts if part))


def normalize_space(value):
    return re.sub(r"\s+", " ", value or "").strip()


def split_table_values(value):
    value = re.sub(r"<br\s*/?>", ",", value or "", flags=re.IGNORECASE)
    value = re.sub(r"`", "", value)
    return [normalize_space(part) for part in re.split(r",|;", value) if normalize_space(part)]


def parse_image_readme(path, readme, source_url, source_sha=None):
    title_match = re.search(r"^#\s+(.+)$", readme, flags=re.MULTILINE)
    summary_match = re.search(r"## Summary\s+\*([^*]+)\*", readme, flags=re.DOTALL)

    metadata = {}
    for row in re.findall(r"^\|\s*\*([^*]+)\*\s*\|\s*(.*?)\s*\|\s*$", readme, flags=re.MULTILINE):
        metadata[normalize_space(row[0]).lower()] = normalize_space(row[1])

    name = path.rstrip("/").split("/")[-1]
    return ContainerImageRecord(
        path=path,
        name=name,
        title=normalize_space(title_match.group(1)) if title_match else name,
        summary=normalize_space(summary_match.group(1)) if summary_match else "",
        published_images=split_table_values(metadata.get("published images", "")),
        categories=split_table_values(metadata.get("categories", "")),
        source_url=source_url,
        source_sha=source_sha,
    )


def open_url(url, opener=urlopen):
    try:
        return opener(url, timeout=DEFAULT_REQUEST_TIMEOUT)
    except TypeError:
        return opener(url)


def fetch_json(url, opener=urlopen):
    with open_url(url, opener=opener) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_text(url, opener=urlopen):
    with open_url(url, opener=opener) as response:
        return response.read().decode("utf-8")


def fetch_msft_container_image_records(
    repo=DEFAULT_IMAGES_REPO,
    ref=DEFAULT_IMAGES_REF,
    opener=urlopen,
):
    src_url = f"{GITHUB_API_ROOT}/{repo}/contents/src?ref={ref}"
    src_items = fetch_json(src_url, opener=opener)
    records = []

    for item in src_items:
        if item.get("type") != "dir":
            continue

        path = item["path"]
        readme_url = f"{RAW_GITHUB_ROOT}/{repo}/{ref}/{path}/README.md"
        try:
            readme = fetch_text(readme_url, opener=opener)
        except Exception:
            continue

        records.append(
            parse_image_readme(
                path=path,
                readme=readme,
                source_url=readme_url,
                source_sha=item.get("sha"),
            )
        )

    return records


def initialize_database(db_path=DEFAULT_DB_PATH):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS msft_container_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            published_images TEXT NOT NULL,
            categories TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_sha TEXT,
            search_text TEXT NOT NULL,
            embedding TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_msft_container_images_name
        ON msft_container_images (name)
        """
    )
    return conn


def embed_records(records, embedding_client, model):
    texts = [record.search_text for record in records]
    response = embedding_client.embeddings.create(input=texts, model=model)
    return [json.dumps(item.embedding) for item in response.data]


def upsert_records(conn, records: Iterable[ContainerImageRecord], embeddings=None):
    records = list(records)
    embeddings = embeddings or [None] * len(records)
    updated_at = datetime.utcnow().isoformat()

    for record, embedding in zip(records, embeddings):
        conn.execute(
            """
            INSERT INTO msft_container_images (
                path,
                name,
                title,
                summary,
                published_images,
                categories,
                source_url,
                source_sha,
                search_text,
                embedding,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                name = excluded.name,
                title = excluded.title,
                summary = excluded.summary,
                published_images = excluded.published_images,
                categories = excluded.categories,
                source_url = excluded.source_url,
                source_sha = excluded.source_sha,
                search_text = excluded.search_text,
                embedding = excluded.embedding,
                updated_at = excluded.updated_at
            """,
            (
                record.path,
                record.name,
                record.title,
                record.summary,
                json.dumps(record.published_images),
                json.dumps(record.categories),
                record.source_url,
                record.source_sha,
                record.search_text,
                embedding,
                updated_at,
            ),
        )

    conn.commit()
    return len(records)


def build_database(
    db_path=DEFAULT_DB_PATH,
    repo=DEFAULT_IMAGES_REPO,
    ref=DEFAULT_IMAGES_REF,
    embedding_client=None,
    embedding_model=None,
    opener=urlopen,
):
    records = fetch_msft_container_image_records(repo=repo, ref=ref, opener=opener)
    embeddings = None
    if embedding_client and embedding_model:
        embeddings = embed_records(records, embedding_client, embedding_model)

    conn = initialize_database(db_path)
    try:
        return upsert_records(conn, records, embeddings=embeddings)
    finally:
        conn.close()
