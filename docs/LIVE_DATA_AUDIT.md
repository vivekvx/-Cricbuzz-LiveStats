# Live API accuracy audit — 24 October 2026

The sampled provider data is genuine cricket data and the sampled match totals/results agree with public publisher/ICC listings. The original application had format and outcome-storage gaps; these are corrected in this revision. This is an evidence-based sample audit, not a claim that every live record or provider field has been independently verified.

## Scope and evidence

Ten bounded authenticated requests captured the live, recent and upcoming lists; three scorecards (T20I, ODI and Test); one match-information response; and Axar Patel's profile, batting career and bowling career tables. No credentials or request headers are included in committed audit artifacts. No API key was printed.

The captured lists contained **9 live-category entries, 78 recent entries and 4 upcoming entries**, representing **86 unique matches**. The provider's live category included completed matches; the app preserves the actual provider status rather than labeling every returned record ongoing.

An isolated temporary SQLite database imported those lists and the three scorecards: **66 players, seven innings, 62 batting performances and 44 bowling rows**. Re-importing each scorecard left row counts unchanged. **268 checks passed**, including:

- Exact imported team IDs, dates, formats and states for every captured list entry.
- Batting runs plus extras equal the innings total for all seven innings.
- Bowler legal balls sum to innings legal balls for all seven innings.
- Bowler runs conceded plus byes/leg-byes/penalties equal the innings total.
- Dismissal counts equal wicket totals; active/not-out batters are not dismissed, and did-not-bat players are participants rather than zero-run batting performances.
- Stored batting and bowling values match the captured payloads.
- Dataset career runs, dismissal-based averages, strike rates, wickets, bowling averages and economies agree with independent arithmetic.
- Fetched API career cells are preserved verbatim, separately from scorecard-derived totals.
- All 25 SQL statements execute on the isolated real-data database. Their full mathematical expected-answer tests remain in the automated suite, rather than being inferred from execution alone.
- Temporary player create/read/update/delete operations persist; no actual hosted user/player records were changed by this database audit. Foreign-key checks pass.

Machine-readable evidence: `live_audit_results.json`. To repeat the offline checks on the privately saved original responses, use `python scripts/audit_captured.py /path/to/captured-responses`. Minimal captured regression examples are under tests/fixtures/audited_scorecards.json with provenance. Live API calls are not made by the automated suite.

## External score/result cross-checks

| Match | API score/result | Public corroboration |
|---|---|---|
| NZ–India, 2nd T20I, ID 161201 | NZ 180/5 in 20 overs; India 181/6 in 19.5; India won by four wickets | [Cricbuzz score listing](https://www.cricbuzz.com/live-cricket-scores/161201/vs-india-2026-10-24-hagley-oval) |
| Sri Lanka–England, 3rd ODI, ID 170727 | England 429/4; Sri Lanka 430/8 in 49.5; Sri Lanka won by two wickets | [ICC match](https://www.icc-cricket.com/matches/274144/sri-lanka-vs-england), [ICC report](https://www.icc-cricket.com/news/sri-lanka-pull-off-a-monumental-odi-chase-against-england) |
| South Africa–Australia, 2nd Test, ID 147931 | SA 425/9 declared; Australia 99 and 295; SA won by an innings and 31 runs | [ICC WTC match](https://www.icc-cricket.com/tournaments/world-test-championship/matches/269791/south-africa-vs-australia), [Cricbuzz scorecard](https://www.cricbuzz.com/live-cricket-scorecard/147931/rsa-vs-aus-2nd-test-australia-tour-of-south-africa-2026) |

These cross-checks used indexed public score/report content. Direct retrieval of some publisher pages was unavailable, and search indexes can lag. All seven innings passed internal scorecard arithmetic; individual values for every player were not separately cross-checked against an independent publisher.

Axar's API Test runs (688) and ODI runs (918) agree with the [public Cricbuzz profile](https://www.cricbuzz.com/profiles/8808/axar). Its indexed T20 career figure was older than the authenticated response, so it cannot independently validate the current T20 total. The captured API ODI strike rate is **92.27**, while 918 runs from 995 balls gives **92.2613**, normally rounded to 92.26. This one-hundredth discrepancy belongs to the provider table. The raw API table is displayed as supplied; scorecard leaderboards compute their own rates. No source value is silently corrected or represented as independently exact.

## Defects corrected

1. **International format contamination.** The provider uses TEST/ODI labels for domestic first-class/one-day matches as well as internationals. Domestic TEST/ODI, unofficial Tests and warm-ups now map to Other. Only confirmed International T20 groups become T20I; domestic/league T20 remains T20. Women-group formats lacking explicit international context are conservatively unclassified for ODI/Test rather than guessed. Q11/Q20 exclude unclassified Other matches from their international-format comparison/eligibility. Existing live rows are repaired from saved provider snapshots by an idempotent migration.
2. **Outcome text was not persisted.** Explicit provider strings such as “India won by 4 wkts” now populate winner/margin/method. Outcomes are never calculated from team scores. Unknown/unrecognized results remain NULL on new records; incomplete refreshes preserve previously confirmed outcomes. Explicit drawn/tied/abandoned corrections clear a prior winner. Cached live/upcoming lists cannot downgrade a completed match. The first recorded innings supplies batting-first identity. Close-match queries exclude innings victories because their method is stored as innings, not an ordinary runs victory.
3. **Schedule updates.** Repeat list imports now update changed match dates and team IDs rather than retaining an old fixture schedule.
4. **Freshness ambiguity.** Match-list and scorecard fetch times are shown separately from provider update times. Live snapshots older than 15 minutes warn the viewer; absent timestamps are labeled unverifiable. Lists and scorecards are separate snapshots and can differ by deliveries or status until refreshed. Manual refresh does not promise continuous real-time updates.
5. **Missing-data interpretation.** Live SQL warns when capacities, countries, outcomes, toss or fielding data are unavailable. Missing fielding is not presented as evidence of a complete overall ranking. Leaderboards explicitly describe imported scorecards, not worldwide or full-career rankings.
6. **Legacy DNB rows and unknown roles.** Legacy scorecards now exclude did-not-bat entries just like current cards. Unknown player roles remain selectable as Unknown during editing, rather than silently defaulting to Batsman.

7. **Hosted chart crash.** The deployed app uses Python 3.14. The player chart now uses a direct Vega-Lite specification to avoid an Altair schema-import failure observed in the hosted browser. CI covers both Python 3.11 and 3.14.

## Limits that remain

Toss histories, fielding histories, complete represented-country metadata, series schedules and venue capacities are not automatically imported by the current UI. The captured match-information endpoint contained useful venue country/capacity fields; those are not yet an implemented enrichment flow. This is an adapter-coverage limit, not proof that the provider lacks the data. Queries requiring those fields can be incomplete and now disclose that fact.

The app is a manually refreshed snapshot application. Provider delays, independently cached endpoints and older browser/database snapshots can differ. A successful HTTP response proves delivery, not global accuracy or unlimited historical completeness. For an assignment demo, show Live API for actual imported matches/scorecards, and clearly labeled Sample Data for the full 25-question historical exercise.
