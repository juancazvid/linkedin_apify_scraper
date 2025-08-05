# Use the Apify Python image with Chrome pre-installed
FROM apify/actor-python-selenium:latest

# Install Chrome dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the LinkedIn scraper library
COPY linkedin_scraper ./linkedin_scraper

# Copy source code
COPY . ./

# Run the actor using the src module
CMD python3 -m src
