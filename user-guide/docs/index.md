# Getting started

L1nkZip is a simple URL shortener API. It is written in Python and uses the [Fastapi][FastApi] framework and [Pony ORM][PonyORM]. The main priorities of this project are strong privacy, simplicity and low resource usage to have cheaper hosting as possible. The first option in L1nkZip is always a combination of [sqlite](https://www.sqlite.org) for the database and [litestream][litestream] for its replication and resilience from cheap and volatile environments. Using Pony ORM allows other options if sqlite is not of your taste. This app is mainly focused on running inside a container managed by Kubernetes or docker.

The code of l1nkZip is available on its [Github repository][Github repository] under the [MIT license](https://spdx.org/licenses/MIT.html). You can check all the available endpoints at the [API documentation][Swagger UI].

## Features

* Free installation for casual usage, available to use right now to everyone at [https://l1nk.zip/docs][Swagger UI].
* Simple to setup, low resource usage and low maintenance for cheap [self-hosting](/l1nkZip/install).
* Using [litestream][litestream], you will have a reliable database almost impossible to destroy, backed on any compatible and unexpensive S3 bucket.
* Although [litestream][litestream] being, in most cases, the best choice, Postgresql is also available. Other databases like MySQL, Oracle or CockroachDB can be used [building your own images](/l1nkZip/install/#requirements).
* Optional protection against phisphing using the [PhishTank][PhishTank] database.

## User manual

Being an API, links can be posted in many different ways. These examples are using the official API domain, available for general usage by everyone, but you can self-host it and use your own domain. If you are interested on self-hosting, check the [installation](/l1nkZip/install) page.

From the command-line, you have plenty of options, like [curl](https://curl.se), [wget](https://www.gnu.org/software/wget/), [httpie](https://httpie.io) or [httpx](https://www.python-httpx.org) to just name a few. Here is an example with `curl`:

```bash
curl -X 'POST' \
  'https://l1nk.zip/url' \
  -H 'accept: application/json' \
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

[FastApi]: https://fastapi.tiangolo.com
[PonyORM]: https://ponyorm.org
[PhishTank]: https://phishtank.org
[Swagger UI]: https://l1nk.zip/docs
[litestream]: https://litestream.io
[Github repository]: https://github.com/dorogoy/l1nkZip
