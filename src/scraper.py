#!/usr/bin/env python3
"""
GrowWiz Web Scraper
Scrapes grow forums, blogs, and YouTube for cultivation advice
"""

import asyncio
import aiohttp
import json
import os
import re
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from loguru import logger

# Hyperbrowser integration for advanced scraping
try:
    from mcp_hyperbrowser import scrape_webpage, crawl_webpages, extract_structured_data
    HYPERBROWSER_AVAILABLE = True
    logger.info("Hyperbrowser integration available")
except ImportError:
    HYPERBROWSER_AVAILABLE = False
    logger.warning("Hyperbrowser not available - falling back to traditional scraping")

class GrowTipScraper:
    """Web scraper for cannabis and plant growing advice"""
    
    def __init__(self):
        self.session = None
        self.driver = None
        self.scraped_data = []
        self.max_pages = int(os.getenv("MAX_SCRAPE_PAGES", 50))
        self.user_agent = os.getenv("USER_AGENT", "GrowWiz/1.0")
        
        # Target websites for scraping
        self.target_sites = {
            "forums": [
                "https://www.rollitup.org/",
                "https://www.thcfarmer.com/",
                "https://www.grasscity.com/forum/",
                "https://www.420magazine.com/community/",
                "https://www.icmag.com/forum/"
            ],
            "blogs": [
                "https://www.leafly.com/news/growing/",
                "https://www.royalqueenseeds.com/blog/",
                "https://www.growweedeasy.com/",
                "https://www.ilovegrowingmarijuana.com/guides/",
                "https://www.dutch-passion.com/en/blog/"
            ]
        }
        
        # Backward compatibility attributes
        self.forum_urls = self.target_sites["forums"]
        self.blog_urls = self.target_sites["blogs"]
        
        # Keywords to focus scraping on
        self.keywords = [
            "nitrogen deficiency", "phosphorus deficiency", "potassium deficiency",
            "overwatering", "underwatering", "light burn", "nutrient burn",
            "pH problems", "humidity control", "temperature control",
            "flowering stage", "vegetative stage", "seedling care",
            "harvest time", "trichomes", "pest control", "mold prevention"
        ]
        
        logger.info("GrowTipScraper initialized")
    
    async def setup_session(self):
        """Setup aiohttp session for web requests (alias for initialize_session)"""
        await self.initialize_session()
    
    async def initialize_session(self):
        """Initialize aiohttp session for web requests"""
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=3)
        timeout = aiohttp.ClientTimeout(total=30)
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            connector=connector,
            timeout=timeout
        )
        
        logger.info("HTTP session initialized")
    
    def setup_selenium_driver(self):
        """Setup Selenium WebDriver for JavaScript-heavy sites"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"--user-agent={self.user_agent}")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Selenium WebDriver initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Selenium: {e}")
            self.driver = None
    
    async def scrape_with_hyperbrowser(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Use Hyperbrowser for advanced scraping of modern sites"""
        if not HYPERBROWSER_AVAILABLE:
            logger.warning("Hyperbrowser not available, falling back to traditional scraping")
            return []
        
        tips = []
        
        try:
            # Use Hyperbrowser to scrape multiple URLs
            for url in urls:
                logger.info(f"Scraping {url} with Hyperbrowser")
                
                # Scrape webpage content
                result = await scrape_webpage(
                    url=url,
                    outputFormat=["markdown", "html"],
                    sessionOptions={
                        "useStealth": True,
                        "acceptCookies": True,
                        "solveCaptchas": False
                    }
                )
                
                if result and 'markdown' in result:
                    content = result['markdown']
                    
                    # Extract growing tips from markdown content
                    extracted_tips = self.extract_tips_from_content(content, url, "hyperbrowser")
                    tips.extend(extracted_tips)
                    
                    # Rate limiting
                    await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Error with Hyperbrowser scraping: {e}")
        
        return tips
    
    async def crawl_grow_sites_hyperbrowser(self, base_urls: List[str]) -> List[Dict[str, Any]]:
        """Use Hyperbrowser to crawl entire grow sites"""
        if not HYPERBROWSER_AVAILABLE:
            return []
        
        tips = []
        
        for base_url in base_urls:
            try:
                logger.info(f"Crawling {base_url} with Hyperbrowser")
                
                # Crawl the website
                result = await crawl_webpages(
                    url=base_url,
                    outputFormat=["markdown"],
                    followLinks=True,
                    maxPages=20,
                    sessionOptions={
                        "useStealth": True,
                        "acceptCookies": True
                    }
                )
                
                if result and isinstance(result, list):
                    for page_result in result:
                        if 'markdown' in page_result:
                            content = page_result['markdown']
                            page_url = page_result.get('url', base_url)
                            
                            extracted_tips = self.extract_tips_from_content(content, page_url, "hyperbrowser_crawl")
                            tips.extend(extracted_tips)
                
            except Exception as e:
                logger.error(f"Error crawling {base_url} with Hyperbrowser: {e}")
        
        return tips
    
    async def extract_structured_grow_data(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Extract structured growing data using Hyperbrowser"""
        if not HYPERBROWSER_AVAILABLE:
            return []
        
        # Define schema for structured extraction
        schema = {
            "type": "object",
            "properties": {
                "grow_tips": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "tip": {"type": "string"},
                            "category": {"type": "string"},
                            "strain": {"type": "string"},
                            "growth_stage": {"type": "string"},
                            "problem_type": {"type": "string"}
                        }
                    }
                },
                "problems": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "problem": {"type": "string"},
                            "symptoms": {"type": "array", "items": {"type": "string"}},
                            "solutions": {"type": "array", "items": {"type": "string"}},
                            "severity": {"type": "string"}
                        }
                    }
                }
            }
        }
        
        structured_data = []
        
        try:
            result = await extract_structured_data(
                urls=urls,
                prompt="Extract cannabis growing tips, plant problems, and solutions from this content. Focus on practical advice for indoor cultivation.",
                schema=schema
            )
            
            if result:
                structured_data.extend(result)
                
        except Exception as e:
            logger.error(f"Error extracting structured data: {e}")
        
        return structured_data
    
    def extract_tips_from_content(self, content: str, source_url: str, scrape_type: str) -> List[Dict[str, Any]]:
        """Extract growing tips from scraped content"""
        tips = []
        
        # Split content into paragraphs
        paragraphs = content.split('\n\n')
        
        for para in paragraphs:
            para = para.strip()
            
            if len(para) > 50 and self.is_relevant_content(para):
                tip = {
                    "source": source_url,
                    "type": scrape_type,
                    "content": self.clean_text(para),
                    "keywords": self.extract_keywords(para),
                    "timestamp": time.time(),
                    "relevance_score": self.calculate_relevance(para)
                }
                tips.append(tip)
        
    async def scrape_grow_forums(self) -> List[Dict[str, Any]]:
        """Main scraping function - enhanced with Hyperbrowser support"""
        if not self.session:
            await self.setup_session()
        
        all_tips = []
        
        # Try Hyperbrowser first for better results
        if HYPERBROWSER_AVAILABLE:
            logger.info("Using Hyperbrowser for enhanced scraping")
            
            # Modern grow forums that require JavaScript
            modern_forums = [
                "https://www.rollitup.org/",
                "https://www.thcfarmer.com/",
                "https://www.autoflower.net/",
                "https://www.icmag.com/",
                "https://www.420magazine.com/"
            ]
            
            # Use Hyperbrowser for modern sites
            hyperbrowser_tips = await self.scrape_with_hyperbrowser(modern_forums)
            all_tips.extend(hyperbrowser_tips)
            
            # Crawl specific grow sites
            crawl_sites = [
                "https://www.leafly.com/news/growing",
                "https://www.growweedeasy.com/",
                "https://www.ilovegrowingmarijuana.com/"
            ]
            
            crawled_tips = await self.crawl_grow_sites_hyperbrowser(crawl_sites)
            all_tips.extend(crawled_tips)
            
            # Extract structured data from key resources
            structured_urls = [
                "https://www.growweedeasy.com/nutrient-deficiencies-cannabis",
                "https://www.leafly.com/news/growing/common-cannabis-growing-problems",
                "https://www.ilovegrowingmarijuana.com/marijuana-plant-problems/"
            ]
            
            structured_data = await self.extract_structured_grow_data(structured_urls)
            
            # Convert structured data to tips format
            for data in structured_data:
                if 'grow_tips' in data:
                    for tip_data in data['grow_tips']:
                        tip = {
                            "source": "structured_extraction",
                            "type": "structured_data",
                            "content": tip_data.get('tip', ''),
                            "category": tip_data.get('category', ''),
                            "strain": tip_data.get('strain', ''),
                            "growth_stage": tip_data.get('growth_stage', ''),
                            "keywords": [tip_data.get('category', ''), tip_data.get('growth_stage', '')],
                            "timestamp": time.time(),
                            "relevance_score": 0.8
                        }
                        all_tips.append(tip)
                
                if 'problems' in data:
                    for problem_data in data['problems']:
                        tip = {
                            "source": "structured_extraction",
                            "type": "problem_solution",
                            "content": f"Problem: {problem_data.get('problem', '')}. Solutions: {', '.join(problem_data.get('solutions', []))}",
                            "problem_type": problem_data.get('problem', ''),
                            "symptoms": problem_data.get('symptoms', []),
                            "solutions": problem_data.get('solutions', []),
                            "severity": problem_data.get('severity', ''),
                            "keywords": ["problem", "solution", problem_data.get('problem', '')],
                            "timestamp": time.time(),
                            "relevance_score": 0.9
                        }
                        all_tips.append(tip)
        
        # Fallback to traditional scraping
        logger.info("Running traditional scraping as backup")
        traditional_tips = await self.scrape_traditional_forums()
        all_tips.extend(traditional_tips)
        
        # Remove duplicates and sort by relevance
        unique_tips = self.deduplicate_tips(all_tips)
        unique_tips.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Store scraped data
        self.scraped_data.extend(unique_tips)
        await self.save_scraped_data()
        
        logger.info(f"Total scraped tips: {len(unique_tips)}")
        return unique_tips
    
    async def scrape_traditional_forums(self) -> List[Dict[str, Any]]:
        """Traditional scraping method as fallback"""
        if not self.session:
            await self.setup_session()
        
        all_tips = []
        
        # Scrape forums with traditional methods
        for forum_url in self.forum_urls:
            try:
                logger.info(f"Scraping forum: {forum_url}")
                forum_tips = await self.scrape_forum(forum_url)
                all_tips.extend(forum_tips)
                
                # Rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error scraping forum {forum_url}: {e}")
        
        # Scrape blogs
        for blog_url in self.blog_urls:
            try:
                logger.info(f"Scraping blog: {blog_url}")
                blog_tips = await self.scrape_blog(blog_url)
                all_tips.extend(blog_tips)
                
                # Rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error scraping blog {blog_url}: {e}")
        
        return all_tips
    
    def deduplicate_tips(self, tips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate tips based on content similarity"""
        unique_tips = []
        seen_content = set()
        
        for tip in tips:
            content = tip.get('content', '').lower().strip()
            
            # Create a simplified version for comparison
            simplified = re.sub(r'[^\w\s]', '', content)
            simplified = ' '.join(simplified.split())
            
            # Check if we've seen similar content
            is_duplicate = False
            for seen in seen_content:
                # Simple similarity check
                if len(simplified) > 0 and len(seen) > 0:
                    similarity = len(set(simplified.split()) & set(seen.split())) / len(set(simplified.split()) | set(seen.split()))
                    if similarity > 0.8:  # 80% similarity threshold
                        is_duplicate = True
                        break
            
            if not is_duplicate and len(simplified) > 20:  # Minimum content length
                unique_tips.append(tip)
                seen_content.add(simplified)
        
        return unique_tips
    
    async def scrape_forum(self, forum_url: str) -> List[Dict[str, Any]]:
        """Scrape a specific forum for growing tips"""
        tips = []
        
        try:
            async with self.session.get(forum_url) as response:
                if response.status != 200:
                    logger.warning(f"HTTP {response.status} for {forum_url}")
                    return tips
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find forum threads/posts
                post_selectors = [
                    '.post-content', '.message-content', '.thread-content',
                    '.post-body', '.message-body', '.content'
                ]
                
                posts = []
                for selector in post_selectors:
                    found_posts = soup.select(selector)
                    if found_posts:
                        posts = found_posts
                        break
                
                # Extract tips from posts
                for post in posts[:20]:  # Limit to first 20 posts
                    text = post.get_text(strip=True)
                    
                    if self.is_relevant_content(text):
                        tip = {
                            "source": forum_url,
                            "type": "forum_post",
                            "content": self.clean_text(text),
                            "keywords": self.extract_keywords(text),
                            "timestamp": time.time(),
                            "relevance_score": self.calculate_relevance(text)
                        }
                        tips.append(tip)
                
        except Exception as e:
            logger.error(f"Error scraping forum {forum_url}: {e}")
        
        return tips
    
    async def scrape_blog(self, blog_url: str) -> List[Dict[str, Any]]:
        """Scrape a specific blog for growing articles"""
        tips = []
        
        try:
            async with self.session.get(blog_url) as response:
                if response.status != 200:
                    logger.warning(f"HTTP {response.status} for {blog_url}")
                    return tips
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find article links
                article_links = []
                link_selectors = ['a[href*="grow"]', 'a[href*="cannabis"]', 'a[href*="plant"]']
                
                for selector in link_selectors:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get('href')
                        if href:
                            full_url = urljoin(blog_url, href)
                            if self.is_relevant_url(full_url):
                                article_links.append(full_url)
                
                # Scrape individual articles
                for article_url in article_links[:10]:  # Limit to 10 articles
                    try:
                        article_tips = await self.scrape_article(article_url)
                        tips.extend(article_tips)
                        await asyncio.sleep(1)  # Rate limiting
                        
                    except Exception as e:
                        logger.error(f"Error scraping article {article_url}: {e}")
                
        except Exception as e:
            logger.error(f"Error scraping blog {blog_url}: {e}")
        
        return tips
    
    async def scrape_article(self, article_url: str) -> List[Dict[str, Any]]:
        """Scrape an individual article for growing tips"""
        tips = []
        
        try:
            async with self.session.get(article_url) as response:
                if response.status != 200:
                    return tips
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract article content
                content_selectors = [
                    '.article-content', '.post-content', '.entry-content',
                    '.content', 'article', '.main-content'
                ]
                
                content = None
                for selector in content_selectors:
                    found_content = soup.select_one(selector)
                    if found_content:
                        content = found_content
                        break
                
                if content:
                    # Extract paragraphs with growing tips
                    paragraphs = content.find_all('p')
                    
                    for para in paragraphs:
                        text = para.get_text(strip=True)
                        
                        if len(text) > 50 and self.is_relevant_content(text):
                            tip = {
                                "source": article_url,
                                "type": "blog_article",
                                "content": self.clean_text(text),
                                "keywords": self.extract_keywords(text),
                                "timestamp": time.time(),
                                "relevance_score": self.calculate_relevance(text)
                            }
                            tips.append(tip)
                
        except Exception as e:
            logger.error(f"Error scraping article {article_url}: {e}")
        
        return tips
    
    def is_relevant_content(self, text: str) -> bool:
        """Check if content is relevant to plant growing"""
        text_lower = text.lower()
        
        # Check for growing-related keywords
        relevant_terms = [
            'grow', 'plant', 'cannabis', 'marijuana', 'leaf', 'leaves',
            'nutrient', 'water', 'light', 'humidity', 'temperature',
            'flowering', 'vegetative', 'harvest', 'deficiency', 'burn',
            'ph', 'soil', 'hydro', 'seed', 'clone'
        ]
        
        keyword_count = sum(1 for term in relevant_terms if term in text_lower)
        
        # Must have at least 2 relevant terms and be substantial content
        return keyword_count >= 2 and len(text) > 100
    
    def is_relevant_url(self, url: str) -> bool:
        """Check if URL is likely to contain relevant growing content"""
        url_lower = url.lower()
        relevant_patterns = [
            'grow', 'cannabis', 'marijuana', 'plant', 'cultivation',
            'nutrient', 'deficiency', 'problem', 'guide', 'tip'
        ]
        
        return any(pattern in url_lower for pattern in relevant_patterns)
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text"""
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def calculate_relevance(self, text: str) -> float:
        """Calculate relevance score for content"""
        text_lower = text.lower()
        score = 0.0
        
        # Keyword matching
        keyword_matches = len(self.extract_keywords(text))
        score += keyword_matches * 0.2
        
        # Length bonus (longer content often more valuable)
        if len(text) > 200:
            score += 0.1
        if len(text) > 500:
            score += 0.1
        
        # Specific problem indicators
        problem_indicators = ['deficiency', 'problem', 'issue', 'burn', 'stress']
        for indicator in problem_indicators:
            if indicator in text_lower:
                score += 0.15
        
        return min(score, 1.0)  # Cap at 1.0
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?()-]', '', text)
        
        # Limit length
        if len(text) > 1000:
            text = text[:1000] + "..."
        
        return text.strip()
    
    async def get_relevant_tips(self, query: str) -> List[Dict[str, Any]]:
        """Get tips relevant to a specific query"""
        if not self.scraped_data:
            await self.load_scraped_data()
        
        query_lower = query.lower()
        relevant_tips = []
        
        for tip in self.scraped_data:
            content_lower = tip['content'].lower()
            
            # Simple relevance matching
            if any(word in content_lower for word in query_lower.split()):
                tip_copy = tip.copy()
                tip_copy['query_relevance'] = self.calculate_query_relevance(query, tip['content'])
                relevant_tips.append(tip_copy)
        
        # Sort by relevance and return top results
        relevant_tips.sort(key=lambda x: x.get('query_relevance', 0), reverse=True)
        return relevant_tips[:10]
    
    def calculate_query_relevance(self, query: str, content: str) -> float:
        """Calculate how relevant content is to a specific query"""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        # Jaccard similarity
        intersection = len(query_words.intersection(content_words))
        union = len(query_words.union(content_words))
        
        return intersection / union if union > 0 else 0.0
    
    async def save_scraped_data(self):
        """Save scraped data to file"""
        try:
            os.makedirs("data", exist_ok=True)
            
            with open("data/scraped_tips.json", "w") as f:
                json.dump(self.scraped_data, f, indent=2)
            
            logger.info(f"Saved {len(self.scraped_data)} scraped tips to file")
            
        except Exception as e:
            logger.error(f"Error saving scraped data: {e}")
    
    async def load_scraped_data(self):
        """Load previously scraped data from file"""
        try:
            if os.path.exists("data/scraped_tips.json"):
                with open("data/scraped_tips.json", "r") as f:
                    self.scraped_data = json.load(f)
                
                logger.info(f"Loaded {len(self.scraped_data)} scraped tips from file")
            
        except Exception as e:
            logger.error(f"Error loading scraped data: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()

# Legacy function for compatibility with your notes
def scrape_grow_forums():
    """Legacy function matching your notes"""
    return ["Don't overwater seedlings", "Ideal humidity for flowering: 40-50%"]

# Example usage
if __name__ == "__main__":
    async def main():
        scraper = GrowTipScraper()
        
        try:
            # Test scraping
            tips = await scraper.scrape_grow_forums()
            print(f"Scraped {len(tips)} tips")
            
            # Test query
            if tips:
                relevant = await scraper.get_relevant_tips("nitrogen deficiency")
                print(f"Found {len(relevant)} relevant tips for 'nitrogen deficiency'")
                
                for tip in relevant[:3]:
                    print(f"- {tip['content'][:100]}...")
            
        finally:
            scraper.cleanup()
    
    # Run the example
    asyncio.run(main())