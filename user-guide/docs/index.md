# Getting started

L1nkZip is a simple URL shortener API. It is written in Python and uses the [Fastapi][FastApi] framework and [Pony ORM][PonyORM]. The main features of this project are strong privacy, simplicity and low resource usage to have cheaper hosting as possible. The first option in L1nkZip is always a combination of [sqlite](https://www.sqlite.org) for the database and [litestream][litestream] for its replication and resilience from cheap and volatile environments. Using Pony ORM allows other options if sqlite is not of your taste. This app is mainly focused on running inside a container managed by Kubernetes or docker.

The code of l1nkZip is available at its [Github repository][Github repository] under the [MIT license](https://spdx.org/licenses/MIT.html). You can check all the available endpoints at the [API documentation][Swagger UI].

## Features

* Free URL shortener available at [https://l1nk.zip/docs][Swagger UI].
* Simple to setup, low resource usage and low maintenance for cheap [self-hosting](/l1nkZip/install).
* Using [litestream][litestream], you will have a reliable database almost impossible to destroy, backed on any compatible and unexpensive S3 bucket.
* Although [litestream][litestream] being, in most cases, the best choice, Postgresql is also available. Other databases like MySQL, Oracle or CockroachDB can be used [building your own images](/l1nkZip/install/#requirements).
* Optional protection against phishing using the [PhishTank][PhishTank] database.
* Built-in rate limiting to prevent abuse through mass URL creation and enumeration attacks.
* Optional Redis caching for improved performance on frequently accessed URLs.

## User manual

Being an API, URLs can be posted in many different ways. These examples are using the official API domain, available for general usage by everyone, but you can self-host it and use your own domain. If you are interested on self-hosting, check the [installation](/l1nkZip/install) page.

From the command-line, you have plenty of options, like [curl](https://curl.se), [wget](https://www.gnu.org/software/wget/), [httpie](https://httpie.io) or [httpx](https://www.python-httpx.org) to just name a few. Here is an example with `curl`:

```bash
curl -X 'POST' \
  'https://l1nk.zip/url' \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://www.google.com"}'
```

or a shorter one with `httpx`:

```bash
httpx -m POST -j '{"url": "https://www.google.com"}' https://l1nk.zip/url
```

You can also use non CLI apps, like [Postman](https://www.postman.com) or [Insomnia](https://insomnia.rest). Or even the included [Swagger UI][Swagger UI] that allows you to add a link quickly [from a web form](https://l1nk.zip/docs#/urls/create_url_url_post).


Of course, you can also use your preferred programming language. Here is an example in Python:

```python
import httpx

url = "https://www.google.com"
header = {"Content-Type": "application/json"}
response = httpx.post("https://l1nk.zip/url", header=header, json={"url": url})
print(response.json())
```

or PHP:

```php
<?php
$ch = curl_init("https://l1nk.zip/url");
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode(["url" => "https://www.google.com"]));
curl_setopt($ch, CURLOPT_HTTPHEADER, ["Content-Type: application/json"]);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
$response = curl_exec($ch);
curl_close($ch);
echo $response;
```


It's all about options.

### Official L1nkZip CLI

For a dedicated command-line experience, L1nkZip has an official CLI client available at [l1nkzip-cli](https://github.com/dorogoy/l1nkzip-cli). The CLI provides a modern, rich-powered interface with beautiful output formatting.

#### Installation

```bash
curl -O https://raw.githubusercontent.com/dorogoy/l1nkzip-cli/master/main.py
chmod +x main.py
chmod +x l1nkzip
```

#### Usage Examples

Shorten a URL:
```bash
./main.py shorten https://www.google.com
```

Get information about a short link:
```bash
./main.py info abc123
```

List all URLs (requires API token):
```bash
./main.py list --token YOUR_TOKEN
```

Update PhishTank database (admin only):
```bash
./main.py update-phishtank --token YOUR_TOKEN
```

#### Configuration

- Set API token via `L1NKZIP_TOKEN` environment variable or `--token` flag
- Custom API endpoint via `L1NKZIP_API_URL` environment variable
- Defaults to `https://l1nk.zip` if not specified

The CLI uses [rich](https://github.com/Textualize/rich) for beautiful output and [uv](https://github.com/astral-sh/uv) for dependency management.

## Rate Limiting

L1nkZip includes built-in rate limiting to protect against abuse:

### Default Limits
- **URL Creation**: 10 requests per minute per IP address
- **URL Redirection**: 120 requests per minute per IP address
- **Admin Endpoints**: No rate limiting when using valid authentication token

### Customization
You can customize rate limits using environment variables:

```bash
# Custom rate limits (format: "requests/period")
export RATE_LIMIT_CREATE="20/minute"    # URL creation limit
export RATE_LIMIT_REDIRECT="180/minute"  # URL redirection limit
```

### Rate Limit Headers
When rate limited, responses include informative headers:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in current period
- `X-RateLimit-Reset`: Time when limit resets (UTC timestamp)

## Redis Caching

For improved performance, L1nkZip supports optional Redis caching:

### Configuration
Enable caching by setting the Redis server URL:

```bash
# Enable Redis caching (Optional)
export REDIS_SERVER=redis://localhost:6379/0

# Optional: Custom cache TTL (default: 86400 seconds = 24 hours)
export REDIS_TTL=3600  # 1 hour TTL
```

### How It Works
- **Cache Hits**: Frequently accessed URLs are served from Redis, reducing database load
- **Cache Misses**: URLs not in cache are fetched from database and cached automatically
- **Visit Counting**: Visit statistics are maintained accurately even for cached requests
- **TTL Expiration**: Cached entries automatically expire after configured time

### Benefits
- **Performance**: Faster redirects for popular URLs
- **Scalability**: Reduced database load under high traffic
- **Optional**: Fully disabled when Redis is not configured
- **Configurable**: TTL can be adjusted based on usage patterns

### Self-Hosting Notes
When self-hosting with Redis:
1. Ensure Redis server is running and accessible
2. Set appropriate TTL based on your traffic patterns
3. Monitor cache hit rates for performance optimization

[FastApi]: https://fastapi.tiangolo.com
[PonyORM]: https://ponyorm.org
[PhishTank]: https://phishtank.org
[Swagger UI]: https://l1nk.zip/docs
[litestream]: https://litestream.io
[Github repository]: https://github.com/dorogoy/l1nkZip
[CLI repository]: https://github.com/dorogoy/l1nkzip-cli
