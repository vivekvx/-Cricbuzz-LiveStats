# API setup and research record

Research date: 24 October 2026. Initial research ran without credentials. A key was subsequently supplied and authenticated match-list, current scorecard, profile and career-table access succeeded. See [live verification](LIVE_VERIFICATION.md). Account quotas, plan entitlements and archive coverage remain unverified.

## Selected adapter

**Cricbuzz Cricket**, published by `cricketapilive` on RapidAPI, legacy **v1** contract. This is a marketplace provider; do not describe it as an official Cricbuzz developer API. API versions and similarly named products are not interchangeable.

Primary provider references:

- [Cricbuzz Cricket live operation](https://rapidapi.com/cricketapilive/api/cricbuzz-cricket/playground/matches%2Flive): indexed public documentation lists live matches and X-RapidAPI-Key / X-RapidAPI-Host headers.
- [Scorecard operation](https://rapidapi.com/cricketapilive/api/cricbuzz-cricket/playground/matches%2Fget-scorecard): public listing identifies matchId as required.
- [Provider playground](https://rapidapi.com/cricketapilive/api/cricbuzz-cricket): lists matches, series, players, venues and stats. Newer indexed entries advertise v2; select the compatible legacy v1 version if your subscription still exposes it.
- [Selected provider pricing](https://rapidapi.com/cricketapilive/api/cricbuzz-cricket/pricing): the unauthenticated page did not expose usable pricing during research. Exact quota, request rate, per-endpoint entitlements and continued v1 access remain **unverified**. Check your subscribed account. Do not copy quotas from another similarly named API.
- [RapidAPI subscription documentation](https://docs.rapidapi.com/v2/docs/api-pricing): subscriptions and billing depend on the provider's plan.

The legacy wire paths below are cross-checked against the published [v1 generated endpoint reference](https://pypi.org/project/bach-cricbuzz-cricket/) and community integrations. The live-list, scorecard and player endpoints were subsequently authenticated successfully; series and venue adapters remain fixture-only. Direct retrieval of the RapidAPI playground returned HTTP 403 in this environment. Public operation discovery was possible through indexed documentation; authenticated OpenAPI export was not available during initial research. Response verification was subsequently completed for the five paths listed in LIVE_VERIFICATION.md.

| Resource | Implemented legacy wire path | UI use / limits |
|---|---|---|
| Live/recent/upcoming | `/matches/v1/{live,recent,upcoming}` | Match centre refresh; no pagination parameter invented |
| Full scorecard | `/mcenter/v1/{matchId}/scard` | On-demand batting, bowling and innings ingestion |
| Profile | `/stats/v1/player/{playerId}` | Fetch player statistics |
| Career batting / bowling | `/stats/v1/player/{playerId}/{batting,bowling}` | Separate provider career snapshots |
| Series matches | `/series/v1/{seriesId}` | Reusable adapter, not bulk historical backfill |
| Venue metadata | `/venues/v1/{venueId}` | Reusable adapter; match list venue details are stored |

Live/recent lists do **not** promise complete historical coverage. Archive pagination, archive retention, which endpoints need paid plans, and exact v1 account access could not be established without provider access. The application does not invent page/cursor parameters or bulk-fetch a supposed complete history. Series start dates, capacities, winner/toss metadata and fielding details may be absent from imported list/scorecard records; corresponding analytics legitimately return incomplete/empty results. Country is kept Unknown if not supplied. A T20 record in an explicitly International match group is classified T20I; league/domestic groups remain T20. Synthetic data verifies the complete analytical schema independently of these coverage gaps.

## Configure

1. Open the selected provider listing, inspect version and pricing, and subscribe to a plan yourself.
2. Copy `.env.example` to `.env`; set `RAPIDAPI_KEY`. The app loads this file automatically. Alternatively put `RAPIDAPI_KEY = "..."` in `.streamlit/secrets.toml`.
3. Leave the base and host at the v1 defaults unless the provider explicitly supplies compatible replacements. The host must be the provider host, not rapidapi.com.
4. Start the app, choose **Live API**, and press **Refresh matches**. Select a returned match ID and fetch its detailed scorecard. Fetch player career statistics separately on the Player statistics page.
5. If your account only offers incompatible v2, the schema checks will reject it. A v2 transformation requires a real response/OpenAPI contract; changing only the base URL cannot resolve it. Use Sample Data meanwhile.

Never paste a key into source, commit it, or include it in a recording. Both environment and Streamlit secrets are ignored by Git. No live credential was searched for elsewhere on this machine.

## Request behavior

HTTPS only; no redirects forwarding credential headers. Five-second connection and twenty-second read timeouts. Up to three attempts for transport/server failures with 1/2-second backoff. 401/403 fail immediately; 404 means endpoint/resource unavailable; 429 shows a sanitized Retry-After and requires a later manual refresh, avoiding extra quota use. No provider body or secret is logged. Responses must match expected object/list/table shapes. Empty lists are distinct from failures. Successful payload snapshots and UTC fetch timestamps are stored for provenance. The UI marks cached snapshots as potentially stale. Cache TTL is 120 seconds; explicit refresh clears the appropriate cache. No background polling occurs.

## Parsing limits

The original fixtures are synthetic contract examples. `current_scorecard.json` is a minimal projection of the authenticated current scorecard; PROVENANCE.md identifies its source. Both legacy scoreCard and observed current lowercase scorecard structures are supported. Current cards resolve batting-team names against stored match teams, preserve zero-ball dismissals, exclude did-not-bat rows from batting performances, and treat "batting" as not dismissed. Positions follow the returned batter sequence; partnership results remain proxies. A profile fills unknown styles/role/country only when supplied. Career API tables are preserved separately and displayed as fetched; they are never added to scorecard-derived totals, which would double count performance. Fielding and actual stand-by-stand partnership data are not fabricated.
