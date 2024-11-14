import re

from unidecode import unidecode


def convert_party_slug(name: str):
    matches = re.findall(r'(["\'«»])(.+?)\1|«(.+?)»', name)
    results = [match[1] if match[1] else match[2] for match in matches]
    try:
        party_name = results[0]
    except IndexError:
        party_name = name
    return unidecode(party_name).lower().replace(" - ", "-").replace(" ", "_").strip()
