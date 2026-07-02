import argparse
from pathlib import Path

from metadata.generated.schema.api.data.createGlossary import CreateGlossaryRequest
from metadata.generated.schema.api.data.createGlossaryTerm import (
    CreateGlossaryTermRequest,
)
from metadata.sdk import Glossaries, GlossaryTerms, configure
import yaml


def sync_glossary_file(path: Path) -> None:
    data = yaml.safe_load(path.read_text())

    glossary = Glossaries.create(
        CreateGlossaryRequest(
            name=data["name"],
            displayName=data.get("displayName"),
            description=data.get("description"),
            reviewers=None,
            owners=None,
            tags=None,
            mutuallyExclusive=False,
            domains=None,
            extension=None,
        )
    )
    print(f"Synced glossary: {glossary.name.root}")

    for term in data.get("terms", []):
        created = GlossaryTerms.create(
            CreateGlossaryTermRequest(
                glossary=data["name"],
                name=term["name"],
                displayName=term.get("displayName"),
                description=term.get("description"),
                synonyms=term.get("synonyms"),
                relatedTerms=term.get("relatedTerms"),
                parent=None,
                references=None,
                conceptMappings=None,
                reviewers=None,
                owners=None,
                tags=None,
                mutuallyExclusive=False,
                extension=None,
            )
        )
        print(f"  Synced term: {created.name.root}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--host-port", required=True)
    parser.add_argument("--jwt-token", required=True)
    args = parser.parse_args()

    configure(host=args.host_port, jwt_token=args.jwt_token)
    sync_glossary_file(Path(args.config))


if __name__ == "__main__":
    main()
