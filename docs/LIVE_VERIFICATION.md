# Authenticated API verification — 24 October 2026

The user supplied a RapidAPI key through their screenshot. It was extracted locally into `.env` with owner-only permissions; its value was never printed and is excluded from Git and the submission ZIP.

The following paths on `cricbuzz-cricket.p.rapidapi.com` returned successful authenticated JSON:

- `/matches/v1/live`: eight provider-listed matches, including Test, ODI and T20I records. The list can also include completed matches; their provider states are retained.
- `/mcenter/v1/161201/scard`: the current response uses lowercase `scorecard`, `inningsid`, `batsman` and `bowler` fields rather than legacy `scoreCard`. The normalizer now supports both observed structures.
- `/stats/v1/player/9443`: player profile; provider role `WK-Batsman` maps to Wicket-keeper and missing bowling style remains Unknown.
- `/stats/v1/player/9443/batting` and `/stats/v1/player/9443/bowling`: provider career tables, stored separately from match-derived statistics. Original provider format labels are retained in these snapshots; the provider uses a T20 column alongside IPL, so do not interpret that snapshot label as a guaranteed domestic-only category.

The current scorecard stored two innings, 15 actual batting-performance rows and 12 bowling rows. Did-not-bat squad members remain participants without becoming zero-run batting performances. Active batters marked `batting` are not counted as dismissed. Team IDs are resolved strictly against the two stored match-team names. The recorded innings dismissal totals agree with their five/six wickets. Re-import is idempotent and foreign-key checks pass.

The provider's match-list notation can use `.6` for an over-end delivery; the display canonicalizes e.g. 19.6 to 20.0 while keeping legal-ball storage. List and scorecard requests are separate snapshots and may differ by a delivery; each saved payload has its own fetch timestamp.

The API portal screenshot selects v2, but authenticated requests using the existing wire paths succeeded. This establishes the specific paths above; it does not establish universal v1/v2 equivalence. Series/venue standalone requests, exact plan limits, bulk history and archive pagination were not exercised. A successful response verifies provider delivery, not independent accuracy or latency of its sports feed.

The in-app browser was switched to Live API and visibly rendered provider teams, scores and stored scorecards. `live_api_verified.png` records that state. No credential appears in it. The original demonstration video remains a labeled synthetic-data walkthrough.
