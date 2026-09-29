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
