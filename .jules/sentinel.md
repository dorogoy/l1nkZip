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

## 2026-10-10 - Explicit Defense-in-Depth Block on IPv6 Documentation Prefix (`2001:db8::/32`)
**Vulnerability:** IPv6 documentation addresses (`2001:db8::/32`, RFC 3849) are non-routable addresses reserved for documentation and examples. Python's `ipaddress` module evaluates `2001:db8::/32` as `is_private=True` and `is_global=False`, so the fallthrough check already rejects them.
**Learning:** Explicitly checking `ip.packed.startswith(b"\x20\x01\x0d\xb8")` serves as explicit defense-in-depth against future stdlib reclassifications while documenting intent for RFC 3849 documentation prefixes.
**Prevention:** Explicitly block `2001:db8::/32` (`ip.packed.startswith(b"\x20\x01\x0d\xb8")`) as defense-in-depth during SSRF checks.

## 2026-10-12 - SSRF Bypass via ISATAP IPv6 Addresses with Universal/Local Bit Set (`0200:5efe` Prefix)
**Vulnerability:** ISATAP IPv6 interface identifiers (RFC 5214 §6.1) construct 64-bit interface IDs starting with either `0000:5efe` (u-bit=0) or `0200:5efe` (u-bit=1). Checking only `b"\x00\x00\x5e\xfe"` allows hostnames like `[2000::0200:5efe:127.0.0.1]` or `[2000::0200:5efe:10.0.0.1]` to evaluate to `is_global=True` and `is_private=False` in Python's `ipaddress` module, bypassing SSRF validation.
**Learning:** Checking `ip.packed[8:12] in (b"\x00\x00\x5e\xfe", b"\x02\x00\x5e\xfe")` ensures ISATAP interface IDs with both `u=0` and `u=1` are identified and their embedded IPv4 address unwrapped.
**Prevention:** Always check both `0000:5efe` and `0200:5efe` interface identifier prefixes when unwrapping ISATAP IPv6 addresses for SSRF prevention.

## 2026-10-15 - Explicit Defense-in-Depth Block on RFC 9637 IPv6 Documentation Prefix (`3fff::/20`)
**Vulnerability:** RFC 9637 allocated `3fff::/20` as additional non-routable IPv6 documentation address space (expanding RFC 3849 `2001:db8::/32`). Since Python 3.14 (gh-124217) the stdlib classifies it as `is_private=True` / `is_global=False`, so the existing fallthrough check already rejects these addresses on every Python this project supports (`requires-python >= 3.14`).
**Learning:** Matching `ip.packed[:2] == b"\x3f\xff" and (ip.packed[2] & 0xF0) == 0x00` accurately identifies all IPv6 addresses within the RFC 9637 `/20` documentation range (`3fff::/20`), serving as explicit defense-in-depth.
**Prevention:** Explicitly block `3fff::/20` (`ip.packed[:2] == b"\x3f\xff" and (ip.packed[2] & 0xF0) == 0x00`) alongside `2001:db8::/32` as defense-in-depth during SSRF checks.

## 2026-10-18 - SSRF Bypass via Standard RFC 6052 /48 Layout for Local-Use NAT64 (`64:ff9b:1::/48`)
**Vulnerability:** RFC 6052 §2.2 specifies that for a `/48` IPv6 prefix (such as RFC 8215 Local-Use NAT64 `64:ff9b:1::/48`), the embedded 32-bit IPv4 address is split across bits 48..63 (`ip.packed[6:8]`) and bits 72..87 (`ip.packed[9:11]`), with the u-octet (`ip.packed[8]`) required to be zero. Checking contiguous bytes 7..10 or only `ip.packed[-4:]` failed to evaluate private/loopback IPv4 addresses in canonical RFC 6052 /48 layout, allowing SSRF bypasses.
**Learning:** Reconstructing the split 32-bit IPv4 address (`ip.packed[6:8] + ip.packed[9:11]`) and verifying `ip.packed[8] == 0` extracts the canonical target IPv4 address for RFC 6052 /48 prefixes.
**Prevention:** Always reconstruct split IPv4 fields (`ip.packed[6:8] + ip.packed[9:11]`) and check u-octet when evaluating `/48` NAT64 IPv6 addresses.

## 2026-10-20 - SSRF Bypass via Deprecated 6bone IPv6 Range (`3ffe::/16`)
**Vulnerability:** The 6bone experimental IPv6 network prefix (`3ffe::/16`, RFC 2471) was formally obsoleted and phased out by RFC 3701. In Python's standard `ipaddress` module, addresses in `3ffe::/16` (such as `3ffe::1`) evaluate to `is_global=True` and `is_private=False`, allowing potential SSRF bypasses targeting legacy unrouted IPv6 infrastructure.
**Learning:** Checking `ip.packed[:2] == b"\x3f\xfe"` explicitly identifies all addresses within the deprecated 6bone `/16` prefix.
**Prevention:** Explicitly block `3ffe::/16` (`ip.packed[:2] == b"\x3f\xfe"`) during URL validation for SSRF prevention.

## 2026-10-22 - Rejected Unwrapping of 6over4 IPv6 Interface Identifiers (`0000:0000` Prefix)
**Vulnerability:** Proposal to unwrap 6over4 IPv6 interface identifiers (`0000:0000` prefix at bytes 8..12, RFC 2529) to extract embedded IPv4 addresses for SSRF checks.
**Learning:** In standard IPv6 addressing, the upper 32 bits of a 64-bit interface identifier (`ip.packed[8:12]`) are `0000:0000` (`b"\x00\x00\x00\x00"`) for all low-numbered host IDs (such as `::1`, `::2`, or AS112 address `2001:4:112::1`). Unwrapping `ip.packed[-4:]` whenever `ip.packed[8:12] == b"\x00\x00\x00\x00"` misinterprets lower 32 bits of standard IPv6 host IDs (like `2001:4:112::1`, whose low bytes are `0.0.0.1`) as IPv4 addresses, falsely blocking globally reachable IPv6 destinations and breaking prefix evaluation.
**Prevention:** Do not unwrap `0000:0000` as an embedded 6over4 IPv4 address during IPv6 SSRF checks.

## 2026-10-22 - SSRF Bypass via Reserved Local/Internal TLDs (`.local`, `.internal`, `.home.arpa`)
**Vulnerability:** Reserved top-level domain names such as `.local` (RFC 6762 mDNS), `.internal` (IANA private networks), and `.home.arpa` (RFC 8375 home networks) were not blocked during static URL validation prior to DNS resolution. If DNS or mDNS resolution failed during static validation or resolved on client/internal networks, hostnames like `http://printer.local` or `http://app.internal` could be accepted as shorten target links.
**Learning:** Checking `hostname_lower == "home.arpa" or hostname_lower.endswith((".localhost", ".local", ".internal", ".home.arpa"))` explicitly blocks all reserved local and internal network domain names (including bare `home.arpa` and subdomains) at URL validation time.
**Prevention:** Always include reserved local/internal TLDs (`.local`, `.internal`, `.home.arpa`, `.localhost`) in static hostname checks during URL validation to prevent SSRF targeting local mDNS or private networks.

## 2026-10-25 - SSRF Bypass via Zero-Network IPv4 Targets (`0.0.0.0/8`) in Local-Use NAT64 (`64:ff9b:1::/48`)
**Vulnerability:** Evaluating embedded IPv4 addresses in RFC 6052 Local-Use NAT64 (`64:ff9b:1::/48`) gated `_is_blocked_ip` with `if embedded[0] != 0`. Non-routable targets in the `0.0.0.0/8` range (such as `0.0.0.1` or `0.0.0.0`) had `embedded[0] == 0`, causing `embedded[0] != 0` to evaluate to `False`. This skipped `_is_blocked_ip` evaluation when `ip.packed[-4:] == b"\x00\x00\x00\x00"`, bypassing SSRF validation.
**Learning:** `0.0.0.0/8` IPv4 targets (`ip.packed[0] == 0`) have `embedded[0] == 0`. Gating split `/48` evaluation with `ip.packed[-4:] == b"\x00\x00\x00\x00" or embedded[0] != 0` ensures split placement canonical targets in `0.0.0.0/8` are evaluated and blocked while allowing legacy last-4 placement targets.
**Prevention:** Evaluate `_is_blocked_ip(ipaddress.IPv4Address(embedded))` whenever canonical split placement is used (`ip.packed[-4:] == b"\x00\x00\x00\x00"`), without requiring `embedded[0] != 0`.

## 2026-10-27 - SSRF Bypass via Local-Use NAT64 IPv6 Translation Prefix (`100:64::/96`)
**Vulnerability:** Local-Use NAT64 IPv6 hostnames using the RFC 8215 prefix `100:64::/96` (such as `100:64::127.0.0.1` or `100:64::10.0.0.1`) embed target IPv4 addresses in the last 4 bytes (`ip.packed[-4:]`). In Python's standard `ipaddress` module, `100:64::/96` addresses evaluate to `is_reserved=True`, which causes static validation to block all `100:64::/96` destinations including valid public IPv4 targets, while failing to explicitly evaluate the embedded IPv4 target.
**Learning:** Checking `ip.packed.startswith(b"\x01\x00\x00\x64" + b"\x00" * 8)` identifies Local-Use NAT64 addresses (`100:64::/96`), allowing extraction of `ipaddress.IPv4Address(ip.packed[-4:])` to recursively evaluate `_is_blocked_ip`.
**Prevention:** Always unwrap RFC 8215 Local-Use NAT64 (`100:64::/96`) embedded IPv4 addresses alongside Well-Known NAT64 (`64:ff9b::/96`) and recursively evaluate the extracted IPv4 address against blocked IP rules.
