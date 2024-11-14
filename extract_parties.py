import logging

import httpx
from lxml.html import fromstring

from core.config import settings
from db import upsert_mongo_docs
from utils import convert_party_slug

timeout = httpx.Timeout(120.0, connect=60.0)
client = httpx.AsyncClient(headers={"Content-Type": "text"}, timeout=timeout)


async def extract_parties(city_url: str):
    r = await client.get(city_url)
    party_elements = fromstring(r.text).xpath('//a[@class="parties__card"]')

    collected = []
    processed_parties = set()

    for el in party_elements:
        img, span = el.getchildren()
        original_party = next(span.itertext())
        slug = convert_party_slug(original_party)

        if slug in processed_parties:
            continue

        collected.append(
            {
                "img": img.get("src"),
                "name": original_party,
                "slug": slug
            }
        )
        processed_parties.add(slug)

    return collected


async def extract():
    base_url = "https://talapker.shailoo.gov.kg"
    # ky required because in election scraping parties has ky names
    resp = await client.get(url=base_url + "/ky/kenesh_gor")
    resp.raise_for_status()

    city_urls = fromstring(resp.text).xpath('//a[@class="kenesh__card"]/@href')
    collected = []

    for path in city_urls:
        url = base_url + path

        r = await client.get(url)
        if r.status_code != 200:
            continue

        parties = await extract_parties(url)
        collected.extend(parties)

    if collected:
        logging.info("Saving items...")

        await upsert_mongo_docs(
            collection_name=settings.parties_collection,
            docs=collected,
            fields=("slug",)
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(extract())
