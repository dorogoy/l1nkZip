# Installation

L1nkZip is distributed as a Docker image, although the full code can be found on the [Github repository][Github repository] in case you want to use it directly or contribute. It can be run as a Docker container or deployed to a Kubernetes cluster. [Litestream][litestream] is not required to run L1nkZip, but it is strongly encouraged if you are going to use sqlite.

## Requirements

L1nkZip would not be possible without the amazings [FastApi][FastApi] and [PonyORM][PonyORM] projects. The only requirement is Python 3.7+ if you use sqlite. Otherwise, you must install the database driver for your database of choice.

The official Docker image comes with sqlite and postgresql support, but you can extend it to support other databases.

* mysql: MySQLdb
* oracle: cx_oracle

Example from a Dockerfile extending the Docker image to support MySQL:

```Dockerfile
FROM dorogoy/l1nkzip:latest

RUN pip install --no-cache-dir MySQL-python
```

For more information check the [PonyORM documentation](https://docs.ponyorm.org/database.html).

## Configuration

### Required environment variables

* `API_DOMAIN`: Domain of the API. This is the domain of the shortened URLs.
* `DB_TYPE`: Database type. Supported values are `inmemory`, `sqlite` and `postgresql`. Other databases like `mysql`, `oracle`, and `cockroachdb` are also supported thanks to [PonyORM][PonyORM], but require additional drivers.
* `DB_NAME`: Database name. Used for sqlite and postgresql.
* `TOKEN`: Token used to authenticate some administrative actions to the API. This is a secret value and should not be shared.
* `GENERATOR_STRING`: String used to generate the shortened URLs. This is a secret value and should not be shared. You can shuffle uppercase, lowercase letters and/or numbers without repeating them.

### Optional environment variables

* `API_NAME`: Name of the API. Used in the OpenAPI documentation. Default: L1nkZip
* `DB_HOST`: Database host. Used for postgresql.
* `DB_USER`: Database user. Used for postgresql.
* `DB_PASSWORD`: Database password. Used for postgresql.
* `DB_DSN`: Database DSN. Used for Oracle.
* `SITE_URL`: URL of the website. Used when the API is visited from a browser.
* `PHISHTANK`: Enable protection against phisphing. Default: false. The values can also be "anonymous" or your actual [PhishTank key][PhishTank developer info]. More details below.

## Phishtank support

L1nkZip can be configured to check if the URL to be shortened is in the [PhishTank][PhishTank] database. This is an optional feature and can be enabled by setting the `PHISHTANK` environment variable to `anonymous` or your actual [PhishTank key][PhishTank developer info].

To avoid overloading the service, the Phishtank database is downloaded into the local L1nkZip database. This action will be launched each time the update endpoint is contacted successfully. The update endpoint is protected by the `TOKEN` environment variable and should be called periodically by a cronjob or similar. Please, be respectful with the Phishtank policies. Check the [API documentation][Swagger UI] for more details about the update endpoint.

Each update to the Phishtank database can add new entries and remove old ones. This will keep the size of the database under control, it is not growing all the time. When an entry is removed from the database, the shortened URL will be allowed/reactivated again. Keep in mind that L1nkZip is not a censorship tool and it is not intended to be used as such.

## Docker image

The docker image is available on [Docker Hub][Docker Hub].

```bash
docker pull dorogoy/l1nkzip
```

## Kubernetes manifest

This is an example of a StatefulSet to deploy L1nkZip to a Kubernetes cluster. The required secrets are not included and it uses a sqlite database with litestream. This example is for a S3 compatible service (idrivee), [Amazon S3 configuration](https://litestream.io/guides/s3/) for AWS is slightly different. Please, have a look at the [Litestream documentation][litestream] for more details.

```yaml
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: litestream
data:
  litestream.yml: |
    dbs:
      - path: /data/l1nkzip.db
        replicas:
          - type: s3
            bucket: <your-bucket>
            path: l1nkzip.db
            endpoint: <your-endpoint>
            region: <your-region>
            force-path-style: true
---
apiVersion: v1
kind: Service
metadata:
  name: l1nkzip
spec:
  selector:
    app: l1nkzip
  type: ClusterIP
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: 80
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: l1nkzip
spec:
  selector:
    matchLabels:
      app: l1nkzip
  serviceName: l1nkzip
  replicas: 1
  template:
    metadata:
      labels:
        app: l1nkzip
    spec:
      initContainers:
        - name: init-litestream
          image: litestream/litestream:0.3.9
          args:
            [
              "restore",
              "-if-db-not-exists",
              "-if-replica-exists",
              "-v",
              "$(DB_NAME)",
            ]
          volumeMounts:
            - name: l1nkzip
              mountPath: /data
            - name: litestream
              mountPath: /etc/litestream.yml
              subPath: litestream.yml
          env:
            - name: LITESTREAM_ACCESS_KEY_ID
              valueFrom:
                secretKeyRef:
                  name: l1nkzip-secret
                  key: LITESTREAM_ACCESS_KEY_ID
            - name: LITESTREAM_SECRET_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: l1nkzip-secret
                  key: LITESTREAM_SECRET_ACCESS_KEY
            - name: DB_NAME
              valueFrom:
                configMapKeyRef:
                  name: l1nkzip-config
                  key: DB_NAME
      containers:
        - name: litestream
          image: litestream/litestream:0.3.9
          args: ["replicate"]
          volumeMounts:
            - name: l1nkzip
              mountPath: /data
            - name: litestream
              mountPath: /etc/litestream.yml
              subPath: litestream.yml
          env:
            - name: LITESTREAM_ACCESS_KEY_ID
              valueFrom:
                secretKeyRef:
                  name: l1nkzip-secret
                  key: LITESTREAM_ACCESS_KEY_ID
            - name: LITESTREAM_SECRET_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: l1nkzip-secret
                  key: LITESTREAM_SECRET_ACCESS_KEY
          ports:
            - name: metrics
              containerPort: 9090
        - name: l1nkzip
          image: dorogoy/l1nkzip:latest
          imagePullPolicy: Always
          ports:
            - name: http
              containerPort: 80
          volumeMounts:
            - name: l1nkzip
              mountPath: /data
            - name: litestream
              mountPath: /etc/litestream.yml
              subPath: litestream.yml
          env:
            - name: TOKEN
              valueFrom:
                secretKeyRef:
                  name: l1nkzip-secret
                  key: TOKEN
            - name: GENERATOR_STRING
              valueFrom:
                secretKeyRef:
                  name: l1nkzip-secret
                  key: GENERATOR_STRING
            - name: PHISHTANK
              value: "anonymous"
            - name: DB_TYPE
              value: sqlite
            - name: DB_NAME
              valueFrom:
                configMapKeyRef:
                  name: l1nkzip-config
                  key: DB_NAME
            - name: API_DOMAIN
              valueFrom:
                configMapKeyRef:
                  name: l1nkzip-config
                  key: API_DOMAIN
            - name: SITE_URL
              valueFrom:
                configMapKeyRef:
                  name: l1nkzip-config
                  key: SITE_URL
      volumes:
        - name: litestream
          configMap:
            name: litestream
        - name: l1nkzip
          persistentVolumeClaim:
            claimName: l1nkzip
  volumeClaimTemplates:
    - metadata:
        name: l1nkzip
      spec:
        accessModes:
          - ReadWriteOnce
        resources:
          requests:
            storage: 1Gi
```

[FastApi]: https://fastapi.tiangolo.com
[PonyORM]: https://ponyorm.org
[PhishTank]: https://phishtank.org
[PhishTank developer info]: https://phishtank.org/developer_info.php
[Swagger UI]: https://l1nk.zip/docs
[litestream]: https://litestream.io
[Github repository]: https://github.com/dorogoy/l1nkZip
[Docker Hub]: https://hub.docker.com/r/dorogoy/l1nkzip
