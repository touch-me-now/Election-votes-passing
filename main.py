import logging
import sys
from datetime import datetime

from pydantic import BaseModel

from core.api_clients import ElectionAPIClient
from core.config import settings
from db import upsert_mongo_docs, get_cities
from utils import convert_party_slug

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        # logging.FileHandler(settings.log_file_path)
    ]
)


class Item(BaseModel):
    party_slug: str
    name: str
    position: int
    region_id: int
    city_slug: str
    percent: str
    count: int
    update_ts: float


class ManualItem(BaseModel):
    city_slug: str
    three: int
    five: int 
    seven: int 
    eight: int 
    

async def parse_party_votes():
    api_client = ElectionAPIClient(election_id=settings.election_id)

    cities = await get_cities()
    collected_items = []
    collected_manual_items = []

    for city_meta in cities:
        division_id, region_id, city_slug = city_meta["id"], city_meta["region_id"], city_meta["slug"]

        result = await api_client.ballot_count(
            election_type=settings.election_type,
            division_id=division_id  # in this case we sent str, but it's also work!
        )

        overview = result.get("overview", {})
        pcos_count = overview.get("pcos", {})
        collected_manual_items.append(
            ManualItem(
                city_slug=city_slug,
                three=pcos_count.get("p3", 0),
                five=pcos_count.get("p5", 0),
                seven=pcos_count.get("p7", 0),
                eight=pcos_count.get("p8", 0)
            )
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
                    party_slug=convert_party_slug(b["name_ky"] or b["name_ru"]),
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
        

    return collected_manual_items, collected_items


async def main():
    logging.info("Start parse party votes...")
    manual_items, items = await parse_party_votes()
    
    if manual_items:
        logging.info("Saving manual items...")
        
        await upsert_mongo_docs(
            collection_name=settings.manual_votes,
            docs=manual_items,
            fields=("city_slug",)
        )
    else:
        logging.error("Not found any manual items!")
        
    if items:
        logging.info("Saving items...")

        await upsert_mongo_docs(
            collection_name=settings.votes_collection,
            docs=items,
            fields=("name", "region_id", "city_slug")
        )
    else:
        logging.error("Not found any items!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

