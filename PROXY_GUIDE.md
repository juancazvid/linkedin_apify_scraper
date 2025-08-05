# LinkedIn Scraper - Complete Proxy Configuration Guide

## 📋 Table of Contents
- [Overview](#overview)
- [Proxy Configuration](#proxy-configuration)
- [Rotation Strategies](#rotation-strategies)
- [Session Management](#session-management)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Overview

The LinkedIn Scraper Actor uses a flexible proxy system that supports:
- Apify Proxy (datacenter and residential)
- Custom proxy servers
- Session persistence
- Multiple rotation strategies
- Automatic failure recovery

## Proxy Configuration

### 1. Apify Proxy (Recommended)

```json
{
    "proxyConfiguration": {
        "useApifyProxy": true,
        "apifyProxyGroups": ["RESIDENTIAL"],
        "apifyProxyCountry": "US"
    }
}
```

**Available Proxy Groups:**
- `RESIDENTIAL` - IP addresses from real devices (most reliable)
- `DATACENTER` - Server IPs (faster but more detectable)

**Country Codes:**
- `US` - United States
- `GB` - United Kingdom
- `DE` - Germany
- `FR` - France
- `CA` - Canada
- etc.

### 2. Custom Proxies

```json
{
    "proxyConfiguration": {
        "useApifyProxy": false,
        "proxyUrls": [
            "http://username:password@proxy1.example.com:8080",
            "http://username:password@proxy2.example.com:8080",
            "socks5://username:password@proxy3.example.com:1080"
        ]
    }
}
```

### 3. No Proxy (Testing Only)

```json
{
    "proxyConfiguration": {
        "useApifyProxy": false
    }
}
```

## Rotation Strategies

### RECOMMENDED (Default)

Best for most use cases. The actor:
- Intelligently rotates proxies
- Reuses successful proxies
- Discards failed proxies
- Balances speed and reliability

```json
{
    "proxyRotation": "RECOMMENDED"
}
```

### PER_REQUEST

Maximum anonymity but slower. The actor:
- Uses a new proxy for every request
- Creates new browser session each time
- Re-authenticates to LinkedIn
- Best for avoiding detection

```json
{
    "proxyRotation": "PER_REQUEST"
}
```

### UNTIL_FAILURE

Fastest but requires good proxies. The actor:
- Keeps the same proxy until it fails
- Only rotates on connection errors
- Maintains browser session
- Good for small batches

```json
{
    "proxyRotation": "UNTIL_FAILURE"
}
```

## Session Management

### What are Session Pools?

Session pools maintain state across actor runs:
- Cookies and authentication
- Proxy assignments
- Rate limit tracking
- Browser fingerprints

### Using Session Pools

```json
{
    "sessionPoolName": "linkedin_main_pool",
    "proxyRotation": "RECOMMENDED"
}
```

### Session Pool Benefits

1. **Faster Processing**
   - Skip re-authentication
   - Reuse working proxies
   - Maintain cookies

2. **Better Rate Limits**
   - Track usage per session
   - Distribute load
   - Avoid blocks

3. **State Persistence**
   - Resume interrupted runs
   - Share between actors
   - Maintain login state

### Session Naming Conventions

```
linkedin_[purpose]_[date]
```

Examples:
- `linkedin_profiles_20250108`
- `linkedin_companies_batch1`
- `linkedin_jobs_daily`

## Examples

### Example 1: Safe High-Volume Scraping

```json
{
    "scrapeType": "person",
    "urls": ["..."],
    "cookie": "...",
    "proxyConfiguration": {
        "useApifyProxy": true,
        "apifyProxyGroups": ["RESIDENTIAL"],
        "apifyProxyCountry": "US"
    },
    "proxyRotation": "PER_REQUEST",
    "sessionPoolName": "linkedin_safe_batch",
    "maxResults": 1000
}
```

### Example 2: Fast Scraping with Sessions

```json
{
    "scrapeType": "company",
    "urls": ["..."],
    "cookie": "...",
    "proxyConfiguration": {
        "useApifyProxy": true,
        "apifyProxyGroups": ["DATACENTER"]
    },
    "proxyRotation": "UNTIL_FAILURE",
    "sessionPoolName": "linkedin_fast_session",
    "maxResults": 50
}
```

### Example 3: Mixed Proxy Strategy

```json
{
    "scrapeType": "job",
    "urls": ["..."],
    "cookie": "...",
    "proxyConfiguration": {
        "useApifyProxy": true,
        "apifyProxyGroups": ["RESIDENTIAL", "DATACENTER"]
    },
    "proxyRotation": "RECOMMENDED",
    "sessionPoolName": "linkedin_mixed_pool",
    "maxResults": 200
}
```

### Example 4: Custom Proxy Rotation

```json
{
    "scrapeType": "person",
    "urls": ["..."],
    "email": "user@example.com",
    "password": "password",
    "proxyConfiguration": {
        "useApifyProxy": false,
        "proxyUrls": [
            "http://proxy1.provider.com:8080",
            "http://proxy2.provider.com:8080",
            "http://proxy3.provider.com:8080"
        ]
    },
    "proxyRotation": "RECOMMENDED",
    "maxResults": 100
}
```

## Troubleshooting

### Common Issues

#### 1. Proxy Connection Failed
```
Error: Failed to create Chrome driver: ERR_PROXY_CONNECTION_FAILED
```
**Solution:**
- Check proxy credentials
- Verify proxy is active
- Try different proxy group
- Check Apify proxy balance

#### 2. Session Expired
```
Error: Session pool authentication failed
```
**Solution:**
- Sessions expire after 24 hours
- Use new session pool name
- Re-authenticate with credentials

#### 3. Rate Limited
```
Error: Too many requests from this IP
```
**Solution:**
- Switch to PER_REQUEST rotation
- Use residential proxies
- Add longer delays
- Reduce concurrent runs

#### 4. Proxy Rotation Not Working
```
Warning: Using same proxy repeatedly
```
**Solution:**
- Check proxy pool size
- Verify rotation strategy
- Ensure multiple proxies available
- Check proxy configuration

### Best Practices by Use Case

#### Lead Generation (100-500 profiles)
```json
{
    "proxyConfiguration": {
        "useApifyProxy": true,
        "apifyProxyGroups": ["RESIDENTIAL"]
    },
    "proxyRotation": "RECOMMENDED",
    "sessionPoolName": "linkedin_leads_[date]"
}
```

#### Market Research (500+ profiles)
```json
{
    "proxyConfiguration": {
        "useApifyProxy": true,
        "apifyProxyGroups": ["RESIDENTIAL"],
        "apifyProxyCountry": "US"
    },
    "proxyRotation": "PER_REQUEST",
    "sessionPoolName": "linkedin_research_[batch]"
}
```

#### Daily Monitoring (< 100 profiles)
```json
{
    "proxyConfiguration": {
        "useApifyProxy": true,
        "apifyProxyGroups": ["DATACENTER"]
    },
    "proxyRotation": "UNTIL_FAILURE",
    "sessionPoolName": "linkedin_daily_monitor"
}
```

#### Testing & Development
```json
{
    "proxyConfiguration": {
        "useApifyProxy": false
    },
    "headless": false
}
```

## Performance Metrics

| Strategy | Speed | Reliability | Detection Risk | Best For |
|----------|-------|-------------|----------------|----------|
| RECOMMENDED | Medium | High | Low | General use |
| PER_REQUEST | Slow | Very High | Very Low | High volume |
| UNTIL_FAILURE | Fast | Medium | Medium | Small batches |

## Proxy Costs (Apify)

| Type | Cost/GB | Speed | Detection Risk |
|------|---------|-------|----------------|
| Datacenter | $0.60 | Fast | Medium |
| Residential | $12.50 | Medium | Very Low |

## Advanced Configuration

### Dynamic Proxy Selection

For advanced users, you can implement dynamic proxy selection based on:
- Time of day
- Target profile type
- Previous success rates
- Geographic requirements

### Monitoring Proxy Health

Track these metrics:
- Success rate per proxy
- Average response time
- Failed connection count
- Rate limit encounters

### Proxy Pool Management

Tips for managing proxy pools:
1. Rotate pools daily/weekly
2. Keep separate pools for different tasks
3. Monitor pool performance
4. Clean failed sessions regularly

---

**Remember:** Always use proxies in production to avoid IP blocks and ensure reliable scraping!
