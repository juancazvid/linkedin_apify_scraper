import asyncio
import json
import os
import random
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import traceback

from apify import Actor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Import the LinkedIn scraper components
from linkedin_scraper import Person, Company, Job, JobSearch, actions


class LinkedInScraperActor:
    """Apify Actor for scraping LinkedIn profiles, companies, and jobs."""
    
    def __init__(self):
        self.driver = None
        self.scraped_at = datetime.now().isoformat()
        self.request_count = 0
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        self.proxy_config = None
        self.proxy_rotation = "RECOMMENDED"
        self.session_pool_name = None
        self.current_proxy_url = None
        self.proxy_failure_count = 0
        self.max_proxy_failures = 5
    
    async def setup_proxy_configuration(self, proxy_config: Dict[str, Any]) -> Optional[Any]:
        """Setup proxy configuration based on input."""
        if not proxy_config:
            return None
            
        try:
            # Check if using Apify proxy
            if proxy_config.get("useApifyProxy"):
                # Create Apify proxy configuration
                config_options = {
                    "groups": proxy_config.get("apifyProxyGroups", ["RESIDENTIAL"]),
                    "country_code": proxy_config.get("apifyProxyCountry", "US")
                }
                
                return Actor.create_proxy_configuration(**config_options)
                
            # Check for custom proxy URLs
            elif proxy_config.get("proxyUrls"):
                # Return custom proxy configuration
                return {
                    "type": "custom",
                    "urls": proxy_config.get("proxyUrls")
                }
                
            return None
            
        except Exception as e:
            Actor.log.error(f"Failed to setup proxy configuration: {e}")
            return None
    
    async def get_proxy_url(self) -> Optional[str]:
        """Get a proxy URL based on rotation strategy."""
        if not self.proxy_config:
            return None
            
        try:
            # Handle Apify proxy
            if hasattr(self.proxy_config, 'new_url'):
                # Check rotation strategy
                if self.proxy_rotation == "PER_REQUEST":
                    # Always get a new proxy for each request
                    if self.session_pool_name:
                        session_id = f"{self.session_pool_name}_{self.request_count}"
                        return await self.proxy_config.new_url(session_id)
                    else:
                        return await self.proxy_config.new_url()
                        
                elif self.proxy_rotation == "UNTIL_FAILURE":
                    # Keep using the same proxy until it fails
                    if not self.current_proxy_url or self.proxy_failure_count >= self.max_proxy_failures:
                        self.proxy_failure_count = 0
                        if self.session_pool_name:
                            session_id = f"{self.session_pool_name}_persistent"
                            self.current_proxy_url = await self.proxy_config.new_url(session_id)
                        else:
                            self.current_proxy_url = await self.proxy_config.new_url()
                    return self.current_proxy_url
                    
                else:  # RECOMMENDED
                    # Use session pool if available, otherwise rotate smartly
                    if self.session_pool_name:
                        session_id = f"{self.session_pool_name}_{self.request_count % 10}"
                        return await self.proxy_config.new_url(session_id)
                    else:
                        return await self.proxy_config.new_url()
                        
            # Handle custom proxy
            elif isinstance(self.proxy_config, dict) and self.proxy_config.get("type") == "custom":
                urls = self.proxy_config.get("urls", [])
                if urls:
                    if self.proxy_rotation == "PER_REQUEST":
                        return random.choice(urls)
                    elif self.proxy_rotation == "UNTIL_FAILURE":
                        if not self.current_proxy_url:
                            self.current_proxy_url = random.choice(urls)
                        return self.current_proxy_url
                    else:  # RECOMMENDED
                        # Round-robin through custom proxies
                        index = self.request_count % len(urls)
                        return urls[index]
                        
        except Exception as e:
            Actor.log.error(f"Failed to get proxy URL: {e}")
            
        return None
        
    async def setup_driver(self, headless: bool = True) -> webdriver.Chrome:
        """Set up Chrome driver with proxy if configured."""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
        # Additional options to avoid detection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Randomize user agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
        
        # Add more anti-detection options
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--start-maximized')
        
        # Set up proxy if configured
        proxy_url = await self.get_proxy_url()
        if proxy_url:
            chrome_options.add_argument(f'--proxy-server={proxy_url}')
            Actor.log.info(f"Using proxy: {proxy_url[:50]}...")  # Log partial URL for security
        
        # Use Apify's Chrome binary if available
        try:
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            Actor.log.error(f"Failed to create Chrome driver: {e}")
            # If proxy failed, increment failure count
            if proxy_url and self.proxy_rotation == "UNTIL_FAILURE":
                self.proxy_failure_count += 1
                Actor.log.warning(f"Proxy failure count: {self.proxy_failure_count}/{self.max_proxy_failures}")
            raise
            
        # Execute script to mask automation
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                })
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                })
                window.chrome = {
                    runtime: {}
                }
                Object.defineProperty(navigator, 'permissions', {
                    get: () => ({
                        query: () => Promise.resolve({ state: 'granted' })
                    })
                })
            '''
        })
        
        return driver
    
    def login_to_linkedin(self, driver: webdriver.Chrome, email: str, password: str, cookie: Optional[str] = None) -> bool:
        """Login to LinkedIn using credentials or cookie."""
        try:
            if cookie:
                Actor.log.info("Logging in with cookie...")
                actions.login(driver, cookie=cookie)
            else:
                Actor.log.info("Logging in with email/password...")
                actions.login(driver, email=email, password=password)
            
            # Add a small delay after login
            time.sleep(2)
            
            Actor.log.info("Successfully logged into LinkedIn")
            return True
            
        except Exception as e:
            Actor.log.error(f"Failed to login to LinkedIn: {e}")
            return False
    
    def add_rate_limit_delay(self, min_delay: float = 2.0, max_delay: float = 5.0):
        """Add random delay for rate limiting."""
        delay = random.uniform(min_delay, max_delay)
        Actor.log.debug(f"Rate limiting: waiting {delay:.2f} seconds")
        time.sleep(delay)
        self.request_count += 1
        
        # Add longer delay every 10 requests
        if self.request_count % 10 == 0:
            long_delay = random.uniform(10, 20)
            Actor.log.info(f"Taking a longer break: {long_delay:.2f} seconds")
            time.sleep(long_delay)
    
    def retry_on_failure(self, func, *args, **kwargs):
        """Retry a function on failure with exponential backoff."""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    Actor.log.error(f"Failed after {self.max_retries} attempts: {e}")
                    raise
                
                wait_time = self.retry_delay * (2 ** attempt)
                Actor.log.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time} seconds: {e}")
                time.sleep(wait_time)
    
    def scrape_person(self, url: str, get_contacts: bool = False) -> Dict[str, Any]:
        """Scrape a LinkedIn person profile."""
        try:
            Actor.log.info(f"Scraping person profile: {url}")
            
            # Add rate limiting
            self.add_rate_limit_delay()
            
            person = Person(
                linkedin_url=url,
                driver=self.driver,
                scrape=True,
                close_on_complete=False
            )
            
            result = {
                "type": "person",
                "url": url,
                "name": person.name,
                "location": getattr(person, 'location', None),
                "about": person.about,
                "open_to_work": getattr(person, 'open_to_work', False),
                "company": person.company,
                "job_title": person.job_title,
                "experiences": [],
                "educations": [],
                "interests": [],
                "accomplishments": [],
                "scraped_at": self.scraped_at
            }
            
            # Convert experiences to dict
            for exp in person.experiences:
                result["experiences"].append({
                    "position_title": exp.position_title,
                    "company": exp.institution_name,
                    "location": exp.location,
                    "from_date": exp.from_date,
                    "to_date": exp.to_date,
                    "duration": exp.duration,
                    "description": exp.description,
                    "linkedin_url": exp.linkedin_url
                })
            
            # Convert educations to dict
            for edu in person.educations:
                result["educations"].append({
                    "institution": edu.institution_name,
                    "degree": edu.degree,
                    "from_date": edu.from_date,
                    "to_date": edu.to_date,
                    "description": edu.description,
                    "linkedin_url": edu.linkedin_url
                })
            
            # Add contacts if requested
            if get_contacts and person.contacts:
                result["contacts"] = []
                for contact in person.contacts:
                    result["contacts"].append({
                        "name": contact.name,
                        "occupation": contact.occupation,
                        "url": contact.url
                    })
            
            Actor.log.info(f"Successfully scraped person: {person.name}")
            return result
            
        except Exception as e:
            Actor.log.error(f"Error scraping person {url}: {e}")
            return {"error": str(e), "url": url, "type": "person"}
    
    def scrape_company(self, url: str, get_employees: bool = False) -> Dict[str, Any]:
        """Scrape a LinkedIn company profile."""
        try:
            Actor.log.info(f"Scraping company profile: {url}")
            
            # Add rate limiting
            self.add_rate_limit_delay()
            
            company = Company(
                linkedin_url=url,
                driver=self.driver,
                scrape=True,
                get_employees=get_employees,
                close_on_complete=False
            )
            
            result = {
                "type": "company",
                "url": url,
                "name": company.name,
                "about": company.about_us,
                "website": company.website,
                "phone": company.phone,
                "headquarters": company.headquarters,
                "founded": company.founded,
                "industry": company.industry,
                "company_type": company.company_type,
                "company_size": company.company_size,
                "specialties": company.specialties,
                "headcount": company.headcount,
                "scraped_at": self.scraped_at
            }
            
            # Add showcase pages
            if company.showcase_pages:
                result["showcase_pages"] = [
                    {
                        "name": page.name,
                        "url": page.linkedin_url,
                        "followers": page.followers
                    }
                    for page in company.showcase_pages
                ]
            
            # Add employees if requested
            if get_employees and company.employees:
                result["employees"] = company.employees
            
            Actor.log.info(f"Successfully scraped company: {company.name}")
            return result
            
        except Exception as e:
            Actor.log.error(f"Error scraping company {url}: {e}")
            return {"error": str(e), "url": url, "type": "company"}
    
    def scrape_job(self, url: str) -> Dict[str, Any]:
        """Scrape a LinkedIn job posting."""
        try:
            Actor.log.info(f"Scraping job posting: {url}")
            
            # Add rate limiting
            self.add_rate_limit_delay()
            
            job = Job(
                linkedin_url=url,
                driver=self.driver,
                scrape=True,
                close_on_complete=False
            )
            
            result = job.to_dict()
            result["type"] = "job"
            result["scraped_at"] = self.scraped_at
            
            Actor.log.info(f"Successfully scraped job: {job.job_title}")
            return result
            
        except Exception as e:
            Actor.log.error(f"Error scraping job {url}: {e}")
            return {"error": str(e), "url": url, "type": "job"}
    
    def search_jobs(self, search_term: str, scrape_recommended: bool = True) -> List[Dict[str, Any]]:
        """Search for jobs on LinkedIn."""
        try:
            Actor.log.info(f"Searching for jobs: {search_term}")
            
            job_search = JobSearch(
                driver=self.driver,
                scrape=scrape_recommended,
                close_on_complete=False
            )
            
            results = []
            
            # Get search results
            if search_term:
                job_listings = job_search.search(search_term)
                for job in job_listings:
                    results.append({
                        "type": "job_search_result",
                        "job_title": job.job_title,
                        "company": job.company,
                        "location": job.location,
                        "url": job.linkedin_url,
                        "scraped_at": self.scraped_at
                    })
            
            # Add recommended jobs if requested
            if scrape_recommended:
                if hasattr(job_search, 'recommended_jobs'):
                    for job in job_search.recommended_jobs:
                        results.append({
                            "type": "recommended_job",
                            "job_title": job.job_title,
                            "company": job.company,
                            "location": job.location,
                            "url": job.linkedin_url,
                            "scraped_at": self.scraped_at
                        })
            
            Actor.log.info(f"Found {len(results)} jobs")
            return results
            
        except Exception as e:
            Actor.log.error(f"Error searching jobs: {e}")
            return [{"error": str(e), "search_term": search_term, "type": "job_search"}]
    
    async def run(self, actor_input: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Main run method for the actor."""
        results = []
        
        try:
            # Extract input parameters
            scrape_type = actor_input.get("scrapeType", "person")
            urls = actor_input.get("urls", [])
            email = actor_input.get("email")
            password = actor_input.get("password")
            cookie = actor_input.get("cookie")
            
            # Proxy configuration
            proxy_configuration = actor_input.get("proxyConfiguration", {"useApifyProxy": True})
            self.proxy_rotation = actor_input.get("proxyRotation", "RECOMMENDED")
            self.session_pool_name = actor_input.get("sessionPoolName")
            
            headless = actor_input.get("headless", True)
            get_contacts = actor_input.get("getContacts", False)
            get_employees = actor_input.get("getEmployees", False)
            job_search_term = actor_input.get("jobSearchTerm")
            max_results = actor_input.get("maxResults", 100)
            
            # Validate input
            if not cookie and not (email and password):
                Actor.log.error("Either cookie or email/password must be provided for authentication")
                await Actor.set_value("ERROR", {"error": "Authentication credentials missing"})
                return results
            
            # Setup proxy configuration
            Actor.log.info("Setting up proxy configuration...")
            self.proxy_config = await self.setup_proxy_configuration(proxy_configuration)
            
            # Setup driver
            Actor.log.info("Setting up Chrome driver...")
            self.driver = await self.setup_driver(headless=headless)
            
            # Login to LinkedIn
            if not self.login_to_linkedin(self.driver, email, password, cookie):
                await Actor.set_value("ERROR", {"error": "Login failed"})
                return results
            
            # Save session info if using session pool
            if self.session_pool_name:
                session_info = {
                    "session_pool": self.session_pool_name,
                    "login_time": datetime.now().isoformat(),
                    "status": "active"
                }
                await Actor.set_value(f"SESSION_{self.session_pool_name}", session_info)
            
            # Save progress periodically
            progress = {
                "total": min(len(urls), max_results) if urls else max_results,
                "completed": 0,
                "failed": 0,
                "scrape_type": scrape_type,
                "proxy_rotation": self.proxy_rotation,
                "session_pool": self.session_pool_name
            }
            await Actor.set_value("PROGRESS", progress)
            
            # Process based on scrape type
            if scrape_type == "person":
                for i, url in enumerate(urls[:max_results]):
                    Actor.log.info(f"Processing person {i+1}/{min(len(urls), max_results)}: {url}")
                    try:
                        # For PER_REQUEST rotation, recreate driver
                        if self.proxy_rotation == "PER_REQUEST" and i > 0:
                            self.driver.quit()
                            self.driver = await self.setup_driver(headless=headless)
                            # Re-login if needed
                            if not self.login_to_linkedin(self.driver, email, password, cookie):
                                Actor.log.error(f"Failed to re-login for URL {url}")
                                progress["failed"] += 1
                                continue
                        
                        result = self.retry_on_failure(self.scrape_person, url, get_contacts)
                        results.append(result)
                        await Actor.push_data(result)
                        progress["completed"] += 1
                        
                    except Exception as e:
                        Actor.log.error(f"Failed to scrape {url}: {e}")
                        progress["failed"] += 1
                        results.append({"error": str(e), "url": url, "type": "person"})
                        
                        # If using UNTIL_FAILURE, check if we need to rotate proxy
                        if self.proxy_rotation == "UNTIL_FAILURE":
                            self.proxy_failure_count += 1
                            if self.proxy_failure_count >= self.max_proxy_failures:
                                Actor.log.info("Max proxy failures reached, rotating proxy...")
                                self.current_proxy_url = None
                                self.driver.quit()
                                self.driver = await self.setup_driver(headless=headless)
                                if not self.login_to_linkedin(self.driver, email, password, cookie):
                                    Actor.log.error("Failed to re-login after proxy rotation")
                                    break
                    
                    # Update progress
                    await Actor.set_value("PROGRESS", progress)
                    
            elif scrape_type == "company":
                for i, url in enumerate(urls[:max_results]):
                    Actor.log.info(f"Processing company {i+1}/{min(len(urls), max_results)}: {url}")
                    try:
                        # For PER_REQUEST rotation, recreate driver
                        if self.proxy_rotation == "PER_REQUEST" and i > 0:
                            self.driver.quit()
                            self.driver = await self.setup_driver(headless=headless)
                            if not self.login_to_linkedin(self.driver, email, password, cookie):
                                Actor.log.error(f"Failed to re-login for URL {url}")
                                progress["failed"] += 1
                                continue
                        
                        result = self.retry_on_failure(self.scrape_company, url, get_employees)
                        results.append(result)
                        await Actor.push_data(result)
                        progress["completed"] += 1
                        
                    except Exception as e:
                        Actor.log.error(f"Failed to scrape {url}: {e}")
                        progress["failed"] += 1
                        results.append({"error": str(e), "url": url, "type": "company"})
                    
                    # Update progress
                    await Actor.set_value("PROGRESS", progress)
                    
            elif scrape_type == "job":
                for i, url in enumerate(urls[:max_results]):
                    Actor.log.info(f"Processing job {i+1}/{min(len(urls), max_results)}: {url}")
                    try:
                        # For PER_REQUEST rotation, recreate driver
                        if self.proxy_rotation == "PER_REQUEST" and i > 0:
                            self.driver.quit()
                            self.driver = await self.setup_driver(headless=headless)
                            if not self.login_to_linkedin(self.driver, email, password, cookie):
                                Actor.log.error(f"Failed to re-login for URL {url}")
                                progress["failed"] += 1
                                continue
                        
                        result = self.retry_on_failure(self.scrape_job, url)
                        results.append(result)
                        await Actor.push_data(result)
                        progress["completed"] += 1
                        
                    except Exception as e:
                        Actor.log.error(f"Failed to scrape {url}: {e}")
                        progress["failed"] += 1
                        results.append({"error": str(e), "url": url, "type": "job"})
                    
                    # Update progress
                    await Actor.set_value("PROGRESS", progress)
                    
            elif scrape_type == "job_search":
                job_results = self.search_jobs(job_search_term, scrape_recommended=True)
                for i, result in enumerate(job_results[:max_results]):
                    results.append(result)
                    await Actor.push_data(result)
                    progress["completed"] += 1
                    
                    if (i + 1) % 10 == 0:
                        await Actor.set_value("PROGRESS", progress)
            
            # Final progress update
            progress["status"] = "completed"
            await Actor.set_value("PROGRESS", progress)
            
            # Save session state if using session pool
            if self.session_pool_name:
                session_info = {
                    "session_pool": self.session_pool_name,
                    "completion_time": datetime.now().isoformat(),
                    "status": "completed",
                    "stats": {
                        "completed": progress["completed"],
                        "failed": progress["failed"]
                    }
                }
                await Actor.set_value(f"SESSION_{self.session_pool_name}_FINAL", session_info)
            
            Actor.log.info(f"Successfully scraped {len(results)} items ({progress['failed']} failed)")
            
        except Exception as e:
            Actor.log.error(f"Fatal error in actor run: {e}")
            Actor.log.error(traceback.format_exc())
            await Actor.set_value("ERROR", {"error": str(e), "traceback": traceback.format_exc()})
            
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
        
        return results


async def main():
    """Main entry point for the Apify Actor."""
    async with Actor:
        actor_input = await Actor.get_input() or {}
        
        Actor.log.info("LinkedIn Scraper Actor started")
        Actor.log.info(f"Input: {json.dumps(actor_input, indent=2)}")
        
        scraper = LinkedInScraperActor()
        results = await scraper.run(actor_input)
        
        Actor.log.info(f"LinkedIn Scraper Actor finished. Scraped {len(results)} items")


if __name__ == "__main__":
    asyncio.run(main())
