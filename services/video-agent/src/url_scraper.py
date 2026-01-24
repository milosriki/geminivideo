"""
URL Asset Scraper
Extracts images, text, and metadata from product URLs for video generation.
"""
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Dict, List, Any
import re

logger = logging.getLogger(__name__)

class URLAssetScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def scrape(self, url: str) -> Dict[str, Any]:
        """
        Scrape assets from a URL
        """
        try:
            logger.info(f"Scraping URL: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract Metadata
            title = self._get_meta_content(soup, 'og:title') or soup.title.string
            description = self._get_meta_content(soup, 'og:description') or self._get_meta_content(soup, 'description')
            
            # Extract Images
            images = self._extract_images(soup, url)
            
            # Extract Text Content (for script generation)
            text_content = self._extract_text(soup)
            
            return {
                "url": url,
                "title": title,
                "description": description,
                "images": images[:10], # Top 10 images
                "text_content": text_content[:2000], # First 2000 chars
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            return {
                "url": url,
                "status": "error",
                "error": str(e)
            }

    def _get_meta_content(self, soup, property_name):
        tag = soup.find('meta', property=property_name) or soup.find('meta', attrs={'name': property_name})
        return tag['content'] if tag else None

    def _extract_images(self, soup, base_url) -> List[str]:
        images = []
        
        # 1. OG Image
        og_image = self._get_meta_content(soup, 'og:image')
        if og_image:
            images.append(urljoin(base_url, og_image))
            
        # 2. Product Images (heuristics)
        for img in soup.find_all('img'):
            src = img.get('src')
            if not src:
                continue
                
            full_url = urljoin(base_url, src)
            
            # Filter out small icons/tracking pixels
            width = img.get('width')
            height = img.get('height')
            
            if width and int(width) < 100: continue
            if height and int(height) < 100: continue
            
            # Filter by keywords
            if any(x in src.lower() for x in ['product', 'gallery', 'upload', 'cdn']):
                images.append(full_url)
                
        return list(set(images)) # Deduplicate

    def _extract_text(self, soup) -> str:
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()
            
        text = soup.get_text()
        
        # Break into lines and remove leading/trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text

# Global instance
url_scraper = URLAssetScraper()
