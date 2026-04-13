from __future__ import annotations

import argparse
import json
from collections.abc import Mapping

from eunigraph.core.config import get_settings
from eunigraph.modules.ingestion.application.openaire_beginners_kit import (
    OpenAireBeginnersKitSeeder,
)
from eunigraph.persistence.postgres.session import create_session


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed EuniGraph from the OpenAIRE Beginner's Kit.",
    )
    parser.add_argument("command", choices=["load", "reset", "status"])
    parser.add_argument("--limit-per-file", type=int, default=None)
    args = parser.parse_args()

    session = create_session()
    try:
        seeder = OpenAireBeginnersKitSeeder(session, get_settings())
        result: Mapping[str, object]
        if args.command == "load":
            result = seeder.load(limit_per_file=args.limit_per_file)
        elif args.command == "reset":
            result = seeder.reset()
        else:
            result = seeder.get_status().__dict__
        print(json.dumps(result, default=str, indent=2))
    finally:
        session.close()


if __name__ == "__main__":
    main()
