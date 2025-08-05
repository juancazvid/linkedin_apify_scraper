#!/usr/bin/env python3
"""
Local testing script for LinkedIn Scraper Actor
Run this script to test the actor locally before deploying to Apify
"""

import asyncio
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Mock Apify Actor for local testing
class MockActor:
    @staticmethod
    def log():
        import logging
        return logging.getLogger(__name__)
    
    @staticmethod
    async def get_input():
        """Return test input for local testing"""
        return {
            "scrapeType": "person",  # Change to test different types
            "urls": [
                "https://www.linkedin.com/in/example-profile-1",
                # Add more URLs for testing
            ],
            # Use either email/password or cookie
            "email": os.getenv("LINKEDIN_EMAIL"),
            "password": os.getenv("LINKEDIN_PASSWORD"),
            # "cookie": os.getenv("LINKEDIN_COOKIE"),
            "useProxy": False,  # Disable proxy for local testing
            "headless": False,  # Show browser for debugging
            "getContacts": False,
            "getEmployees": False,
            "maxResults": 2
        }
    
    @staticmethod
    async def push_data(data):
        """Mock data push - just print to console"""
        print(f"Data pushed: {json.dumps(data, indent=2)}")
    
    @staticmethod
    async def set_value(key, value):
        """Mock key-value store"""
        print(f"Key-Value stored: {key} = {json.dumps(value, indent=2)}")
    
    @staticmethod
    def create_proxy_configuration():
        """Mock proxy configuration"""
        return None


async def test_scraper():
    """Test the LinkedIn scraper locally"""
    import sys
    import logging
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Mock the Actor module
    sys.modules['apify'] = type('module', (), {'Actor': MockActor})
    
    # Import after mocking
    from src.main import LinkedInScraperActor
    
    # Create scraper instance
    scraper = LinkedInScraperActor()
    
    # Get test input
    test_input = await MockActor.get_input()
    
    print("=" * 60)
    print("LinkedIn Scraper Actor - Local Test")
    print("=" * 60)
    print(f"Test Input: {json.dumps(test_input, indent=2)}")
    print("=" * 60)
    
    # Run the scraper
    try:
        results = await scraper.run(test_input)
        
        print("=" * 60)
        print(f"Test completed successfully!")
        print(f"Total results: {len(results)}")
        print("=" * 60)
        
        # Print results
        for i, result in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(json.dumps(result, indent=2))
            
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()


def test_specific_function():
    """Test specific functions of the scraper"""
    from src.main import LinkedInScraperActor
    
    scraper = LinkedInScraperActor()
    
    # Test driver setup
    print("Testing driver setup...")
    driver = scraper.setup_driver(use_proxy=False, headless=False)
    
    # Test login
    print("Testing LinkedIn login...")
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    
    if scraper.login_to_linkedin(driver, email, password):
        print("Login successful!")
        
        # Test person scraping
        test_url = "https://www.linkedin.com/in/example-profile"
        print(f"Testing person scraping: {test_url}")
        result = scraper.scrape_person(test_url)
        print(f"Result: {json.dumps(result, indent=2)}")
    else:
        print("Login failed!")
    
    # Clean up
    driver.quit()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test LinkedIn Scraper Actor locally")
    parser.add_argument(
        "--mode",
        choices=["full", "function"],
        default="full",
        help="Test mode: full actor run or specific function test"
    )
    
    args = parser.parse_args()
    
    if args.mode == "full":
        # Run full actor test
        asyncio.run(test_scraper())
    else:
        # Test specific functions
        test_specific_function()
