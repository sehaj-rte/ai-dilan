import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
import time
import re
from typing import Dict, Any, Optional, List
import html2text

logger = logging.getLogger(__name__)

class WebScraperService:
    def __init__(self):
        self.session = requests.Session()
        # Set a user agent to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        self.html_converter.body_width = 0  # Don't wrap lines
        
    def scrape_url(self, url: str, max_length: int = 50000) -> Dict[str, Any]:
        """
        Scrape content from a URL and return structured data
        
        Args:
            url: The URL to scrape
            max_length: Maximum length of content to extract (default 50KB)
            
        Returns:
            Dict containing success status, content, metadata, and any errors
        """
        try:
            logger.info(f"🌐 Web Scraper: Starting to scrape URL: {url}")
            
            # Validate URL
            if not self._is_valid_url(url):
                return {
                    "success": False,
                    "error": "Invalid URL format"
                }
            
            # Make request with timeout
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                return {
                    "success": False,
                    "error": f"URL does not contain HTML content. Content-Type: {content_type}"
                }
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract metadata
            metadata = self._extract_metadata(soup, url)
            
            # Extract main content
            content = self._extract_content(soup)
            
            # Limit content length
            if len(content) > max_length:
                content = content[:max_length] + "\n\n[Content truncated due to length limit]"
                logger.warning(f"Content truncated to {max_length} characters")
            
            # Get word count
            word_count = len(content.split())
            
            logger.info(f"✅ Web Scraper: Successfully scraped {word_count} words from {url}")
            
            return {
                "success": True,
                "content": content,
                "metadata": {
                    **metadata,
                    "word_count": word_count,
                    "content_length": len(content),
                    "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "source_url": url
                }
            }
            
        except requests.exceptions.Timeout:
            logger.error(f"❌ Web Scraper: Timeout while scraping {url}")
            return {
                "success": False,
                "error": "Request timeout - the website took too long to respond"
            }
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Web Scraper: Connection error while scraping {url}")
            return {
                "success": False,
                "error": "Connection error - could not reach the website"
            }
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ Web Scraper: HTTP error while scraping {url}: {e}")
            return {
                "success": False,
                "error": f"HTTP error: {e.response.status_code} - {e.response.reason}"
            }
        except Exception as e:
            logger.error(f"❌ Web Scraper: Unexpected error while scraping {url}: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except:
            return False
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract metadata from HTML"""
        metadata = {}
        
        # Title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()
        
        # Meta description
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag:
            metadata['description'] = desc_tag.get('content', '').strip()
        
        # Open Graph metadata
        og_title = soup.find('meta', property='og:title')
        if og_title:
            metadata['og_title'] = og_title.get('content', '').strip()
        
        og_desc = soup.find('meta', property='og:description')
        if og_desc:
            metadata['og_description'] = og_desc.get('content', '').strip()
        
        # Author
        author_tag = soup.find('meta', attrs={'name': 'author'})
        if author_tag:
            metadata['author'] = author_tag.get('content', '').strip()
        
        # Keywords
        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_tag:
            metadata['keywords'] = keywords_tag.get('content', '').strip()
        
        # Domain
        parsed_url = urlparse(url)
        metadata['domain'] = parsed_url.netloc
        
        return metadata
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from HTML"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Try to find main content areas
        main_content = None
        
        # Look for common content containers
        content_selectors = [
            'main',
            'article',
            '[role="main"]',
            '.content',
            '.main-content',
            '.post-content',
            '.entry-content',
            '.article-content',
            '#content',
            '#main',
            '.container .content'
        ]
        
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                main_content = elements[0]
                break
        
        # If no main content found, use body
        if not main_content:
            main_content = soup.find('body')
        
        if not main_content:
            main_content = soup
        
        # Convert to markdown-like text
        content = self.html_converter.handle(str(main_content))
        
        # Clean up the content
        content = self._clean_content(content)
        
        return content
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize extracted content"""
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        content = re.sub(r'[ \t]+', ' ', content)
        
        # Remove common noise patterns
        noise_patterns = [
            r'Cookie Policy.*?Accept',
            r'This website uses cookies.*?(?=\n|$)',
            r'Subscribe to our newsletter.*?(?=\n|$)',
            r'Sign up for.*?(?=\n|$)',
            r'Follow us on.*?(?=\n|$)',
            r'Share this.*?(?=\n|$)',
        ]
        
        for pattern in noise_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove excessive newlines again after cleaning
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        return content.strip()
    
    def get_page_info(self, url: str) -> Dict[str, Any]:
        """
        Get basic page information without full content extraction
        Useful for previewing before scraping
        """
        try:
            logger.info(f"🔍 Web Scraper: Getting page info for {url}")
            
            if not self._is_valid_url(url):
                return {
                    "success": False,
                    "error": "Invalid URL format"
                }
            
            # Make a HEAD request first to check if it's accessible
            head_response = self.session.head(url, timeout=10)
            head_response.raise_for_status()
            
            # Make GET request for metadata
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            metadata = self._extract_metadata(soup, url)
            
            # Get content preview (first 500 characters)
            content_preview = self._extract_content(soup)[:500] + "..."
            
            logger.info(f"✅ Web Scraper: Retrieved page info for {metadata.get('title', url)}")
            
            return {
                "success": True,
                "metadata": metadata,
                "content_preview": content_preview,
                "content_type": response.headers.get('content-type', ''),
                "status_code": response.status_code
            }
            
        except Exception as e:
            logger.error(f"❌ Web Scraper: Error getting page info for {url}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Create singleton instance
web_scraper_service = WebScraperService()
