"""
Unit tests for GrowWiz web scraper module
"""

import pytest
import sys
import os
import json
import tempfile
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from scraper import GrowTipScraper, scrape_grow_forums

class TestGrowTipScraper:
    """Test cases for GrowTipScraper class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.scraper = GrowTipScraper()
        
        # Mock HTML content for testing
        self.mock_forum_html = """
        <html>
            <body>
                <div class="post">
                    <p>Don't overwater your cannabis plants. Check soil moisture first.</p>
                </div>
                <div class="post">
                    <p>Ideal humidity for flowering stage is 40-50%.</p>
                </div>
                <div class="comment">
                    <p>LED lights should be 18-24 inches from canopy.</p>
                </div>
            </body>
        </html>
        """
        
        self.mock_blog_html = """
        <html>
            <body>
                <article>
                    <h1>Growing Tips for Beginners</h1>
                    <p>Temperature should be maintained between 70-85°F during day.</p>
                    <p>Use pH 6.0-7.0 for soil growing.</p>
                </article>
            </body>
        </html>
        """
    
    def teardown_method(self):
        """Clean up after tests"""
        # Close scraper if needed
        if hasattr(self.scraper, 'session') and self.scraper.session:
            asyncio.run(self.scraper.close())
    
    def test_initialization(self):
        """Test scraper initialization"""
        assert self.scraper is not None
        assert hasattr(self.scraper, 'session')
        assert hasattr(self.scraper, 'driver')
        assert hasattr(self.scraper, 'scraped_data')
        assert isinstance(self.scraper.scraped_data, list)
    
    def test_load_config(self):
        """Test configuration loading"""
        config = self.scraper._load_config()
        
        assert isinstance(config, dict)
        assert 'target_sites' in config
        assert 'keywords' in config
        assert 'selectors' in config
        assert 'request_delay' in config
        
        # Check target sites structure
        assert 'forums' in config['target_sites']
        assert 'blogs' in config['target_sites']
        assert isinstance(config['target_sites']['forums'], list)
        assert isinstance(config['target_sites']['blogs'], list)
    
    @pytest.mark.asyncio
    async def test_init_session(self):
        """Test aiohttp session initialization"""
        await self.scraper._init_session()
        
        assert self.scraper.session is not None
        assert hasattr(self.scraper.session, 'get')
        
        # Clean up
        await self.scraper.session.close()
    
    def test_init_driver(self):
        """Test Selenium driver initialization"""
        # Mock webdriver
        with patch('scraper.webdriver.Chrome') as mock_chrome:
            mock_driver = Mock()
            mock_chrome.return_value = mock_driver
            
            self.scraper._init_driver()
            
            assert self.scraper.driver is not None
            mock_chrome.assert_called_once()
    
    def test_clean_text(self):
        """Test text cleaning functionality"""
        dirty_text = "  This is a test\n\n  with extra   spaces\t\tand tabs  "
        clean_text = self.scraper._clean_text(dirty_text)
        
        assert clean_text == "This is a test with extra spaces and tabs"
        
        # Test with None input
        assert self.scraper._clean_text(None) == ""
        
        # Test with empty string
        assert self.scraper._clean_text("") == ""
    
    def test_calculate_relevance(self):
        """Test relevance calculation"""
        # High relevance text
        high_relevance_text = "cannabis growing tips humidity temperature nutrients"
        high_score = self.scraper._calculate_relevance(high_relevance_text)
        
        # Low relevance text
        low_relevance_text = "cooking recipes and travel destinations"
        low_score = self.scraper._calculate_relevance(low_relevance_text)
        
        assert high_score > low_score
        assert 0 <= high_score <= 1
        assert 0 <= low_score <= 1
        
        # Test with empty text
        empty_score = self.scraper._calculate_relevance("")
        assert empty_score == 0
    
    @pytest.mark.asyncio
    async def test_scrape_forums_mock(self):
        """Test forum scraping with mocked HTTP response"""
        # Mock aiohttp response
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=self.mock_forum_html)
        mock_response.status = 200
        
        # Mock session
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        
        self.scraper.session = mock_session
        
        # Test scraping
        results = await self.scraper._scrape_forums(['http://test-forum.com'])
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Check result structure
        for result in results:
            assert 'url' in result
            assert 'content' in result
            assert 'relevance_score' in result
            assert 'timestamp' in result
            assert isinstance(result['relevance_score'], (int, float))
    
    @pytest.mark.asyncio
    async def test_scrape_blogs_mock(self):
        """Test blog scraping with mocked HTTP response"""
        # Mock aiohttp response
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=self.mock_blog_html)
        mock_response.status = 200
        
        # Mock session
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        
        self.scraper.session = mock_session
        
        # Test scraping
        results = await self.scraper._scrape_blogs(['http://test-blog.com'])
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Check result structure
        for result in results:
            assert 'url' in result
            assert 'content' in result
            assert 'relevance_score' in result
            assert 'timestamp' in result
    
    @pytest.mark.asyncio
    async def test_scrape_all_mock(self):
        """Test complete scraping process with mocked responses"""
        # Mock responses
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=self.mock_forum_html)
        mock_response.status = 200
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        
        self.scraper.session = mock_session
        
        # Override config for testing
        self.scraper.config['target_sites'] = {
            'forums': ['http://test-forum.com'],
            'blogs': ['http://test-blog.com']
        }
        
        # Test scraping
        results = await self.scraper.scrape_all()
        
        assert isinstance(results, list)
        assert len(self.scraper.scraped_data) > 0
        
        # Verify data was stored
        for item in self.scraper.scraped_data:
            assert 'url' in item
            assert 'content' in item
            assert 'relevance_score' in item
            assert 'timestamp' in item
    
    def test_save_data(self):
        """Test data saving functionality"""
        # Add test data
        test_data = [
            {
                'url': 'http://test.com',
                'content': 'Test growing tip',
                'relevance_score': 0.8,
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        self.scraper.scraped_data = test_data
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        temp_file.close()
        
        try:
            # Test saving
            self.scraper.save_data(temp_file.name)
            
            # Verify file was created and contains data
            assert os.path.exists(temp_file.name)
            
            with open(temp_file.name, 'r') as f:
                saved_data = json.load(f)
            
            assert isinstance(saved_data, list)
            assert len(saved_data) == 1
            assert saved_data[0]['url'] == 'http://test.com'
            
        finally:
            os.unlink(temp_file.name)
    
    def test_load_data(self):
        """Test data loading functionality"""
        # Create test data file
        test_data = [
            {
                'url': 'http://test.com',
                'content': 'Test growing tip',
                'relevance_score': 0.8,
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(test_data, temp_file)
        temp_file.close()
        
        try:
            # Test loading
            self.scraper.load_data(temp_file.name)
            
            assert len(self.scraper.scraped_data) == 1
            assert self.scraper.scraped_data[0]['url'] == 'http://test.com'
            
        finally:
            os.unlink(temp_file.name)
    
    def test_load_data_nonexistent_file(self):
        """Test loading from nonexistent file"""
        # Should not raise exception
        self.scraper.load_data('nonexistent_file.json')
        
        # Data should remain empty
        assert len(self.scraper.scraped_data) == 0
    
    def test_get_relevant_tips(self):
        """Test getting relevant tips"""
        # Add test data with different relevance scores
        self.scraper.scraped_data = [
            {
                'content': 'High relevance tip about cannabis growing',
                'relevance_score': 0.9,
                'url': 'http://test1.com',
                'timestamp': datetime.now().isoformat()
            },
            {
                'content': 'Medium relevance tip',
                'relevance_score': 0.5,
                'url': 'http://test2.com',
                'timestamp': datetime.now().isoformat()
            },
            {
                'content': 'Low relevance tip',
                'relevance_score': 0.2,
                'url': 'http://test3.com',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        # Test getting top tips
        top_tips = self.scraper.get_relevant_tips(limit=2, min_relevance=0.4)
        
        assert len(top_tips) == 2
        assert top_tips[0]['relevance_score'] >= top_tips[1]['relevance_score']
        assert all(tip['relevance_score'] >= 0.4 for tip in top_tips)
    
    def test_search_tips(self):
        """Test searching tips by query"""
        # Add test data
        self.scraper.scraped_data = [
            {
                'content': 'Cannabis plants need proper humidity levels',
                'relevance_score': 0.8,
                'url': 'http://test1.com',
                'timestamp': datetime.now().isoformat()
            },
            {
                'content': 'Temperature control is important for growth',
                'relevance_score': 0.7,
                'url': 'http://test2.com',
                'timestamp': datetime.now().isoformat()
            },
            {
                'content': 'Watering schedule for vegetables',
                'relevance_score': 0.6,
                'url': 'http://test3.com',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        # Search for humidity-related tips
        humidity_tips = self.scraper.search_tips('humidity')
        
        assert len(humidity_tips) > 0
        assert 'humidity' in humidity_tips[0]['content'].lower()
        
        # Search for non-existent term
        no_results = self.scraper.search_tips('nonexistent_term')
        assert len(no_results) == 0
    
    @pytest.mark.asyncio
    async def test_error_handling_http(self):
        """Test error handling for HTTP requests"""
        # Mock failed response
        mock_response = AsyncMock()
        mock_response.status = 404
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        
        self.scraper.session = mock_session
        
        # Should handle errors gracefully
        results = await self.scraper._scrape_forums(['http://nonexistent-site.com'])
        
        # Should return empty list on error
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality"""
        import time
        
        # Mock quick responses
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=self.mock_forum_html)
        mock_response.status = 200
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        
        self.scraper.session = mock_session
        self.scraper.config['request_delay'] = 0.1  # 100ms delay
        
        # Time multiple requests
        start_time = time.time()
        
        await self.scraper._scrape_forums(['http://test1.com', 'http://test2.com'])
        
        end_time = time.time()
        
        # Should take at least the delay time
        assert (end_time - start_time) >= 0.1
    
    def test_legacy_function(self):
        """Test legacy scrape_grow_forums function"""
        result = scrape_grow_forums()
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Should return sample tips
        for tip in result:
            assert isinstance(tip, str)
            assert len(tip) > 0

class TestScraperIntegration:
    """Integration tests for scraper functionality"""
    
    @pytest.mark.asyncio
    async def test_full_scraping_pipeline(self):
        """Test complete scraping pipeline"""
        scraper = GrowTipScraper()
        
        # Mock the entire pipeline
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value="""
        <html>
            <body>
                <div class="post">
                    <p>Cannabis plants need 18-24 hours of light during vegetative stage.</p>
                </div>
            </body>
        </html>
        """)
        mock_response.status = 200
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        
        scraper.session = mock_session
        
        # Override config for testing
        scraper.config['target_sites'] = {
            'forums': ['http://test-forum.com'],
            'blogs': ['http://test-blog.com']
        }
        
        try:
            # Run complete pipeline
            results = await scraper.scrape_all()
            
            # Verify results
            assert isinstance(results, list)
            assert len(results) > 0
            
            # Check data structure
            for result in results:
                assert 'url' in result
                assert 'content' in result
                assert 'relevance_score' in result
                assert 'timestamp' in result
                assert isinstance(result['relevance_score'], (int, float))
                assert 0 <= result['relevance_score'] <= 1
            
            # Test data persistence
            temp_file = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
            temp_file.close()
            
            try:
                scraper.save_data(temp_file.name)
                
                # Load in new scraper instance
                new_scraper = GrowTipScraper()
                new_scraper.load_data(temp_file.name)
                
                assert len(new_scraper.scraped_data) == len(scraper.scraped_data)
                
            finally:
                os.unlink(temp_file.name)
                
        finally:
            await scraper.close()
    
    @pytest.mark.asyncio
    async def test_concurrent_scraping(self):
        """Test concurrent scraping of multiple sites"""
        scraper = GrowTipScraper()
        
        # Mock responses for multiple sites
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value="<p>Test content</p>")
        mock_response.status = 200
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        
        scraper.session = mock_session
        
        # Test multiple URLs
        urls = [f'http://test{i}.com' for i in range(5)]
        
        try:
            results = await scraper._scrape_forums(urls)
            
            # Should handle multiple URLs
            assert isinstance(results, list)
            
            # Verify all requests were made
            assert mock_session.get.call_count == len(urls)
            
        finally:
            await scraper.close()

if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])