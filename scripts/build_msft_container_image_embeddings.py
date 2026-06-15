import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv():
        return False

from helpers.msft_container_images import (
    DEFAULT_DB_PATH,
    DEFAULT_IMAGES_REF,
    DEFAULT_IMAGES_REPO,
    build_database,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build a local SQLite embedding database for Microsoft dev container images."
    )
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--repo", default=DEFAULT_IMAGES_REPO)
    parser.add_argument("--ref", default=DEFAULT_IMAGES_REF)
    parser.add_argument("--skip-embeddings", action="store_true")
    return parser.parse_args()


def main():
    load_dotenv()
    args = parse_args()
    embedding_model = os.getenv("EMBEDDING", "text-embedding-3-small")
    embedding_client = None
    if not args.skip_embeddings:
        from helpers.openai_helpers import setup_azure_openai

        embedding_client = setup_azure_openai()

    count = build_database(
        db_path=args.db_path,
        repo=args.repo,
        ref=args.ref,
        embedding_client=embedding_client,
        embedding_model=None if args.skip_embeddings else embedding_model,
    )
    print(f"Stored {count} Microsoft dev container image records in {args.db_path}")


if __name__ == "__main__":
    main()
