## 2026-09-14 - SSRF Bypass via IPv4-Mapped IPv6 Addresses
**Vulnerability:** `ipaddress.ip_address` returns an `IPv6Address` for IPv4-mapped IPv6 hostnames (such as `::ffff:127.0.0.1` or `::ffff:10.0.0.1`), for which `is_private` and `is_loopback` can evaluate to `False` on older Python runtimes or fail to check underlying IPv4 attributes.
**Learning:** Checking `isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped` allows extracting the underlying `IPv4Address` to recursively evaluate `_is_blocked_ip(ip.ipv4_mapped)`.
**Prevention:** Always unwrap `ip.ipv4_mapped` when evaluating `IPv6Address` instances against blocked IP ranges.

## 2026-09-14 - SSRF Bypass via Alternative IPv4 Formats
**Vulnerability:** Python's standard `ipaddress.ip_address` raises `ValueError` for IPv4 hostnames in non-decimal/non-quad-dotted integer/hex/octal representations (such as `2130706433`, `0x7f000001`, `0177.0.0.1`, `127.1`, `0`), which causes URL validation logic relying solely on `ipaddress.ip_address(hostname)` to skip private/loopback IP detection and allow SSRF bypasses.
**Learning:** `socket.inet_aton` properly converts these alternative IPv4 formats into 4-byte packed representations, which can then be safely passed to `ipaddress.ip_address(packed)` to obtain an `IPv4Address` object for `is_private` / `is_loopback` checks.
**Prevention:** Always parse hostnames using `socket.inet_aton(hostname)` prior to `ipaddress.ip_address` check when validating URLs for SSRF prevention.
