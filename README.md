# LinkedIn Scraper Actor

> **Professional LinkedIn data extraction tool** – Scrape profiles, companies, jobs, and perform job searches with advanced anti-detection features.

## ✨ Features

* 🧑 **Person Profiles** - Extract complete profile data including experience, education, skills
* 🏢 **Company Pages** - Scrape company information, employees, and statistics  
* 💼 **Job Postings** - Extract job details, requirements, and application info
* 🔍 **Job Search** - Search and scrape multiple job listings
* 🔐 **Flexible Authentication** - Login with email/password or cookie
* 🛡️ **Anti-Detection** - Built-in proxy support and browser fingerprinting
* 📊 **Structured Data** - Clean, normalized JSON output

## 🚀 Quick Start

### Project Setup

All configuration files go in the **root directory** of your project:
- `docker-compose.yml` - Development environment (root level)
- `Dockerfile` - Container configuration (root level)
- `actor.json` - Actor metadata (root level)
- `input_schema.json` - Input validation (root level)
- All other config files at root level

### Authentication Options

#### Option 1: Email & Password
```json
{
    "scrapeType": "person",
    "urls": ["https://www.linkedin.com/in/example"],
    "email": "your-email@example.com",
    "password": "your-password"
}
```

#### Option 2: Cookie Authentication (Recommended)
1. Login to LinkedIn in your browser
2. Open Developer Tools (F12)
3. Go to Application → Cookies
4. Find and copy the `li_at` cookie value
5. Use it in the actor:

```json
{
    "scrapeType": "person",
    "urls": ["https://www.linkedin.com/in/example"],
    "cookie": "YOUR_LI_AT_COOKIE_VALUE"
}
```

## 📥 Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scrapeType` | string | ✅ | Type of content to scrape: `person`, `company`, `job`, `job_search` |
| `urls` | array | ✅* | LinkedIn URLs to scrape (not needed for job_search) |
| `email` | string | ⚠️ | LinkedIn email (required if no cookie) |
| `password` | string | ⚠️ | LinkedIn password (required if no cookie) |
| `cookie` | string | ⚠️ | LinkedIn li_at cookie (alternative to email/password) |
| `proxyConfiguration` | object | ❌ | Proxy settings (default: Apify proxy enabled) |
| `proxyRotation` | string | ❌ | Proxy rotation strategy: `RECOMMENDED`, `PER_REQUEST`, `UNTIL_FAILURE` |
| `sessionPoolName` | string | ❌ | Session pool name for sharing sessions across runs |
| `headless` | boolean | ❌ | Run in headless mode (default: true) |
| `getContacts` | boolean | ❌ | Scrape person's connections (person only) |
| `getEmployees` | boolean | ❌ | Scrape company employees (company only) |
| `jobSearchTerm` | string | ⚠️ | Search term (required for job_search) |
| `maxResults` | integer | ❌ | Maximum results to scrape (default: 100) |

### 🔧 Proxy Configuration

The actor supports advanced proxy configuration for reliable scraping:

#### **Proxy Configuration Object**
```json
{
    "useApifyProxy": true,
    "apifyProxyGroups": ["RESIDENTIAL"],
    "apifyProxyCountry": "US"
}
```

Or use custom proxies:
```json
{
    "useApifyProxy": false,
    "proxyUrls": [
        "http://proxy1.example.com:8080",
        "http://proxy2.example.com:8080"
    ]
}
```

#### **Proxy Rotation Strategies**

- **`RECOMMENDED`** (default): Smart rotation based on proxy health
- **`PER_REQUEST`**: New proxy for each request (safest but slower)
- **`UNTIL_FAILURE`**: Keep proxy until it fails (fastest but riskier)

#### **Session Pools**

Session pools maintain state across actor runs:
```json
{
    "sessionPoolName": "linkedin_session_pool_1",
    "proxyRotation": "RECOMMENDED"
}
```

Benefits:
- Reuse authenticated sessions
- Maintain cookies across runs
- Reduce login frequency
- Better rate limit management

## 📤 Output Format

### Person Profile Output
```json
{
    "type": "person",
    "url": "https://www.linkedin.com/in/example",
    "name": "John Doe",
    "location": "San Francisco, CA",
    "about": "Software engineer passionate about...",
    "company": "Tech Company",
    "job_title": "Senior Software Engineer",
    "open_to_work": false,
    "experiences": [
        {
            "position_title": "Senior Software Engineer",
            "company": "Tech Company",
            "location": "San Francisco, CA",
            "from_date": "Jan 2020",
            "to_date": "Present",
            "duration": "4 years",
            "description": "Leading development of..."
        }
    ],
    "educations": [
        {
            "institution": "University Name",
            "degree": "Bachelor of Science - Computer Science",
            "from_date": "2012",
            "to_date": "2016",
            "description": "Dean's List..."
        }
    ],
    "scraped_at": "2025-01-01T12:00:00.000Z"
}
```

### Company Profile Output
```json
{
    "type": "company",
    "url": "https://www.linkedin.com/company/example",
    "name": "Example Corp",
    "about": "Leading provider of...",
    "website": "https://example.com",
    "phone": "+1-555-0100",
    "headquarters": "San Francisco, CA",
    "founded": "2010",
    "industry": "Technology",
    "company_type": "Public Company",
    "company_size": "1,001-5,000 employees",
    "specialties": "Software, AI, Cloud",
    "headcount": 3500,
    "employees": [],  // If getEmployees: true
    "scraped_at": "2025-01-01T12:00:00.000Z"
}
```

### Job Posting Output
```json
{
    "type": "job",
    "url": "https://www.linkedin.com/jobs/view/123456",
    "job_title": "Software Engineer",
    "company": "Tech Company",
    "company_linkedin_url": "https://www.linkedin.com/company/tech",
    "location": "San Francisco, CA",
    "posted_date": "2 days ago",
    "applicant_count": "150 applicants",
    "job_description": "We are looking for...",
    "benefits": "Health insurance, 401k...",
    "scraped_at": "2025-01-01T12:00:00.000Z"
}
```

## 🎯 Use Cases

### 1. Scrape Multiple Profiles
```json
{
    "scrapeType": "person",
    "urls": [
        "https://www.linkedin.com/in/profile1",
        "https://www.linkedin.com/in/profile2",
        "https://www.linkedin.com/in/profile3"
    ],
    "cookie": "YOUR_COOKIE",
    "maxResults": 50
}
```

### 2. Company Research with Employees
```json
{
    "scrapeType": "company",
    "urls": ["https://www.linkedin.com/company/microsoft"],
    "cookie": "YOUR_COOKIE",
    "getEmployees": true,
    "maxResults": 100
}
```

### 3. Job Market Research
```json
{
    "scrapeType": "job_search",
    "jobSearchTerm": "Machine Learning Engineer San Francisco",
    "cookie": "YOUR_COOKIE",
    "maxResults": 200
}
```

### 4. Lead Generation with Contacts
```json
{
    "scrapeType": "person",
    "urls": ["https://www.linkedin.com/in/target-profile"],
    "cookie": "YOUR_COOKIE",
    "getContacts": true
}
```

## 🛡️ How the Proxy System Works

The LinkedIn Scraper Actor includes a sophisticated proxy management system designed for reliable, undetected scraping:

### **Proxy Configuration Options**

1. **Apify Proxy** (Recommended)
   - Automatic proxy rotation
   - Residential and datacenter options
   - Geographic targeting
   - Session management

2. **Custom Proxies**
   - Support for your own proxy servers
   - HTTP/HTTPS proxy support
   - Authentication support

3. **No Proxy**
   - For local testing only
   - Not recommended for production

### **Rotation Strategies**

#### **RECOMMENDED** (Default)
- Smart rotation based on proxy health
- Reuses working proxies
- Automatically discards failed proxies
- Best balance of speed and reliability

#### **PER_REQUEST**
- New proxy for every request
- Maximum anonymity
- Slower but safest
- Recreates browser session each time

#### **UNTIL_FAILURE**
- Keeps same proxy until it fails
- Fastest option
- Good for small batches
- Automatic failover on errors

### **Session Pools**

Session pools maintain authenticated state across actor runs:

```json
{
    "sessionPoolName": "linkedin_pool_2025",
    "proxyRotation": "RECOMMENDED"
}
```

**Benefits:**
- Cookies persist across runs
- Reduces login frequency
- Better rate limit management
- Shared state between actors

**How it works:**
1. First run creates and saves session
2. Subsequent runs reuse the session
3. Sessions expire after 24 hours of inactivity
4. Automatic session refresh on expiry

### **Proxy Failure Handling**

The actor automatically handles proxy failures:

1. **Detection**: Monitors for connection errors
2. **Retry**: Attempts with exponential backoff
3. **Rotation**: Switches proxy after max failures
4. **Recovery**: Re-authenticates if needed

### **Best Practices**

1. **For Testing**: Use no proxy or datacenter proxies
2. **For Production**: Always use residential proxies
3. **For High Volume**: Use PER_REQUEST rotation
4. **For Speed**: Use UNTIL_FAILURE with session pools
5. **For Reliability**: Use RECOMMENDED with residential proxies

## 🛡️ Anti-Detection Tips

1. **Use Cookies Instead of Login**: Reduces detection risk
2. **Enable Proxy**: Always use `useProxy: true` for production
3. **Limit Concurrent Runs**: Don't run multiple instances simultaneously
4. **Respect Rate Limits**: Add delays between large batches
5. **Rotate Accounts**: Use different LinkedIn accounts for large-scale scraping
6. **Keep Sessions Short**: Limit to 100-200 profiles per session

## ⚠️ Important Notes

### Legal Compliance
- Respect LinkedIn's Terms of Service
- Only scrape publicly available information
- Don't use scraped data for spamming or harassment
- Comply with GDPR and data protection laws

### Rate Limiting
- LinkedIn may temporarily restrict accounts that scrape too aggressively
- Recommended: Max 100 profiles per hour
- Use delays between requests for safety

### Data Freshness
- Profile data may be cached by LinkedIn
- Some information requires being logged in to view
- Connection/contact scraping requires 1st-degree connections

## 🔧 Troubleshooting

### Authentication Failed
- Verify email/password are correct
- Check if cookie has expired (cookies typically last 1 year)
- Try logging in manually first to handle any security checks

### No Data Returned
- Ensure URLs are valid LinkedIn URLs
- Check if profile/page is public or requires connection
- Verify authentication is working

### Rate Limited
- Reduce scraping speed
- Use longer delays between requests
- Try different proxy locations
- Switch to a different LinkedIn account

### Missing Data Fields
- Some fields only visible to connections
- Company employee counts require login
- Job applicant counts may be hidden

## 🚦 Best Practices

1. **Start Small**: Test with 5-10 URLs first
2. **Monitor Performance**: Check logs for errors
3. **Handle Failures**: Implement retry logic for failed URLs
4. **Export Regularly**: Download data incrementally
5. **Validate Output**: Check data completeness
6. **Respect Privacy**: Don't scrape private/sensitive information

## 📊 Performance

- **Average Speed**: 5-10 seconds per profile
- **Memory Usage**: ~500MB per browser instance
- **Success Rate**: 95%+ with proper configuration
- **Proxy Recommended**: Yes, for production use

## 🤝 Support

For issues or questions:
1. Check the actor logs for detailed error messages
2. Verify your authentication is working
3. Test with a single URL first
4. Review the anti-detection tips above

## 📝 Changelog

### Version 1.0.0
- Initial release
- Support for person, company, job scraping
- Job search functionality
- Cookie and email/password authentication
- Proxy support
- Anti-detection measures

---

**Ready to extract LinkedIn data?** Configure your authentication and start scraping! 🚀
