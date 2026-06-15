import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from helpers.msft_container_images import (
    ContainerImageRecord,
    initialize_database,
    parse_image_readme,
    upsert_records,
)


README = """
# Python

## Summary

*Develop Python applications with common tools preinstalled.*

| Metadata | Value |
|----------|-------|
| *Categories* | Languages, Python |
| *Image type* | Dockerfile |
| *Published images* | `mcr.microsoft.com/devcontainers/python`, `mcr.microsoft.com/vscode/devcontainers/python` |
"""


class MsftContainerImagesTest(unittest.TestCase):
    def test_parse_image_readme_extracts_searchable_metadata(self):
        record = parse_image_readme(
            path="src/python",
            readme=README,
            source_url="https://example.com/python/README.md",
            source_sha="abc123",
        )

        self.assertEqual(record.name, "python")
        self.assertEqual(record.title, "Python")
        self.assertEqual(record.summary, "Develop Python applications with common tools preinstalled.")
        self.assertEqual(record.categories, ["Languages", "Python"])
        self.assertEqual(
            record.published_images,
            ["mcr.microsoft.com/devcontainers/python", "mcr.microsoft.com/vscode/devcontainers/python"],
        )
        self.assertIn("mcr.microsoft.com/devcontainers/python", record.search_text)

    def test_upsert_records_creates_embedding_database_rows(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "images.db"
            conn = initialize_database(db_path)
            record = ContainerImageRecord(
                path="src/python",
                name="python",
                title="Python",
                summary="Python image",
                published_images=["mcr.microsoft.com/devcontainers/python"],
                categories=["Languages"],
                source_url="https://example.com",
                source_sha="abc123",
            )

            self.assertEqual(upsert_records(conn, [record], embeddings=[json.dumps([0.1, 0.2])]), 1)

            row = conn.execute(
                "SELECT name, published_images, categories, embedding FROM msft_container_images"
            ).fetchone()
            conn.close()

        self.assertEqual(row[0], "python")
        self.assertEqual(json.loads(row[1]), ["mcr.microsoft.com/devcontainers/python"])
        self.assertEqual(json.loads(row[2]), ["Languages"])
        self.assertEqual(json.loads(row[3]), [0.1, 0.2])

    def test_upsert_records_updates_existing_path(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "images.db"
            conn = initialize_database(db_path)
            first = ContainerImageRecord(
                path="src/base",
                name="base",
                title="Base",
                summary="Old summary",
                published_images=[],
                categories=[],
                source_url="https://example.com",
                source_sha="old",
            )
            second = ContainerImageRecord(
                path="src/base",
                name="base",
                title="Base",
                summary="New summary",
                published_images=[],
                categories=[],
                source_url="https://example.com",
                source_sha="new",
            )

            upsert_records(conn, [first], embeddings=["[1]"])
            upsert_records(conn, [second], embeddings=["[2]"])
            rows = conn.execute("SELECT summary, source_sha, embedding FROM msft_container_images").fetchall()
            conn.close()

        self.assertEqual(rows, [("New summary", "new", "[2]")])


if __name__ == "__main__":
    unittest.main()
