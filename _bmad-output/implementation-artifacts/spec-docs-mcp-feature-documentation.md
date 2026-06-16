---
title: 'Document MCP integration in README and GitHub Pages site'
type: 'chore'
created: '2026-06-16'
status: 'done'
baseline_commit: 'd3f724c'
context:
  - _bmad-output/planning-artifacts/epics.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Epic 5 (Model Context Protocol integration) shipped an embedded MCP server over SSE exposing `shorten_url`, `get_original_url`, and `list_urls` tools, but neither the README nor the GitHub Pages user-guide mention it. The README also carries stale test counts (159) that no longer match reality (229).

**Approach:** Add a dedicated MCP page to the mkdocs user-guide site, register it in the nav, surface MCP in the features lists of both README and index.md, add a concise MCP section to the README, and refresh the test counts everywhere they appear.

## Boundaries & Constraints

**Always:** Match existing markdown style and link-reference patterns (e.g. `[text][ref]` then `[ref]: url` footers in the user-guide; inline links in README). Document only what is actually implemented in `l1nkzip/mcp.py` and `l1nkzip/main.py:481-548` — do not invent endpoints, env vars, or tools. MCP requires no new configuration (always enabled; no env var toggles it), so do NOT document a non-existent MCP env var.

**Ask First:** Adding any new file other than `user-guide/docs/mcp.md`.

**Never:** Do not touch code under `l1nkzip/` or `tests/`. Do not modify CHANGELOG.md (release-managed). Do not change the existing Redis/monitoring/rate-limiting/PhishTank documentation. Do not add a new page to README — keep MCP as a section there.

</frozen-after-approval>

## Code Map

- `l1nkzip/mcp.py` -- source of truth for tool names, JSON Schemas, and handler behavior (lines 20-294)
- `l1nkzip/main.py:481-548` -- the actual `/mcp/sse` (GET) and `/mcp/messages` (POST) HTTP routes
- `l1nkzip/config.py` -- confirms no MCP-specific settings exist (MCP is always on)
- `README.md` -- project readme; needs MCP features bullet, MCP section, test-count refresh
- `user-guide/docs/index.md` -- Getting Started page; needs MCP features bullet + link
- `user-guide/docs/selfhosting.md` -- reference for markdown/link style; no MCP config to add
- `user-guide/mkdocs.yml` -- nav config; needs MCP entry

## Tasks & Acceptance

**Execution:**
- [x] `user-guide/docs/mcp.md` -- CREATE -- dedicated MCP page: overview, SSE endpoints (`GET /mcp/sse`, `POST /mcp/messages`), tools table (`shorten_url`/`get_original_url` public, `list_urls` admin+token), tool input schemas, and a client-connection example using curl for the SSE handshake. Follow index.md link-reference footer style.
- [x] `user-guide/mkdocs.yml` -- ADD `MCP Integration: mcp.md` to `nav` between Getting started and Self-hosting.
- [x] `user-guide/docs/index.md` -- ADD MCP bullet to the Features list and a short pointer paragraph linking to the new `/l1nkZip/mcp` page. Use existing `[ref]` link style.
- [x] `README.md` -- ADD an MCP bullet to the Features list; ADD a concise "MCP Integration" section after the Monitoring section covering SSE endpoints and the three tools (public vs admin); REFRESH test counts: "more than 159 tests" -> "more than 229 tests", breakdown 54/61/24 -> 72/119/38, in the Testing section (lines 19, 209, 215-217).
- [x] `README.md` -- UPDATE the two links that point to the testing doc from `user-guide/docs/testing.md` — there is NO testing.md in user-guide/docs (only index.md, selfhosting.md); replace with a valid reference or remove the broken link.

**Acceptance Criteria:**
- Given a reader of the GitHub Pages site, when they open the nav, then an "MCP Integration" page is listed and renders the three documented tools with correct input parameters.
- Given the README features list, when read, then MCP integration is listed alongside Redis/monitoring/rate-limiting.
- Given the README Testing section, when read, then test counts say 229 total with breakdown 72 unit / 119 API / 38 integration (no stale "159").
- Given the documented endpoints, when compared against `l1nkzip/main.py`, then they match exactly (`/mcp/sse` GET, `/mcp/messages` POST) and no fabricated env var is documented.

## Verification

**Commands:**
- `mkdocs build --strict --config-file user-guide/mkdocs.yml` (or `make -C user-guide` if a build target exists) -- expected: site builds with no broken-nav or missing-file errors. If mkdocs isn't installed, skip gracefully.
- `rg -n "159" README.md user-guide/docs` -- expected: no stale test-count references remain.
- `rg -n "/mcp/" README.md user-guide/docs` -- expected: documented endpoints match `l1nkzip/main.py`.

**Manual checks:**
- Visually confirm `mcp.md` tool schemas match `l1nkzip/mcp.py:20-70` (`shorten_url` requires `url`; `get_original_url` requires `link`; `list_urls` requires `token`, optional `limit` default 100, range 1-1000).

## Suggested Review Order

**New MCP reference page (primary deliverable)**

- Entry point: the new dedicated MCP page — endpoints, tool schemas, and client example.
  [`mcp.md:1`](../../user-guide/docs/mcp.md#L1)

- Endpoints table + SSE handshake — verify paths/methods match `main.py`.
  [`mcp.md:7`](../../user-guide/docs/mcp.md#L7)

- Tool reference — three tools with parameter tables; confirm schemas vs `mcp.py`.
  [`mcp.md:38`](../../user-guide/docs/mcp.md#L38)

- Admin token note — uses the working `/l1nkZip/selfhosting` link (patched during review).
  [`mcp.md:107`](../../user-guide/docs/mcp.md#L107)

**README — MCP section + refreshed counts**

- MCP Integration section: endpoints + public/admin tools, links to the new page.
  [`README.md:191`](../../README.md#L191)

- Features bullet + corrected test count (159 -> 229).
  [`README.md:19`](../../README.md#L19)

- Testing section counts + fixed dead testing.md link.
  [`README.md:231`](../../README.md#L231)

**Site wiring**

- MCP bullet in features list pointing at the new page.
  [`index.md:16`](../../user-guide/docs/index.md#L16)

- Nav entry registering the new page.
  [`mkdocs.yml:26`](../../user-guide/mkdocs.yml#L26)
