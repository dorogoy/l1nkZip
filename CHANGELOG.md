## [0.5.8](https://github.com/dorogoy/l1nkZip/compare/v0.5.7...v0.5.8) (2026-04-05)


### Bug Fixes

* **deps:** bump fastapi from 0.120.0 to 0.135.1 ([e44ab02](https://github.com/dorogoy/l1nkZip/commit/e44ab02e62c76b413c2e03fb4c18342ee4f4a980))

## [1.1.4](https://github.com/dorogoy/l1nkZip/compare/v1.1.3...v1.1.4) (2026-09-26)


### Bug Fixes

* replace re.match with re.fullmatch in short link validation ([#304](https://github.com/dorogoy/l1nkZip/issues/304)) ([7057484](https://github.com/dorogoy/l1nkZip/commit/705748404dc4f5b6c0fbf7ba5d108455ef8fcfc1))

## [1.1.3](https://github.com/dorogoy/l1nkZip/compare/v1.1.2...v1.1.3) (2026-09-25)


### Bug Fixes

* block SSRF bypass via NAT64 and 6to4 IPv6 translation addresses ([#302](https://github.com/dorogoy/l1nkZip/issues/302)) ([ff212db](https://github.com/dorogoy/l1nkZip/commit/ff212dbaeaabf99558f174bed459c7a339ac6e70))

## [1.1.2](https://github.com/dorogoy/l1nkZip/compare/v1.1.1...v1.1.2) (2026-09-24)


### Bug Fixes

* prevent SSRF bypass via non-global and multicast IP addresses ([cf546c8](https://github.com/dorogoy/l1nkZip/commit/cf546c8d8f6308be76d6096599a2451f9be2dd9b))

## [1.1.1](https://github.com/dorogoy/l1nkZip/compare/v1.1.0...v1.1.1) (2026-09-23)


### Bug Fixes

* **deps:** bump ruff from 0.16.7 to 0.16.8 ([9e69376](https://github.com/dorogoy/l1nkZip/commit/9e69376db50e3b43506836a588cbc179202a679b))
* **deps:** bump ty from 0.0.78 to 0.0.82 ([aab71b3](https://github.com/dorogoy/l1nkZip/commit/aab71b30a0d92c6edb0b8da6f17415d343af5ecc))
* **deps:** bump uvicorn from 0.52.4 to 0.53.0 ([e37f977](https://github.com/dorogoy/l1nkZip/commit/e37f977de1590192457b739135c2164d4b4fc753))
* escape hyphen in admin token validation regex ([#292](https://github.com/dorogoy/l1nkZip/issues/292)) ([61348d8](https://github.com/dorogoy/l1nkZip/commit/61348d89a80f7e9874a9ba053638380978db167f))
* handle IPv4-mapped IPv6 addresses in SSRF IP checks ([101e6f5](https://github.com/dorogoy/l1nkZip/commit/101e6f52b53faf49b33df73d314acdf42a435da9))
* sanitize site_url scheme on 404 template response ([#298](https://github.com/dorogoy/l1nkZip/issues/298)) ([8e3b9a1](https://github.com/dorogoy/l1nkZip/commit/8e3b9a103b38bf93f71f94ef68b224581b60ce7b))

## [1.1.0](https://github.com/dorogoy/l1nkZip/compare/v1.0.1...v1.1.0) (2026-09-20)


### Features

* add X-Permitted-Cross-Domain-Policies and COOP security headers ([318ec84](https://github.com/dorogoy/l1nkZip/commit/318ec84aacba9ba79327b19c21795c4ff492ed1e))

## [1.0.1](https://github.com/dorogoy/l1nkZip/compare/v1.0.0...v1.0.1) (2026-09-19)


### Bug Fixes

* block hostnames resolving to private IPs to prevent SSRF ([#289](https://github.com/dorogoy/l1nkZip/issues/289)) ([cf08551](https://github.com/dorogoy/l1nkZip/commit/cf0855151aaf059bf933f7f82999dc6ffc8123d8))
* **deps:** bump anyio from 4.10.0 to 4.14.2 ([08a385a](https://github.com/dorogoy/l1nkZip/commit/08a385a3be5ac414bf46c57dc82fedcda709a4a1))


### Documentation

* record deferred CI approval gap on release-please branch ([667c075](https://github.com/dorogoy/l1nkZip/commit/667c0758d2f7561ee183f588264704fe8249260a))

## [1.0.0](https://github.com/dorogoy/l1nkZip/compare/v0.7.6...v1.0.0) (2026-09-18)


### ⚠ BREAKING CHANGES

* **python:** Python 3.12 and 3.13 are no longer supported. The minimum required Python version is now 3.14.

### Features

* **python:** require Python 3.14, drop 3.12/3.13 support ([#285](https://github.com/dorogoy/l1nkZip/issues/285)) ([75eca1e](https://github.com/dorogoy/l1nkZip/commit/75eca1e4376a0be923902f0400d626254dd5dcb1))


### Bug Fixes

* Add HSTS and Permissions-Policy HTTP security headers to all responses. ([425c553](https://github.com/dorogoy/l1nkZip/commit/425c553e4700c033594a605566cd0bf8972df4e3))
* enforce HTTPS for PhishTank API requests ([5b1d0a0](https://github.com/dorogoy/l1nkZip/commit/5b1d0a0e998eadf4e4e936eca74917155b1b2dc0))

## [0.7.6](https://github.com/dorogoy/l1nkZip/compare/v0.7.5...v0.7.6) (2026-09-16)


### Bug Fixes

* **deps:** bump mcp from 2.1.1 to 2.2.0 ([40d19fe](https://github.com/dorogoy/l1nkZip/commit/40d19fe457715c068dd1f6b9e6e4449feb9688d8))
* **deps:** bump psycopg2-binary from 2.9.12 to 2.9.13 ([d77c180](https://github.com/dorogoy/l1nkZip/commit/d77c180323d4567f28669d552d9a2b78b51fb191))
* **deps:** bump ruff from 0.16.6 to 0.16.7 ([1051f8c](https://github.com/dorogoy/l1nkZip/commit/1051f8cebba109be6ac2eb94254c37b8c592192a))
* sensitive token exposure in logs ([#279](https://github.com/dorogoy/l1nkZip/issues/279)) ([0081dac](https://github.com/dorogoy/l1nkZip/commit/0081dac1b50d907c3af259c82147fcc55dcbc243))

## [0.7.5](https://github.com/dorogoy/l1nkZip/compare/v0.7.4...v0.7.5) (2026-09-15)


### Bug Fixes

* SSRF bypass via alternative IPv4 representations ([#274](https://github.com/dorogoy/l1nkZip/issues/274)) ([6b08f68](https://github.com/dorogoy/l1nkZip/commit/6b08f683ea5462ac5979720bf208b7c91de01cc1))

## [0.7.4](https://github.com/dorogoy/l1nkZip/compare/v0.7.3...v0.7.4) (2026-09-14)


### Bug Fixes

* add HTTP security headers middleware ([#269](https://github.com/dorogoy/l1nkZip/issues/269)) ([4ee1271](https://github.com/dorogoy/l1nkZip/commit/4ee1271a91339dbd72a81070db4aa34046c85752))
* **ci:** weekly rebuild must refresh :latest, not create :master ([6fcf011](https://github.com/dorogoy/l1nkZip/commit/6fcf011eb725a465c23eb8318345c37ae0d0fb78))

## [0.7.3](https://github.com/dorogoy/l1nkZip/compare/v0.7.2...v0.7.3) (2026-09-13)


### Bug Fixes

* **docker:** harden image against base-layer CVEs ([#267](https://github.com/dorogoy/l1nkZip/issues/267)) ([83d1876](https://github.com/dorogoy/l1nkZip/commit/83d1876955abb2a7806534021c5afcfabd30aa15))

## [0.7.2](https://github.com/dorogoy/l1nkZip/compare/v0.7.1...v0.7.2) (2026-09-13)


### Bug Fixes

* **deps:** bump ruff from 0.16.5 to 0.16.6 ([2ac998a](https://github.com/dorogoy/l1nkZip/commit/2ac998ac31998ee7fcf90bc277514a2ee97f38f3))
* PhishTank cleanup_days parameter input validation ([#266](https://github.com/dorogoy/l1nkZip/issues/266)) ([73acd7f](https://github.com/dorogoy/l1nkZip/commit/73acd7fe6c79155b7b689b27a65ce3be28443e71))

## [0.7.1](https://github.com/dorogoy/l1nkZip/compare/v0.7.0...v0.7.1) (2026-09-06)


### Bug Fixes

* **deps:** bump prometheus-client from 0.25.0 to 0.26.0 ([d638d45](https://github.com/dorogoy/l1nkZip/commit/d638d45a83e6998b331b93932bb523f6b678d1eb))
* **deps:** bump ruff from 0.16.4 to 0.16.5 ([e606175](https://github.com/dorogoy/l1nkZip/commit/e6061750d830b08e052ecd7e5aefe7fb48d4e325))
* **deps:** bump ty from 0.0.1a19 to 0.0.78 ([f91c72c](https://github.com/dorogoy/l1nkZip/commit/f91c72c1db72c5ee307bf8104d28f15d1780558f))
* **types:** satisfy ty 0.0.78 in cache and models ([86fa931](https://github.com/dorogoy/l1nkZip/commit/86fa931325b3104fe8b20c1c8fb5cf3bf952defa))

## [0.7.0](https://github.com/dorogoy/l1nkZip/compare/v0.6.3...v0.7.0) (2026-08-31)


### Features

* **mcp:** migrate to MCP Python SDK v2.1.1 ([4e312ea](https://github.com/dorogoy/l1nkZip/commit/4e312eac8d89a514666422b09a5f9773ded975f8))


### Bug Fixes

* **deps:** bump psycopg2-binary from 2.9.10 to 2.9.12 ([1b13653](https://github.com/dorogoy/l1nkZip/commit/1b13653c26f0df69d8d01c06713060aefba51668))
* **deps:** bump pytest-asyncio from 1.3.0 to 1.4.0 ([82b70fc](https://github.com/dorogoy/l1nkZip/commit/82b70fcae9888a10fe90c90876cbb8d0314147e5))

## [0.6.3](https://github.com/dorogoy/l1nkZip/compare/v0.6.2...v0.6.3) (2026-08-29)


### Bug Fixes

* **deps:** bump pony from 0.7.19 to 0.7.20 ([cc65e61](https://github.com/dorogoy/l1nkZip/commit/cc65e61dd384eeaf1b31049cd61bde80e01bdb52))
* **deps:** bump ruff from 0.16.3 to 0.16.4 ([d304b53](https://github.com/dorogoy/l1nkZip/commit/d304b53d5a7ac3d177ff1a02ebac7fb854ed63f2))
* **deps:** bump uvicorn from 0.44.0 to 0.52.4 ([a27c4f4](https://github.com/dorogoy/l1nkZip/commit/a27c4f41bf3852f1c3ea717e6ba870328620c3b3))

## [0.6.2](https://github.com/dorogoy/l1nkZip/compare/v0.6.1...v0.6.2) (2026-08-13)


### Bug Fixes

* **deps:** bump idna from 3.10 to 3.15 ([b376a0c](https://github.com/dorogoy/l1nkZip/commit/b376a0c2ca4aea390c121eb1453f4f847090804b))
* **deps:** bump mcp from 1.1.3 to 1.28.1 ([#236](https://github.com/dorogoy/l1nkZip/issues/236)) ([a3976dd](https://github.com/dorogoy/l1nkZip/commit/a3976dd65b4fa628afdaeff44f6149d3811f4ad4))
* **deps:** bump python-dotenv from 1.1.1 to 1.2.2 ([99c6a51](https://github.com/dorogoy/l1nkZip/commit/99c6a51d4b7430d363f1cb1a592975b05c00efbe))
* **deps:** bump ruff from 0.15.12 to 0.16.2 ([#227](https://github.com/dorogoy/l1nkZip/issues/227)) ([c8950c1](https://github.com/dorogoy/l1nkZip/commit/c8950c14ceb01056f681c827ab6d80771abbeeb5))
* **deps:** bump slowapi from 0.1.9 to 0.1.10 ([90f9d00](https://github.com/dorogoy/l1nkZip/commit/90f9d0067ee24b2b57e375227a995576a0aa30bc))
* **deps:** upgrade fastapi, starlette and pydantic to latest ([b661c77](https://github.com/dorogoy/l1nkZip/commit/b661c7794f02195fa33f4a095be64f9e3d9811ee))

## [0.6.1](https://github.com/dorogoy/l1nkZip/compare/v0.6.0...v0.6.1) (2026-06-16)


### Bug Fixes

* address review feedback on test isolation PR ([9689349](https://github.com/dorogoy/l1nkZip/commit/96893496231c2e28dbef258137ad43a0d1c193e1))
* **deps:** bump fastapi from 0.135.3 to 0.137.1 ([b8f1e56](https://github.com/dorogoy/l1nkZip/commit/b8f1e56f125b2d901ea00a52e631dc4b8ccb574c))
* **deps:** bump ruff from 0.15.11 to 0.15.12 ([e12bc9e](https://github.com/dorogoy/l1nkZip/commit/e12bc9ed3083a0e059e03736b97b48d8ea9822dc))
* **version:** read version from pyproject.toml ([674d528](https://github.com/dorogoy/l1nkZip/commit/674d528f6e49ad1187378cc754b99615588781c1))

## [0.6.0](https://github.com/dorogoy/l1nkZip/compare/v0.5.10...v0.6.0) (2026-06-16)


### Features

* add list_urls admin MCP tool with token auth ([0e80d06](https://github.com/dorogoy/l1nkZip/commit/0e80d06efe06eec1b2590b71d18c302dd1fac2ad))
* expose public MCP tools for URL shortening and retrieval ([3ba5d87](https://github.com/dorogoy/l1nkZip/commit/3ba5d878b84fda84b71487e1f605e8eeb752cf70))
* **mcp:** implement SSE transport endpoints and integration tests ([fa93eb4](https://github.com/dorogoy/l1nkZip/commit/fa93eb474e0d61a2c95f655880a7b05b7a771fab))


### Documentation

* document MCP integration and refresh test counts ([18cf5af](https://github.com/dorogoy/l1nkZip/commit/18cf5af38497b4227ebdc6071221c98d577d4a85))
* update architecture and PRD to include MCP integration (AD8) ([cdbf466](https://github.com/dorogoy/l1nkZip/commit/cdbf466d01a447cba6f9f9c468caefcb503fe202))

## [0.5.10](https://github.com/dorogoy/l1nkZip/compare/v0.5.9...v0.5.10) (2026-04-18)


### Bug Fixes

* **deps:** bump prometheus-client from 0.24.1 to 0.25.0 ([fec780a](https://github.com/dorogoy/l1nkZip/commit/fec780af411234084a7816d37227da5d93a0c4f7))
* **deps:** bump ruff from 0.12.7 to 0.15.10 ([1fe8fbe](https://github.com/dorogoy/l1nkZip/commit/1fe8fbe42ee15a72867f46a1c2fdd0e7f4b2f694))
* **deps:** bump validators from 0.34.0 to 0.35.0 ([64f8875](https://github.com/dorogoy/l1nkZip/commit/64f887542b3663a34073cca8e95ff2f59d5b07fe))

## [0.5.9](https://github.com/dorogoy/l1nkZip/compare/v0.5.8...v0.5.9) (2026-04-06)


### Bug Fixes

* **deps:** bump pytest-cov from 7.0.0 to 7.1.0 ([84e9967](https://github.com/dorogoy/l1nkZip/commit/84e99671474363d971fa879f835bdc7b0cb2a87a))
* **deps:** bump redis from 5.0.1 to 7.4.0 ([42ecd03](https://github.com/dorogoy/l1nkZip/commit/42ecd03b4ecc995162d19d08c4dc9698886e7b43))
* **deps:** bump uvicorn from 0.41.0 to 0.44.0 ([d6a0d83](https://github.com/dorogoy/l1nkZip/commit/d6a0d832fed19d02f9480ee256b9a3d2a960bee3))

## [0.5.7](https://github.com/dorogoy/l1nkZip/compare/v0.5.6...v0.5.7) (2026-04-05)


### Bug Fixes

* **deps:** bump pytest from 8.4.1 to 9.0.2 ([4f380b6](https://github.com/dorogoy/l1nkZip/commit/4f380b66547d63f45eb51f8e56967bd3a8c083a3))

## [0.5.6](https://github.com/dorogoy/l1nkZip/compare/v0.5.5...v0.5.6) (2026-04-05)


### Bug Fixes

* **deps:** bump pytest-asyncio from 1.2.0 to 1.3.0 ([e2cb242](https://github.com/dorogoy/l1nkZip/commit/e2cb24239064b3da4ba8bce93b781996f3cb4d2e))

## [0.5.5](https://github.com/dorogoy/l1nkZip/compare/v0.5.4...v0.5.5) (2026-03-15)


### Bug Fixes

* **deps:** bump pytest-cov from 6.0.0 to 7.0.0 ([9c1779c](https://github.com/dorogoy/l1nkZip/commit/9c1779c527391927b82af2a3564dc9002a3dc05b))

## [0.5.4](https://github.com/dorogoy/l1nkZip/compare/v0.5.3...v0.5.4) (2026-03-15)


### Bug Fixes

* **deps:** bump uvicorn from 0.35.0 to 0.40.0 ([5be601a](https://github.com/dorogoy/l1nkZip/commit/5be601a92a8b241e8813c16d87dc73c3ee938eaf))

## [0.5.3](https://github.com/dorogoy/l1nkZip/compare/v0.5.2...v0.5.3) (2026-03-15)


### Bug Fixes

* **deps:** bump prometheus-client from 0.21.0 to 0.24.1 ([9957859](https://github.com/dorogoy/l1nkZip/commit/995785956df3afe5b398b377a18ef0b3591491bf))

## [0.5.2](https://github.com/dorogoy/l1nkZip/compare/v0.5.1...v0.5.2) (2026-02-01)


### Bug Fixes

* **deps:** bump fastapi from 0.115.12 to 0.120.0 ([5f8f8b6](https://github.com/dorogoy/l1nkZip/commit/5f8f8b6f7c3fb4d8d476ca1a1cf15eb872504f9d))
* **deps:** bump pytest-asyncio from 0.25.1 to 1.2.0 ([249595e](https://github.com/dorogoy/l1nkZip/commit/249595e68e00ef84dcb6007996a2574490304cfc))

## [0.5.1](https://github.com/dorogoy/l1nkZip/compare/v0.5.0...v0.5.1) (2025-08-31)


### Bug Fixes

* Replaces mypy with ty for type checking ([c0740f0](https://github.com/dorogoy/l1nkZip/commit/c0740f08d8483ddc030d44b95641ad03e498381e))

# [0.5.0](https://github.com/dorogoy/l1nkZip/compare/v0.4.5...v0.5.0) (2025-08-31)


### Bug Fixes

* **api:** async phishing checks ([b321bb4](https://github.com/dorogoy/l1nkZip/commit/b321bb436b9e1bfa13cd235615573214b314e5cb))
* **db:** handle race condition in insert_link ([e15e872](https://github.com/dorogoy/l1nkZip/commit/e15e8722939bb63d159f5eaa1a349c780ecf5b91))
* **deps:** update Python version to 3.12 and migrate to uv package manager ([4069798](https://github.com/dorogoy/l1nkZip/commit/4069798f75f5f6fe607ca68ebf5c84e67a2fb3cb))
* Improves error handling and code clarity ([401164a](https://github.com/dorogoy/l1nkZip/commit/401164aa0c6437a33d75be47d933fc636537ffa5))
* **phishtank:** add PhishTank integration ([8d8d9de](https://github.com/dorogoy/l1nkZip/commit/8d8d9de8a0f24fd29baf34b38481157fbd6cc228))


### Features

* **api:** add comprehensive URL and admin token validation ([25d9589](https://github.com/dorogoy/l1nkZip/commit/25d9589f9d11ec751ef2894f1afae25f68c2307e))
* **api:** add Prometheus-based monitoring for L1nkZip ([97e8d32](https://github.com/dorogoy/l1nkZip/commit/97e8d32fda44ce87e68f07a5b4c113f2fbca21f9))
* **cache:** add Redis-based redirect caching ([9b4616c](https://github.com/dorogoy/l1nkZip/commit/9b4616c44374ac91994892d17e53f2ae0179d63e))
* **config:** add rate limiting configuration ([8589365](https://github.com/dorogoy/l1nkZip/commit/858936546f92a596d26af71f1f9e4beab457e133))

## [0.4.5](https://github.com/dorogoy/l1nkZip/compare/v0.4.4...v0.4.5) (2025-08-30)


### Bug Fixes

* **deps:** bump mypy from 1.10.0 to 1.17.1 ([53d0ae7](https://github.com/dorogoy/l1nkZip/commit/53d0ae78545db818f9e94295bda269d1280dc8e1))
* **deps:** bump pydantic-settings from 2.4.0 to 2.10.1 ([98d2091](https://github.com/dorogoy/l1nkZip/commit/98d209180493617ff63f44aea1469c43fef9b8ea))
* **deps:** bump uvicorn from 0.34.0 to 0.35.0 ([ac20c39](https://github.com/dorogoy/l1nkZip/commit/ac20c398931d0533780c838453f62b36d0143e78))

## [0.4.4](https://github.com/dorogoy/l1nkZip/compare/v0.4.3...v0.4.4) (2025-07-30)


### Bug Fixes

* **deps:** bump ruff from 0.9.3 to 0.12.5 ([c486c44](https://github.com/dorogoy/l1nkZip/commit/c486c4416b69fdce7b97588d19be413ddb689f44))

## [0.4.3](https://github.com/dorogoy/l1nkZip/compare/v0.4.2...v0.4.3) (2025-06-10)


### Bug Fixes

* **deps:** bump jinja2 from 3.1.5 to 3.1.6 ([3dd768d](https://github.com/dorogoy/l1nkZip/commit/3dd768d04ea72c1602880e772171a8addd687598))

## [0.4.2](https://github.com/dorogoy/l1nkZip/compare/v0.4.1...v0.4.2) (2025-06-10)


### Bug Fixes

* **deps:** bump fastapi from 0.115.8 to 0.115.12 ([ebce3e2](https://github.com/dorogoy/l1nkZip/commit/ebce3e2fa6f29adfe6fd85d168ae1a9979f215ec))

## [0.4.1](https://github.com/dorogoy/l1nkZip/compare/v0.4.0...v0.4.1) (2025-02-26)


### Bug Fixes

* **deps:** bump fastapi from 0.115.2 to 0.115.8 ([1d363e8](https://github.com/dorogoy/l1nkZip/commit/1d363e8036cda9283675cbfcb94583b33027d1bd))

# [0.4.0](https://github.com/dorogoy/l1nkZip/compare/v0.3.8...v0.4.0) (2025-01-29)


### Bug Fixes

* convert Link query to list for stable iteration ([3b45da0](https://github.com/dorogoy/l1nkZip/commit/3b45da064a4f3b18b06e585a89bf768528291649))


### Features

* add health check endpoint and db connection test ([6738edd](https://github.com/dorogoy/l1nkZip/commit/6738edd6c79a7501e606266641d89ba740710d89))

## [0.3.8](https://github.com/dorogoy/l1nkZip/compare/v0.3.7...v0.3.8) (2025-01-29)


### Bug Fixes

* **deps:** bump uvicorn from 0.30.6 to 0.34.0 ([5d85050](https://github.com/dorogoy/l1nkZip/commit/5d8505010b3b91d34a910aafee7256f812fb646e))

## [0.3.7](https://github.com/dorogoy/l1nkZip/compare/v0.3.6...v0.3.7) (2025-01-21)


### Bug Fixes

* **deps:** bump jinja2 from 3.1.4 to 3.1.5 ([a378ad0](https://github.com/dorogoy/l1nkZip/commit/a378ad07cfa45da51ff93ae37416c71e3e15179b))

## [0.3.6](https://github.com/dorogoy/l1nkZip/compare/v0.3.5...v0.3.6) (2025-01-21)


### Bug Fixes

* **deps:** bump httpx from 0.27.0 to 0.28.1 ([2880037](https://github.com/dorogoy/l1nkZip/commit/2880037083b5d9d16732a1ee0ae9af523885093b))

## [0.3.5](https://github.com/dorogoy/l1nkZip/compare/v0.3.4...v0.3.5) (2024-10-15)


### Bug Fixes

* **deps:** bump validators from 0.28.3 to 0.34.0 ([957f09f](https://github.com/dorogoy/l1nkZip/commit/957f09f18ec5ed9823aec5a2e7e96a6144c32fc0))

## [0.3.4](https://github.com/dorogoy/l1nkZip/compare/v0.3.3...v0.3.4) (2024-10-15)


### Bug Fixes

* **deps:** bump fastapi from 0.111.0 to 0.115.2 ([5bfddfa](https://github.com/dorogoy/l1nkZip/commit/5bfddfae934516a501a7f908e8f797e8ad46eb60))

## [0.3.3](https://github.com/dorogoy/l1nkZip/compare/v0.3.2...v0.3.3) (2024-09-09)


### Bug Fixes

* **deps:** bump pydantic-settings from 2.2.1 to 2.4.0 ([#83](https://github.com/dorogoy/l1nkZip/issues/83)) ([1050bfc](https://github.com/dorogoy/l1nkZip/commit/1050bfced2251e5fd96acd52c5a84d52257312a0))

## [0.3.2](https://github.com/dorogoy/l1nkZip/compare/v0.3.1...v0.3.2) (2024-09-09)


### Bug Fixes

* **deps:** bump pony from 0.7.16 to 0.7.19 ([097ed4c](https://github.com/dorogoy/l1nkZip/commit/097ed4c0d7ef25487a18b4e5e3f6aadc29e1bbe4))

## [0.3.1](https://github.com/dorogoy/l1nkZip/compare/v0.3.0...v0.3.1) (2024-09-09)


### Bug Fixes

* **deps:** bump uvicorn from 0.29.0 to 0.30.6 ([75a0523](https://github.com/dorogoy/l1nkZip/commit/75a05237de40a10d7e9dde9802d325b6c0c195bc))

# [0.3.0](https://github.com/dorogoy/l1nkZip/compare/v0.2.2...v0.3.0) (2024-06-02)


### Features

* Add `get_visits` function to retrieve link info ([96084ee](https://github.com/dorogoy/l1nkZip/commit/96084eed92aa69ba589615f432b7054f36097ca5))

## [0.2.2](https://github.com/dorogoy/l1nkZip/compare/v0.2.1...v0.2.2) (2024-06-01)


### Bug Fixes

* **deps:** bump validators from 0.22.0 to 0.28.3 ([5c154d0](https://github.com/dorogoy/l1nkZip/commit/5c154d01d4075dda0de0efa783929c802b25ceca))

## [0.2.1](https://github.com/dorogoy/l1nkZip/compare/v0.2.0...v0.2.1) (2024-06-01)


### Bug Fixes

* **deps:** bump fastapi from 0.109.1 to 0.111.0 ([f32b1e7](https://github.com/dorogoy/l1nkZip/commit/f32b1e79f64c2f1fd560002b94c5d3de8a223f55))

# [0.2.0](https://github.com/dorogoy/l1nkZip/compare/v0.1.11...v0.2.0) (2024-06-01)


### Features

* **release:** add exec plugin to update version ([0bc251a](https://github.com/dorogoy/l1nkZip/commit/0bc251ae938425b01eaa89c55cfd0be9c93f85db))

## [0.1.11](https://github.com/dorogoy/l1nkZip/compare/v0.1.10...v0.1.11) (2024-06-01)


### Bug Fixes

* **deps:** bump pydantic-settings from 2.1.0 to 2.2.1 ([1f0aa6b](https://github.com/dorogoy/l1nkZip/commit/1f0aa6bc001953dc5b6cd819e89b8e4903a45cdc))

## [0.1.10](https://github.com/dorogoy/l1nkZip/compare/v0.1.9...v0.1.10) (2024-05-22)


### Bug Fixes

* **deps:** bump httpx from 0.24.1 to 0.27.0 ([6e84afd](https://github.com/dorogoy/l1nkZip/commit/6e84afdfa6b8fb3abecce2647aa050454f0f41d9))

## [0.1.9](https://github.com/dorogoy/l1nkZip/compare/v0.1.8...v0.1.9) (2024-05-18)


### Bug Fixes

* Bump jinja2 from 3.1.3 to 3.1.4 ([#43](https://github.com/dorogoy/l1nkZip/issues/43)) ([d07b595](https://github.com/dorogoy/l1nkZip/commit/d07b5952a63c5eb6aff6a35202912178a2a96f6b))
