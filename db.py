import logging
from typing import Iterable

from motor import motor_asyncio
from pymongo import UpdateOne

from core.config import settings


mongo_client = motor_asyncio.AsyncIOMotorClient(str(settings.mongo_url))
db = getattr(mongo_client, settings.election_db_name)


async def get_cities():
    collection = getattr(db, settings.cities_collection)
    return await collection.find({}).to_list()


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


async def test_mongo_connection():
    client = motor_asyncio.AsyncIOMotorClient(str(settings.mongo_url))
    try:
        databases = await client.list_database_names()
        logging.info(f"Available databases: {databases}")
    except Exception as e:
        logging.error(f"Failed to connect to MongoDB: {e}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(get_cities())
