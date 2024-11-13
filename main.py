import json
import logging
import sys
from datetime import datetime
from typing import Iterable

from motor import motor_asyncio
from pydantic import BaseModel
from pymongo import UpdateOne

from core.api_clients import ElectionAPIClient
from core.config import settings


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

mongo_client = motor_asyncio.AsyncIOMotorClient(str(settings.mongo_url))
db = getattr(mongo_client, settings.election_db_name)


async def upsert_mongo_docs(collection_name: str, docs: list[dict], fields: Iterable[str]):
    collection = getattr(db, collection_name)

    fields = set(fields)
    operations = []

    for doc in docs:
        if all(field in doc for field in fields):
            filter_criteria = {field: doc[field] for field in fields if field in doc}
            logging.debug(f"Filter criteria: {filter_criteria} for document: {doc}")

            operations.append(
                UpdateOne(
                    {field: doc[field] for field in fields},
                    {"$set": doc},
                    upsert=True
                )
            )
        else:
            logging.warning(f"Document missing required fields: {doc}")

    if operations:
        result = await collection.bulk_write(operations)
        logging.info(f"Modified: {result.modified_count}, Upserted: {result.upserted_count}")


def get_cities():
    with open(settings.cities_json_file) as file:
        return json.load(file)


class Item(BaseModel):
    name: str
    position: int
    region_id: int
    city_slug: str
    percent: str
    count: int
    update_ts: float


async def parse_party_voices():
    api_client = ElectionAPIClient(election_id=settings.election_id)

    cities = get_cities()
    collected_items = []

    for city_meta in cities:
        division_id, region_id, city_slug = city_meta["id"], city_meta["region_id"], city_meta["slug"]

        result = await api_client.ballot_count(
            election_type=settings.election_type,
            division_id=division_id  # in this case we sent str, but it's also work!
        )

        founded_ballots = None

        for b_c in result["ballotCounts"]:
            if b_c["division"]["id"] == division_id:
                # it will be much faster to find them through the keys by position
                founded_ballots = {c["position"]: c for c in b_c["ballotCounts"]}
                break

        if founded_ballots is None:
            logging.warning(
                f"Not found ballots for region: {region_id} city: {city_slug}"
            )
            continue

        ballots = [
            dict(
                Item(
                    name=b["name_ky"] or b["name_ru"],
                    position=b["position"],
                    region_id=region_id,
                    city_slug=city_slug,
                    percent=founded_ballots.get(b["position"], {}).get("pcosPercent", "0%"),
                    count=founded_ballots.get(b["position"], {}).get("pcosCount", 0),
                    update_ts=datetime.utcnow().timestamp()
                )
            )
            for b in result["ballots"]
        ]
        collected_items.extend(ballots)

    return collected_items


async def main():
    logging.info("Start parse party voices...")
    items = await parse_party_voices()

    if items:
        logging.info("Saving items...")

        await upsert_mongo_docs(
            collection_name=settings.voices_collection,
            docs=items,
            fields=("name", "region_id", "city_slug")
        )
    else:
        logging.error("Not found any items!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

