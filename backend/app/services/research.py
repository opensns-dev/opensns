"""
Product research service combining Playwright scraping with optional Firecrawl fallback.
"""

import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ResearchService:
    """
    Unified research service for product URL scraping.
    Uses Playwright for JS-rendered pages, with Firecrawl API as optional fallback.
    """

    def __init__(self, firecrawl_api_key: Optional[str] = None):
        self.firecrawl_api_key = firecrawl_api_key
        self.firecrawl_base_url = "https://api.firecrawl.dev/v1"

    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Scrape a product URL and extract structured information.

        Priority:
        1. Playwright (local, free, handles JS)
        2. Firecrawl API (if API key provided)
        3. Fallback data (if all methods fail)
        """
        if not url or not url.startswith(("http://", "https://")):
            logger.warning(f"Invalid URL: {url}")
            return self._fallback_data()

        # Try Playwright first (preferred method)
        try:
            result = await self._scrape_with_playwright(url)
            if result.get("title") and result.get("title") != "Unknown Product":
                logger.info(f"Successfully scraped with Playwright: {url}")
                return result
        except Exception as e:
            logger.warning(f"Playwright scraping failed: {e}")

        # Fallback to Firecrawl if API key available
        if self.firecrawl_api_key:
            try:
                result = await self._scrape_with_firecrawl(url)
                if result:
                    logger.info(f"Successfully scraped with Firecrawl: {url}")
                    return result
            except Exception as e:
                logger.warning(f"Firecrawl scraping failed: {e}")

        # Final fallback: basic HTTP scraping
        try:
            result = await self._scrape_basic(url)
            if result.get("title"):
                logger.info(f"Successfully scraped with basic HTTP: {url}")
                return result
        except Exception as e:
            logger.warning(f"Basic scraping failed: {e}")

        # Return fallback data if all methods fail
        logger.warning(f"All scraping methods failed for {url}, using fallback data")
        return self._fallback_data()

    async def _scrape_with_playwright(self, url: str) -> Dict[str, Any]:
        """Scrape using Playwright browser."""
        from app.services.scraper import PlaywrightScraper

        product_info = await PlaywrightScraper.scrape_url(url)
        return product_info.to_dict()

    async def _scrape_with_firecrawl(self, url: str) -> Dict[str, Any]:
        """Scrape using Firecrawl API."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.firecrawl_base_url}/scrape",
                json={
                    "url": url,
                    "formats": ["markdown", "html"],
                },
                headers={
                    "Authorization": f"Bearer {self.firecrawl_api_key}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

            if data.get("success") and data.get("data"):
                scraped = data["data"]
                return {
                    "title": scraped.get("metadata", {}).get("title", ""),
                    "description": scraped.get("metadata", {}).get("description", ""),
                    "features": [],  # Firecrawl doesn't extract features
                    "content": scraped.get("markdown", "")[:2000],
                    "images": [],
                    "metadata": scraped.get("metadata", {}),
                    "url": url,
                    "source": "firecrawl",
                }

        return {}

    async def _scrape_basic(self, url: str) -> Dict[str, Any]:
        """Basic HTTP scraping without JavaScript rendering."""
        from bs4 import BeautifulSoup

        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            },
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            # Extract basic info
            title = ""
            title_elem = soup.find("title")
            if title_elem:
                title = title_elem.get_text(strip=True)

            description = ""
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                description = meta_desc.get("content", "")

            # Get body text
            for tag in soup.find_all(["script", "style", "nav", "header", "footer"]):
                tag.decompose()
            content = soup.get_text(separator=" ", strip=True)[:2000]

            return {
                "title": title,
                "description": description,
                "features": [],
                "content": content,
                "images": [],
                "metadata": {},
                "url": url,
                "source": "basic",
            }

    def _fallback_data(self) -> Dict[str, Any]:
        return {
            "title": "Product Page",
            "description": "Product information unavailable - using fallback data.",
            "features": ["Feature 1", "Feature 2", "Feature 3"],
            "content": "Product details will be available after successful scraping.",
            "images": [],
            "metadata": {"fallback": True},
            "url": "",
            "source": "fallback",
        }


# Legacy compatibility - kept for backward compatibility
class FirecrawlService(ResearchService):
    """Alias for backward compatibility."""

    pass


# Default instance (no API key, will use Playwright)
research_service = ResearchService()

# Legacy instance name for compatibility
firecrawl_service = research_service
