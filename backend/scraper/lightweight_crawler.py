import asyncio
import hashlib
import logging
import re
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from typing import Dict, Any, List, Optional, Set

import aiohttp
from bs4 import BeautifulSoup
from backend.config import config

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0",
    config.crawler.user_agent
]


class LightweightCrawler:
    def __init__(self):
        self.robots_parsers: Dict[str, RobotFileParser] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_times: Dict[str, float] = {}
        self._ua_index = 0

    def _get_next_user_agent(self) -> str:
        ua = USER_AGENTS[self._ua_index % len(USER_AGENTS)]
        self._ua_index += 1
        return ua

    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=config.crawler.timeout_seconds)
            self.session = aiohttp.ClientSession(
                headers={
                    'User-Agent': config.crawler.user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                },
                timeout=timeout
            )
        return self.session

    def can_fetch(self, url: str) -> bool:
        """Check robots.txt rules for the domain"""
        if not getattr(config.crawler, 'respect_robots', True):
            return True

        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            if not domain:
                return False

            if domain not in self.robots_parsers:
                rp = RobotFileParser()
                robots_url = f"{parsed.scheme}://{domain}/robots.txt"
                rp.set_url(robots_url)
                try:
                    rp.read()
                    self.robots_parsers[domain] = rp
                except Exception:
                    # If robots.txt cannot be fetched or read, allow access
                    self.robots_parsers[domain] = None
                    return True

            parser = self.robots_parsers.get(domain)
            if parser is None:
                return True
            return parser.can_fetch(config.crawler.user_agent, url)
        except Exception:
            return True

    async def respect_delay(self, domain: str):
        """Respect per-domain politeness crawl delay"""
        if not domain:
            return
        delay = getattr(config.crawler, 'request_delay', 1.0)
        if domain in self.request_times:
            elapsed = time.time() - self.request_times[domain]
            if elapsed < delay:
                await asyncio.sleep(delay - elapsed)
        self.request_times[domain] = time.time()

    async def fetch_page(self, url: str) -> Dict[str, Any]:
        """
        Fetch webpage HTML asynchronously with status code and headers.
        """
        parsed = urlparse(url)
        domain = parsed.netloc
        
        if not self.can_fetch(url):
            logger.info(f"Skipping {url} (blocked by robots.txt)")
            return {'html': '', 'status_code': 403, 'error': 'Blocked by robots.txt'}

        await self.respect_delay(domain)
        session = await self.get_session()
        
        headers = {'User-Agent': self._get_next_user_agent()}
        try:
            async with session.get(url, headers=headers, allow_redirects=True) as response:
                status = response.status
                if status == 200:
                    html = await response.text(errors='replace')
                    return {'html': html, 'status_code': status, 'url': str(response.url)}
                else:
                    return {'html': '', 'status_code': status, 'error': f"HTTP {status}"}
        except asyncio.TimeoutError:
            return {'html': '', 'status_code': 408, 'error': 'Request timeout'}
        except Exception as e:
            return {'html': '', 'status_code': 500, 'error': str(e)}

    def extract_content(self, html: str, url: str) -> Dict[str, Any]:
        """
        Extract clean text, title, meta description, author, word count,
        and child links from HTML.
        """
        if not html:
            return {
                'url': url,
                'title': '',
                'content': '',
                'meta_description': '',
                'author': '',
                'word_count': 0,
                'content_hash': '',
                'links': []
            }

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else ""
            if not title:
                h1 = soup.find('h1')
                title = h1.get_text().strip() if h1 else url

            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': re.compile(r'description', re.I)}) or \
                        soup.find('meta', attrs={'property': 'og:description'})
            description = meta_desc.get('content', '').strip() if meta_desc else ''

            # Extract author
            meta_author = soup.find('meta', attrs={'name': re.compile(r'author', re.I)}) or \
                          soup.find('meta', attrs={'property': 'article:author'})
            author = meta_author.get('content', '').strip() if meta_author else ''

            IGNORED_EXTENSIONS = (
                '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico',
                '.pdf', '.zip', '.tar', '.gz', '.rar', '.7z',
                '.exe', '.bin', '.dmg', '.iso',
                '.mp3', '.mp4', '.avi', '.mov', '.webm', '.wav',
                '.css', '.js', '.woff', '.woff2', '.ttf', '.eot'
            )

            # Extract outgoing links before decomposing elements
            links = []
            parsed_base = urlparse(url)
            for a in soup.find_all('a', href=True):
                href = a['href'].strip()
                if not href or href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                    continue
                full_url = urljoin(url, href)
                # Keep http / https URLs
                if full_url.startswith(('http://', 'https://')):
                    # Clean fragment
                    full_url = full_url.split('#')[0]
                    parsed_link = urlparse(full_url)
                    path_lower = parsed_link.path.lower()
                    if not path_lower.endswith(IGNORED_EXTENSIONS):
                        links.append(full_url)

            # Deduplicate links preserving order
            seen_links = set()
            unique_links = []
            for link in links:
                if link not in seen_links and link != url:
                    seen_links.add(link)
                    unique_links.append(link)

            # Remove unwanted tags for clean text extraction
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript', 'svg', 'form', 'iframe']):
                tag.decompose()

            # Attempt targeted content selectors
            main_element = (
                soup.find('article') or
                soup.find('main') or
                soup.find('div', class_=re.compile(r'(content|post|article|body)', re.I)) or
                soup.find('body')
            )

            if main_element:
                text = main_element.get_text(separator=' ', strip=True)
            else:
                text = soup.get_text(separator=' ', strip=True)

            # Clean and normalize whitespace
            clean_text = self.clean_text(text)
            
            # Form final content representation
            header_block = f"{title}\n{description}".strip()
            full_content = f"{header_block}\n\n{clean_text}".strip() if clean_text else header_block
            
            words = full_content.split()
            word_count = len(words)
            content_hash = hashlib.sha256(full_content.encode('utf-8')).hexdigest() if full_content else ''

            return {
                'url': url,
                'title': title,
                'content': full_content,
                'meta_description': description,
                'author': author,
                'word_count': word_count,
                'content_hash': content_hash,
                'links': unique_links
            }
        except Exception as e:
            logger.error(f"Error parsing HTML for {url}: {e}")
            return {
                'url': url,
                'title': url,
                'content': '',
                'meta_description': '',
                'author': '',
                'word_count': 0,
                'content_hash': '',
                'links': []
            }

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Collapse multiple whitespaces
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        # Filter very short meaningless fragments
        lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 3]
        return '\n'.join(lines)

    async def fetch_sitemap_urls(self, domain_or_url: str) -> List[str]:
        """
        Attempt to fetch and parse sitemap.xml for a domain.
        """
        parsed = urlparse(domain_or_url)
        scheme = parsed.scheme or "https"
        netloc = parsed.netloc or domain_or_url
        sitemap_url = f"{scheme}://{netloc}/sitemap.xml"
        
        result = await self.fetch_page(sitemap_url)
        if result.get('status_code') != 200 or not result.get('html'):
            return []

        urls = []
        try:
            root = ET.fromstring(result['html'])
            # Support standard sitemap namespace
            for elem in root.iter():
                if elem.tag.endswith('loc') and elem.text:
                    u = elem.text.strip()
                    if u.startswith(('http://', 'https://')):
                        urls.append(u)
        except Exception as e:
            logger.warning(f"Failed to parse XML sitemap for {sitemap_url}: {e}")
            
        return urls[:100]

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
