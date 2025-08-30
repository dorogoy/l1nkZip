# Product

## Why this project exists
L1nkZip is a simple, privacy-focused URL shortener API designed to be lightweight, easy to deploy, and low-maintenance. It was created to provide a no-frills URL shortening service that prioritizes simplicity and reliability over complex features.

## Problems it solves
- Provides a straightforward URL shortening service without requiring user accounts or authentication for basic usage
- Offers a cost-effective hosting solution using SQLite with Litestream for database replication and resilience
- Protects users from phishing URLs through optional integration with the PhishTank database
- Supports multiple database backends through Pony ORM while defaulting to the simplest option (SQLite)
- Provides an official CLI client for enhanced command-line interaction

## How it should work
The API should:
1. Accept HTTP POST requests with URLs to shorten
2. Generate short, unique identifiers for each URL using a customizable encoding algorithm
3. Store URL mappings in a database (SQLite preferred, but supports PostgreSQL, MySQL, Oracle, CockroachDB)
4. Redirect HTTP GET requests from short URLs to their original destinations
5. Provide optional phishing protection by checking URLs against the PhishTank database
6. Offer basic administrative endpoints (health check, URL listing) protected by a token

## User experience goals
- **Simplicity**: No user registration required for basic URL shortening
- **Performance**: Fast response times with minimal resource usage
- **Reliability**: Database resilience through Litestream replication to S3
- **Privacy**: No tracking of users beyond basic visit counting
- **Self-hosting**: Easy deployment via Docker with comprehensive documentation
- **Security**: Optional phishing protection and token-based admin access
- **Accessibility**: Official CLI client for diverse usage scenarios
