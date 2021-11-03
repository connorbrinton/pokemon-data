#/usr/bin/env python
import gzip
import json
import re

import boltons.iterutils
import requests
from loguru import logger


URL_RE = re.compile(r"^https://pokeapi\.co/api/v2/pokemon(/\d+/?)?(\?.*)?$")

uncrawled_urls = {"https://pokeapi.co/api/v2/pokemon"}
crawled = {}
while uncrawled_urls:
    # Grab an uncrawled page from the API
    url = uncrawled_urls.pop()

    # Announce crawling
    logger.info(f"Crawling: {url}")

    # Retrieve it
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    # Store it in the set of crawled URLs
    crawled[url] = data

    # Look for referenced URLs we can crawl
    research_results = boltons.iterutils.research(
        data,
        lambda path, key, value: key != "previous" and isinstance(value, str) and bool(URL_RE.match(value)),
    )

    # If we found any URLs to crawl, add them to the backlog
    if research_results:
        _paths, referenced_urls = zip(*research_results)

        # Ignore URLs we've already crawled
        crawlable_urls = set(referenced_urls) - crawled.keys()

        # Add the set of new URLs to the set of uncrawled URLs
        uncrawled_urls |= crawlable_urls

    # Announce crawling completion
    logger.info(f"Crawled: {url}")

# Write crawled data to a file
with gzip.open("pokemon.json.gz", "w") as sink:
    json.dump(crawled, sink)
