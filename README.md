# l1nkZip

L1nkZip is a simple URL shortener API. It is written in Python and uses the [Fastapi](https://fastapi.tiangolo.com/) framework and [Pony ORM](https://ponyorm.org/). The main priority of this project is to be simple and low in resource usage. The first option in L1nkZip is always a combination of [sqlite](https://www.sqlite.org) for the database and [litestream](https://litestream.io) for its replication and resilience from cheap and volatile environments. Using Pony ORM allows to use any other database if sqlite is not of your taste. This app is mainly focused on running inside a container managed by Kubernetes or docker.

The working API is available at https://l1nk.zip/docs

The full documentation is available at https://dorogoy.github.io/l1nkzip.

## Features

* Simple to setup and use. It just works.
* Low resource usage and also low maintenance.
* If you choose the [litestream](https://litestream.io) way, it is very cheap to host. You will have a reliable database almost impossible to destroy, backed on any compatible S3 bucket.
* Do you want to use Postgresql? No problem. Just change the configuration and you are ready to go.
* Optional protection against phisphing with the [PhishTank](https://phishtank.org) database.
