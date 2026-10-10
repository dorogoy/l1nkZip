## 2026-09-14 - SSRF Bypass via IPv4-Mapped IPv6 Addresses
**Vulnerability:** `ipaddress.ip_address` returns an `IPv6Address` for IPv4-mapped IPv6 hostnames (such as `::ffff:127.0.0.1` or `::ffff:10.0.0.1`), for which `is_private` and `is_loopback` can evaluate to `False` on older Python runtimes or fail to check underlying IPv4 attributes.
**Learning:** Checking `isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped` allows extracting the underlying `IPv4Address` to recursively evaluate `_is_blocked_ip(ip.ipv4_mapped)`.
**Prevention:** Always unwrap `ip.ipv4_mapped` when evaluating `IPv6Address` instances against blocked IP ranges.

## 2026-09-14 - SSRF Bypass via Alternative IPv4 Formats
**Vulnerability:** Python's standard `ipaddress.ip_address` raises `ValueError` for IPv4 hostnames in non-decimal/non-quad-dotted integer/hex/octal representations (such as `2130706433`, `0x7f000001`, `0177.0.0.1`, `127.1`, `0`), which causes URL validation logic relying solely on `ipaddress.ip_address(hostname)` to skip private/loopback IP detection and allow SSRF bypasses.
**Learning:** `socket.inet_aton` properly converts these alternative IPv4 formats into 4-byte packed representations, which can then be safely passed to `ipaddress.ip_address(packed)` to obtain an `IPv4Address` object for `is_private` / `is_loopback` checks.
**Prevention:** Always parse hostnames using `socket.inet_aton(hostname)` prior to `ipaddress.ip_address` check when validating URLs for SSRF prevention.

## 2026-09-14 - SSRF Bypass via Non-Global Shared Address Space (CGNAT / Tailscale) and Multicast IPs
**Vulnerability:** `ipaddress.ip_address` returns `is_private=False` and `is_reserved=False` for Carrier-Grade NAT / Shared Address Space (`100.64.0.0/10`, RFC 6598) and multicast addresses (`224.0.0.0/4`). URL validation relying only on `is_private` or `is_reserved` allows SSRF targeting internal CGNAT, Tailscale mesh nodes, or multicast endpoints.
**Learning:** Checking `not ip.is_global` or `ip.is_multicast` correctly identifies non-globally-routable addresses, including CGNAT/Shared Address Space (`100.64.0.0/10`) and multicast (`224.0.0.0/4`), blocking them during SSRF validation.
**Prevention:** Always include `not ip.is_global` and `ip.is_multicast` alongside `is_private` / `is_loopback` / `is_link_local` / `is_reserved` / `is_unspecified` when evaluating IP addresses against SSRF.

## 2026-09-14 - SSRF Bypass via IPv6 Translation Prefixes (NAT64, 6to4, ISATAP)
**Vulnerability:** IPv6 translation addresses such as NAT64 (`64:ff9b::/96`), 6to4 (`2002::/16`), and ISATAP (`0000:5efe:<ipv4>`) embed IPv4 target addresses into IPv6 hostnames (e.g. `64:ff9b::127.0.0.1`, `2002:7f00:0001::`, or `2000::5efe:7f00:1`). Python's `ipaddress.IPv6Address` treats these addresses as global IPv6 addresses (`is_private=False`, `is_global=True`), bypassing standard IPv6 SSRF checks.
**Learning:** Standard library `ipaddress.IPv6Address` provides `ip.sixtofour` for 6to4 addresses; NAT64 (`64:ff9b::/96`) embedded IPv4 can be extracted from `ip.packed[-4:]`; and ISATAP interface identifiers (`ip.packed[8:12] == b"\x00\x00\x5e\xfe"`) embed IPv4 addresses in `ip.packed[-4:]`.
**Prevention:** Always unwrap `ip.sixtofour`, NAT64 (`64:ff9b::/96`), and ISATAP (`0000:5efe`) embedded IPv4 addresses and recursively evaluate `_is_blocked_ip` on the extracted IPv4 address.

## 2026-09-26 - SSRF Bypass via IPv4-Compatible IPv6 Addresses (`::/96` Prefix)
**Vulnerability:** IPv4-compatible IPv6 hostnames using the deprecated `::/96` prefix (such as `::127.0.0.1` or `::10.0.0.1`) embed IPv4 addresses directly in the last 4 bytes of an IPv6 address starting with 12 zero bytes (`b"\x00" * 12`). Python's `ipaddress.IPv6Address` treats these as global IPv6 addresses (`is_private=False`, `is_global=True`), bypassing standard IPv6 SSRF checks while dual-stack HTTP clients or network stacks can fall back to connecting to the embedded IPv4 address.
**Learning:** Checking `ip.packed.startswith(b"\x00" * 12)` identifies IPv4-compatible IPv6 addresses, allowing extraction of `ipaddress.IPv4Address(ip.packed[-4:])` to recursively evaluate `_is_blocked_ip`.
**Prevention:** Always check for `b"\x00" * 12` prefix on `IPv6Address` instances, extract the embedded IPv4 address, and evaluate it against blocked IP rules.

## 2026-09-26 - SSRF Bypass via Deprecated IPv6 Site-Local Addresses (`fec0::/10` Prefix)
**Vulnerability:** IPv6 site-local hostnames using the deprecated `fec0::/10` prefix (such as `fec0::1`) evaluate to `is_private=False` and `is_global=True` in Python's `ipaddress` module, bypassing standard IPv6 SSRF checks.
**Learning:** Python's `ipaddress.IPv6Address` provides `ip.is_site_local` specifically to identify site-local addresses (`fec0::/10`), which are non-globally routable internal site network addresses.
**Prevention:** Always include `getattr(ip, "is_site_local", False)` or `ip.is_site_local` alongside `is_global`, `is_private`, `is_loopback`, `is_link_local`, `is_reserved`, `is_unspecified`, and `is_multicast` when evaluating IP addresses against SSRF.

## 2026-09-26 - Explicit Blocking of Deprecated Teredo IPv6 (`2001:0::/32`) and `0.0.0.0/8` Range
**Vulnerability:** On Python >=3.14 (and >=3.12.4), `2001:0::/32` is part of `2001::/23` which `ipaddress` classifies as non-global/private. Unwrapping embedded IPv4 in Teredo addresses could allow public targets that were previously blocked under the prefix.
**Learning:** For deprecated protocols like Teredo (`2001:0::/32`), explicitly blocking the entire prefix outright (`ip.packed.startswith(b"\x20\x01\x00\x00")`) prevents any unexpected opening of attack vectors while serving as defense-in-depth alongside `0.0.0.0/8` (`ip.packed[0] == 0`).
**Prevention:** Always block deprecated tunneling prefixes like Teredo outright rather than unwrapping embedded IPv4 destinations.

## 2026-10-01 - SSRF Bypass via Local-Use NAT64 IPv6 Addresses (`64:ff9b:1::/48` Prefix)
**Vulnerability:** Local-Use NAT64 IPv6 hostnames using the RFC 8215 prefix `64:ff9b:1::/48` (such as `64:ff9b:1::127.0.0.1` or `64:ff9b:1::10.0.0.1`) embed target IPv4 addresses in the last 4 bytes. Without explicit unwrapping, internal loopback or private IPv4 addresses embedded in Local-Use NAT64 prefixes could bypass SSRF checks depending on Python runtime address classification, or reject valid public targets.
**Learning:** Checking `ip.packed.startswith(b"\x00\x64\xff\x9b\x00\x01")` identifies Local-Use NAT64 addresses (`64:ff9b:1::/48`), allowing extraction of `ipaddress.IPv4Address(ip.packed[-4:])` to recursively evaluate `_is_blocked_ip`.
**Prevention:** Always unwrap RFC 8215 Local-Use NAT64 (`64:ff9b:1::/48`) embedded IPv4 addresses alongside Well-Known NAT64 (`64:ff9b::/96`) and recursively evaluate the extracted IPv4 address against blocked IP rules.

## 2026-10-02 - SSRF Bypass via ORCHIDv2 IPv6 Address Range (`2001:20::/28`)
**Vulnerability:** ORCHIDv2 addresses (`2001:20::/28`, RFC 7343) are non-routable IPv6 overlay addresses for cryptographic identifiers. In Python's standard `ipaddress` module, ORCHIDv2 addresses evaluate to `is_global=True` and `is_private=False`, allowing SSRF validation that relies solely on `is_global` / `is_private` to be bypassed.
**Learning:** Matching `ip.packed.startswith(b"\x20\x01\x00") and (ip.packed[3] & 0xF0) == 0x20` precisely identifies all IPv6 addresses within the ORCHIDv2 `/28` range (`2001:20::/28`).
**Prevention:** Explicitly check and block `2001:20::/28` IPv6 prefix during URL validation for SSRF prevention.

## 2026-10-06 - Rejected Block on Drone Remote ID IPv6 Range (`2001:30::/28`)
**Vulnerability:** Proposal to block Drone Remote ID IPv6 addresses (`2001:30::/28`, allocated by RFC 9374) as non-routable targets.
**Learning:** Per RFC 9374 and the IANA IPv6 Special-Purpose Address Space registry, `2001:30::/28` is marked `Forwardable: True` and `Globally Reachable: True`. Python correctly reports `is_global=True` and `is_private=False` for addresses in this block. Blocking `2001:30::/28` rejects globally reachable IPv6 destinations and would introduce a compatibility-breaking rule without security justification.
**Prevention:** Do not block `2001:30::/28` during SSRF checks as it is globally routable.

## 2026-10-07 - SSRF Bypass via IPv4 IETF Protocol Assignments Range (`192.0.0.0/24`)
**Vulnerability:** In Python's standard `ipaddress` module, `IPv4Network("192.0.0.0/24")` (RFC 6890 IETF Protocol Assignments) is marked as `is_private=True`, but CPython specifically exempts PCP Anycast (`192.0.0.9`, RFC 7723) and TURN Anycast (`192.0.0.10`, RFC 8155) addresses, returning `is_global=True` and `is_private=False`. As a result, URL validation relying on `is_private` / `is_global` fails to block `192.0.0.9` and `192.0.0.10`, allowing potential SSRF targeting of local gateway/router infrastructure.
**Learning:** Matching `ip.packed[:3] == b"\xc0\x00\x00"` explicitly identifies all addresses in the `192.0.0.0/24` range, including PCP and TURN Anycast addresses.
**Prevention:** Explicitly block `192.0.0.0/24` (`ip.packed[:3] == b"\xc0\x00\x00"`) alongside `2001:1::/32` during URL validation for SSRF prevention.

## 2026-10-08 - SSRF Bypass via AMT IPv4 Anycast Range (`192.52.193.0/24`)
**Vulnerability:** Automatic Multicast Tunneling (AMT) IPv4 Anycast hostnames in the `192.52.193.0/24` range (RFC 7450) evaluate to `is_global=True` and `is_private=False` in Python's standard `ipaddress` module. While `2001:3::/32` was previously blocked for IPv6, `192.52.193.0/24` remained unblocked, allowing potential SSRF targeting AMT multicast gateway infrastructure.
**Learning:** Matching `ip.packed[:3] == b"\xc0\x34\xc1"` explicitly identifies all addresses in the AMT IPv4 range (`192.52.193.0/24`).
**Prevention:** Explicitly block `192.52.193.0/24` (`ip.packed[:3] == b"\xc0\x34\xc1"`) alongside `2001:3::/32` during URL validation for SSRF prevention.

## 2026-10-09 - Rejected Block on AS112 IPv4/IPv6 Ranges (`192.175.48.0/24`, `192.31.196.0/24`, `2001:4:112::/48`)
**Vulnerability:** Proposal to block AS112 service addresses (`192.175.48.0/24`, `192.31.196.0/24`, and `2001:4:112::/48`, RFC 7534 / RFC 7535) as non-routable sinkhole targets.
**Learning:** Per RFC 7534 §3.4 and the IANA IPv4 and IPv6 Special-Purpose Address Space registries, AS112 prefixes are marked `Forwardable: True` and `Globally Reachable: True`, and are BGP-announced on the public Internet. Python correctly reports `is_global=True` and `is_private=False` for addresses in these blocks. Blocking AS112 addresses rejects globally reachable IPv4 and IPv6 destinations and would introduce a compatibility-breaking regression without security justification.
**Prevention:** Do not block AS112 IPv4 (`192.175.48.0/24`, `192.31.196.0/24`) or IPv6 (`2001:4:112::/48`) during SSRF checks as they are globally reachable.
