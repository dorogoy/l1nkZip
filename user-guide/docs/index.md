# L1nkZip

L1nkZip is a simple URL shortener API. It is written in Python and uses the [Fastapi](https://fastapi.tiangolo.com/) framework and [Pony ORM](https://ponyorm.org/). The main priority of this project is to be simple and low in resource usage. The first option in L1nkZip is always a combination of [sqlite](https://www.sqlite.org) for the database and [litestream](https://litestream.io) for its replication and resilience from cheap and volatile environments. Using Pony ORM allows to use any other database if sqlite is not of your taste. This app is mainly focused on running inside a container managed by Kubernetes or docker.

## Features

* Simple to setup and use. It just works.
* Low resource usage and also low maintenance.
* If you choose the [litestream](https://litestream.io) way, it is very cheap to host. You will have a reliable database almost impossible to destroy, backed on any compatible S3 bucket.
* Do you want to use Postgresql? No problem. Just change the configuration and you are ready to go.
* Optional protection against phisphing with the [PhishTank](https://phishtank.org) database.

## Usage examples

Being an API, links can be posted in many creative ways. These examples are using the official API domain, available for general usage, but you can selfhost it and use your own domain if you want. If you are interested in selfhosting, check the [installation](/install) page.

From the command-line, you have plenty of options, like [curl](https://curl.se), [wget](https://www.gnu.org/software/wget/), [httpie](https://httpie.io) or [httpx](https://www.python-httpx.org) to just name a few. Here is an example with `curl`:

```bash
curl -X 'POST' \
  'https://l1nk.zip/url' \
  -H 'accept: application/json' \
  -d '{"url": "https://www.google.com"}'
```

of a shorter one with `httpx`:

```bash
httpx -m POST -j '{"url": "https://www.google.com"}' https://l1nk.zip/url
```

You can also use non CLI apps, like [Postman](https://www.postman.com) or [Insomnia](https://insomnia.rest). Or even the included [Swagger UI](https://l1nk.zip/docs).

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

You can check all the available endpoints in the [API documentation](https://l1nk.zip/docs).
