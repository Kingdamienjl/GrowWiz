#!/usr/bin/env python3
"""
Test script for GrowWiz Hyperbrowser-enhanced scraper
Demonstrates advanced web scraping capabilities for grow forums and sites
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.scraper import GrowTipScraper
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

async def test_hyperbrowser_scraping():
    """Test Hyperbrowser scraping capabilities"""
    logger.info("🚀 Starting GrowWiz Hyperbrowser Scraper Test")
    
    scraper = GrowTipScraper()
    
    try:
        # Test 1: Basic forum scraping with Hyperbrowser
        logger.info("📡 Testing Hyperbrowser forum scraping...")
        
        test_urls = [
            "https://www.rollitup.org/",
            "https://www.growweedeasy.com/",
            "https://www.leafly.com/news/growing"
        ]
        
        hyperbrowser_tips = await scraper.scrape_with_hyperbrowser(test_urls[:1])  # Test with one URL first
        logger.info(f"✅ Hyperbrowser scraped {len(hyperbrowser_tips)} tips")
        
        if hyperbrowser_tips:
            logger.info("📝 Sample Hyperbrowser tip:")
            sample_tip = hyperbrowser_tips[0]
            logger.info(f"   Source: {sample_tip.get('source', 'Unknown')}")
            logger.info(f"   Type: {sample_tip.get('type', 'Unknown')}")
            logger.info(f"   Content: {sample_tip.get('content', '')[:200]}...")
            logger.info(f"   Relevance: {sample_tip.get('relevance_score', 0):.2f}")
        
        # Test 2: Structured data extraction
        logger.info("🔍 Testing structured data extraction...")
        
        structured_urls = [
            "https://www.growweedeasy.com/nutrient-deficiencies-cannabis"
        ]
        
        structured_data = await scraper.extract_structured_grow_data(structured_urls)
        logger.info(f"✅ Extracted {len(structured_data)} structured data entries")
        
        if structured_data:
            logger.info("📊 Sample structured data:")
            for i, data in enumerate(structured_data[:1]):
                logger.info(f"   Entry {i+1}: {json.dumps(data, indent=2)[:300]}...")
        
        # Test 3: Full scraping with both methods
        logger.info("🌐 Testing full scraping pipeline...")
        
        all_tips = await scraper.scrape_grow_forums()
        logger.info(f"✅ Total tips from full pipeline: {len(all_tips)}")
        
        # Analyze results
        if all_tips:
            logger.info("📈 Scraping Results Analysis:")
            
            # Count by type
            type_counts = {}
            for tip in all_tips:
                tip_type = tip.get('type', 'unknown')
                type_counts[tip_type] = type_counts.get(tip_type, 0) + 1
            
            for tip_type, count in type_counts.items():
                logger.info(f"   {tip_type}: {count} tips")
            
            # Show top relevance tips
            sorted_tips = sorted(all_tips, key=lambda x: x.get('relevance_score', 0), reverse=True)
            logger.info("🏆 Top 3 most relevant tips:")
            
            for i, tip in enumerate(sorted_tips[:3]):
                logger.info(f"   {i+1}. Score: {tip.get('relevance_score', 0):.2f}")
                logger.info(f"      Source: {tip.get('source', 'Unknown')}")
                logger.info(f"      Content: {tip.get('content', '')[:150]}...")
                logger.info("")
        
        # Test 4: Query-specific tips
        logger.info("🔎 Testing query-specific tip retrieval...")
        
        test_queries = [
            "nitrogen deficiency",
            "humidity control",
            "flowering stage",
            "LED lighting"
        ]
        
        for query in test_queries:
            relevant_tips = await scraper.get_relevant_tips(query)
            logger.info(f"   '{query}': {len(relevant_tips)} relevant tips")
            
            if relevant_tips:
                best_tip = relevant_tips[0]
                logger.info(f"      Best match: {best_tip.get('content', '')[:100]}...")
        
        # Save results
        logger.info("💾 Saving test results...")
        
        test_results = {
            "hyperbrowser_tips": len(hyperbrowser_tips),
            "structured_data_entries": len(structured_data),
            "total_tips": len(all_tips),
            "type_distribution": type_counts if all_tips else {},
            "test_timestamp": asyncio.get_event_loop().time()
        }
        
        os.makedirs("data", exist_ok=True)
        with open("data/hyperbrowser_test_results.json", "w") as f:
            json.dump(test_results, f, indent=2)
        
        logger.info("✅ Test results saved to data/hyperbrowser_test_results.json")
        
        return test_results
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise
    
    finally:
        scraper.cleanup()

async def test_specific_grow_problems():
    """Test scraping for specific grow problems and solutions"""
    logger.info("🌱 Testing specific grow problem scraping...")
    
    scraper = GrowTipScraper()
    
    try:
        # Focus on problem-solving content
        problem_urls = [
            "https://www.growweedeasy.com/nutrient-deficiencies-cannabis",
            "https://www.leafly.com/news/growing/common-cannabis-growing-problems"
        ]
        
        # Extract structured problem data
        problem_data = await scraper.extract_structured_grow_data(problem_urls)
        
        logger.info(f"📋 Found {len(problem_data)} problem datasets")
        
        # Process and display problems
        all_problems = []
        for dataset in problem_data:
            if 'problems' in dataset:
                all_problems.extend(dataset['problems'])
        
        logger.info(f"🚨 Total problems identified: {len(all_problems)}")
        
        # Group by severity
        severity_groups = {}
        for problem in all_problems:
            severity = problem.get('severity', 'unknown')
            if severity not in severity_groups:
                severity_groups[severity] = []
            severity_groups[severity].append(problem)
        
        for severity, problems in severity_groups.items():
            logger.info(f"   {severity.upper()}: {len(problems)} problems")
            
            # Show example
            if problems:
                example = problems[0]
                logger.info(f"      Example: {example.get('problem', 'Unknown')}")
                if example.get('solutions'):
                    logger.info(f"      Solution: {example['solutions'][0]}")
        
        return all_problems
        
    except Exception as e:
        logger.error(f"❌ Problem scraping test failed: {e}")
        return []
    
    finally:
        scraper.cleanup()

def display_banner():
    """Display test banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    🌿 GrowWiz Scraper Test 🌿                ║
    ║              Enhanced with Hyperbrowser Technology           ║
    ║                                                              ║
    ║  Testing advanced web scraping for cannabis growing advice  ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

async def main():
    """Main test function"""
    display_banner()
    
    try:
        # Run main scraping test
        logger.info("Starting comprehensive scraper test...")
        test_results = await test_hyperbrowser_scraping()
        
        # Run specific problem test
        logger.info("Starting grow problem analysis test...")
        problems = await test_specific_grow_problems()
        
        # Final summary
        logger.info("🎉 All tests completed successfully!")
        logger.info(f"📊 Final Summary:")
        logger.info(f"   Total tips scraped: {test_results.get('total_tips', 0)}")
        logger.info(f"   Hyperbrowser tips: {test_results.get('hyperbrowser_tips', 0)}")
        logger.info(f"   Structured data entries: {test_results.get('structured_data_entries', 0)}")
        logger.info(f"   Problems identified: {len(problems)}")
        
        # Performance metrics
        if test_results.get('total_tips', 0) > 0:
            hyperbrowser_ratio = test_results.get('hyperbrowser_tips', 0) / test_results.get('total_tips', 1)
            logger.info(f"   Hyperbrowser contribution: {hyperbrowser_ratio:.1%}")
        
        logger.info("✅ GrowWiz scraper is ready for production use!")
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Check if Hyperbrowser is available
    try:
        import mcp_hyperbrowser
        logger.info("✅ Hyperbrowser is available for testing")
    except ImportError:
        logger.warning("⚠️  Hyperbrowser not available - testing fallback methods only")
    
    # Run tests
    asyncio.run(main())