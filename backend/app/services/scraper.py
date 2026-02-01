"""
Playwright-based web scraper for product page extraction.
Handles JavaScript-rendered pages with automatic content extraction.
"""

import asyncio
import logging
import re
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class ProductInfo:
    """Extracted product information from a URL."""

    title: str = ""
    description: str = ""
    features: List[str] = field(default_factory=list)
    price: Optional[str] = None
    images: List[str] = field(default_factory=list)
    content: str = ""
    url: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "features": self.features,
            "price": self.price,
            "images": self.images,
            "content": self.content,
            "url": self.url,
            "metadata": self.metadata,
        }


class PlaywrightScraper:
    """
    Async web scraper using Playwright for JavaScript-rendered pages.
    Uses a browser pool for efficiency.
    """

    _browser = None
    _lock = asyncio.Lock()
    _initialized = False

    @classmethod
    async def _ensure_browser(cls):
        """Lazy-initialize browser on first use."""
        if cls._browser is not None:
            return cls._browser

        async with cls._lock:
            if cls._browser is not None:
                return cls._browser

            try:
                from playwright.async_api import async_playwright

                cls._playwright = await async_playwright().start()
                cls._browser = await cls._playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                    ],
                )
                cls._initialized = True
                logger.info("Playwright browser initialized")
                return cls._browser
            except Exception as e:
                logger.error(f"Failed to initialize Playwright: {e}")
                raise RuntimeError(
                    "Playwright not installed. Run: playwright install chromium"
                ) from e

    @classmethod
    async def close(cls):
        """Close browser and cleanup resources."""
        async with cls._lock:
            if cls._browser:
                await cls._browser.close()
                cls._browser = None
            if hasattr(cls, "_playwright") and cls._playwright:
                await cls._playwright.stop()
                cls._playwright = None
            cls._initialized = False
            logger.info("Playwright browser closed")

    @classmethod
    @asynccontextmanager
    async def get_page(cls):
        """Context manager for browser page."""
        browser = await cls._ensure_browser()
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
        )
        page = await context.new_page()
        try:
            yield page
        finally:
            await context.close()

    @classmethod
    async def scrape_url(
        cls,
        url: str,
        wait_for_selector: Optional[str] = None,
        timeout: int = 30000,
    ) -> ProductInfo:
        """
        Scrape a product page and extract structured information.

        Args:
            url: Product page URL
            wait_for_selector: Optional CSS selector to wait for
            timeout: Page load timeout in milliseconds

        Returns:
            ProductInfo with extracted data
        """
        result = ProductInfo(url=url)

        try:
            async with cls.get_page() as page:
                # Navigate to page
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout)

                # Wait for content to load
                if wait_for_selector:
                    try:
                        await page.wait_for_selector(wait_for_selector, timeout=5000)
                    except Exception:
                        pass  # Continue even if selector not found

                # Wait a bit for dynamic content
                await asyncio.sleep(1)

                # Get page content
                html = await page.content()
                soup = BeautifulSoup(html, "lxml")

                # Extract title
                result.title = cls._extract_title(soup, page)

                # Extract description
                result.description = cls._extract_description(soup)

                # Extract price
                result.price = cls._extract_price(soup)

                # Extract images
                result.images = cls._extract_images(soup, url)

                # Extract features/bullet points
                result.features = cls._extract_features(soup)

                # Extract main content
                result.content = cls._extract_content(soup)

                # Extract metadata
                result.metadata = cls._extract_metadata(soup)

                logger.info(f"Successfully scraped: {url}")

        except Exception as e:
            logger.error(f"Scraping failed for {url}: {e}")
            result.metadata["error"] = str(e)

        return result

    @staticmethod
    def _extract_title(soup: BeautifulSoup, page=None) -> str:
        """Extract product title from page."""
        # Try common product title patterns
        selectors = [
            "h1.product-title",
            "h1.product-name",
            "h1[itemprop='name']",
            ".product-title h1",
            "#product-title",
            "h1",
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem and elem.get_text(strip=True):
                return elem.get_text(strip=True)

        # Fallback to page title
        title_elem = soup.find("title")
        if title_elem:
            title = title_elem.get_text(strip=True)
            # Remove common suffixes
            for suffix in [" | ", " - ", " – ", " :: "]:
                if suffix in title:
                    title = title.split(suffix)[0]
            return title

        return "Unknown Product"

    @staticmethod
    def _extract_description(soup: BeautifulSoup) -> str:
        """Extract product description."""
        # Try meta description first
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            return meta_desc["content"]

        # Try Open Graph description
        og_desc = soup.find("meta", attrs={"property": "og:description"})
        if og_desc and og_desc.get("content"):
            return og_desc["content"]

        # Try common description selectors
        selectors = [
            ".product-description",
            "#product-description",
            "[itemprop='description']",
            ".description",
            ".product-info",
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if len(text) > 20:
                    return text[:500]

        return ""

    @staticmethod
    def _extract_price(soup: BeautifulSoup) -> Optional[str]:
        """Extract product price."""
        selectors = [
            "[itemprop='price']",
            ".price",
            ".product-price",
            "#price",
            ".current-price",
            ".sale-price",
            "[data-price]",
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                price = (
                    elem.get("content")
                    or elem.get("data-price")
                    or elem.get_text(strip=True)
                )
                if price:
                    # Clean up price string
                    price = re.sub(r"\s+", " ", price).strip()
                    return price

        # Look for price patterns in text
        price_pattern = r"[\$\€\£\₩][\d,]+(?:\.\d{2})?"
        for text in soup.stripped_strings:
            match = re.search(price_pattern, text)
            if match:
                return match.group()

        return None

    @staticmethod
    def _extract_images(soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract product images."""
        images = []
        parsed_base = urlparse(base_url)

        # Try common image selectors
        selectors = [
            ".product-image img",
            ".gallery img",
            "[itemprop='image']",
            ".product-gallery img",
            "#product-images img",
            ".main-image img",
        ]

        for selector in selectors:
            for img in soup.select(selector):
                src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
                if src:
                    # Make absolute URL
                    if src.startswith("//"):
                        src = f"{parsed_base.scheme}:{src}"
                    elif src.startswith("/"):
                        src = f"{parsed_base.scheme}://{parsed_base.netloc}{src}"
                    if src not in images and not src.endswith(".svg"):
                        images.append(src)

        return images[:10]  # Limit to 10 images

    @staticmethod
    def _extract_features(soup: BeautifulSoup) -> List[str]:
        """Extract product features/bullet points."""
        features = []

        # Try common feature list selectors
        selectors = [
            ".product-features li",
            ".features li",
            ".product-highlights li",
            "[itemprop='description'] li",
            ".product-info li",
            ".specifications li",
        ]

        for selector in selectors:
            items = soup.select(selector)
            if items:
                for item in items[:10]:
                    text = item.get_text(strip=True)
                    if text and len(text) > 5:
                        features.append(text)
                if features:
                    break

        return features

    @staticmethod
    def _extract_content(soup: BeautifulSoup) -> str:
        """Extract main content text."""
        # Remove script, style, nav, header, footer
        for tag in soup.find_all(
            ["script", "style", "nav", "header", "footer", "aside"]
        ):
            tag.decompose()

        # Try to find main content area
        main_selectors = [
            "main",
            "#main",
            ".main-content",
            "#content",
            ".product-content",
            "article",
        ]

        for selector in main_selectors:
            main = soup.select_one(selector)
            if main:
                text = main.get_text(separator=" ", strip=True)
                text = re.sub(r"\s+", " ", text)
                return text[:2000]

        # Fallback to body
        body = soup.find("body")
        if body:
            text = body.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text)
            return text[:2000]

        return ""

    @staticmethod
    def _extract_metadata(soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract additional metadata from page."""
        metadata = {}

        # Open Graph data
        og_tags = soup.find_all("meta", attrs={"property": re.compile(r"^og:")})
        for tag in og_tags:
            prop = tag.get("property", "").replace("og:", "")
            content = tag.get("content")
            if prop and content:
                metadata[f"og_{prop}"] = content

        # Schema.org JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                import json

                data = json.loads(script.string)
                if isinstance(data, dict):
                    if data.get("@type") == "Product":
                        metadata["schema_product"] = data
                    elif data.get("@type") == "WebPage":
                        metadata["schema_webpage"] = data
            except Exception:
                pass

        return metadata


# Singleton instance
playwright_scraper = PlaywrightScraper()
