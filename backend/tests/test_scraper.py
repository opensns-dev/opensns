"""
Test script for PlaywrightScraper.
Run with: python -m pytest backend/tests/test_scraper.py -v
Or directly: python backend/tests/test_scraper.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.scraper import PlaywrightScraper
from app.services.research import ResearchService


async def test_scraper_directly():
    """Test the PlaywrightScraper with a real URL."""
    test_urls = [
        "https://www.apple.com/shop/buy-mac/macbook-air",
        "https://www.amazon.com/dp/B0CHX3QBCH",
    ]

    for url in test_urls:
        print(f"\n{'=' * 60}")
        print(f"Testing URL: {url}")
        print("=" * 60)

        try:
            result = await PlaywrightScraper.scrape_url(url, timeout=30000)
            print(f"Title: {result.title}")
            print(
                f"Description: {result.description[:200]}..."
                if result.description
                else "Description: N/A"
            )
            print(f"Price: {result.price}")
            print(
                f"Features: {result.features[:3]}"
                if result.features
                else "Features: N/A"
            )
            print(f"Images: {len(result.images)} found")
            print(f"Content length: {len(result.content)} chars")
        except Exception as e:
            print(f"Error: {e}")

    await PlaywrightScraper.close()


async def test_research_service():
    """Test the ResearchService with fallback chain."""
    service = ResearchService()

    url = "https://www.apple.com/shop/buy-mac/macbook-air"
    print(f"\nTesting ResearchService with: {url}")

    result = await service.scrape_url(url)
    print(f"Source: {result.get('source', 'unknown')}")
    print(f"Title: {result.get('title', 'N/A')}")
    print(f"Description: {result.get('description', 'N/A')[:100]}...")

    await PlaywrightScraper.close()


if __name__ == "__main__":
    print("Testing PlaywrightScraper...")
    print("Make sure to run: playwright install chromium")
    print()

    asyncio.run(test_scraper_directly())
