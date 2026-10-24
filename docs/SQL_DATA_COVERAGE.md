# SQL data coverage investigation — 24 October 2026

The user reported identical empty results for Q9 and Q16 in Live API mode. This was reproduced. The generic message hid a data-coverage gap; a functioning live API and passing SQL calculation tests did not establish that the deployed database contained enough historical data for every question.

## Hosted evidence before the fix

A read-only query through the deployed SQL workspace returned 9 listed matches, 22 players, one match with imported innings, 15 batting rows and a maximum of one participant appearance per player. The three-format audit in LIVE_DATA_AUDIT.md used an isolated temporary database; those 86 matches and seven innings were not the hosted database.

Q9 requires a recognized all-rounder with more than 1,000 runs and more than 50 wickets in one format. Its `career` view sums imported scorecards. Fetched API career tables are separate and do not satisfy that query. This means the current live result cannot answer the full real-world career question.

Q16 requires five appearances for one player in a year. With one imported match per player, an empty result is expected. Listing fixtures does not create participant appearances or batting/bowling rows.

## All-question local reproduction

The local live database had eight listed matches and the same one-scorecard coverage. The table below records actual execution, not inferred availability. Reference date: 2026-10-24. Machine-readable results: `sql_coverage_results.json`.

| Question | Local live rows | Sample rows |
|---|---:|---:|
| Q1 | 0 | 4 |
| Q2 | 8 | 6 |
| Q3 | 0 | 8 |
| Q4 | 0 | 1 |
| Q5 | 16 | 2 |
| Q6 | 2 | 4 |
| Q7 | 1 | 3 |
| Q8 | 0 | 1 |
| Q9 | 0 | 6 |
| Q10 | 2 | 20 |
| Q11 | 0 | 8 |
| Q12 | 0 | 4 |
| Q13 | 1 | 348 |
| Q14 | 0 | 12 |
| Q15 | 0 | 8 |
| Q16 | 0 | 24 |
| Q17 | 0 | 2 |
| Q18 | 0 | 4 |
| Q19 | 7 | 8 |
| Q20 | 0 | 8 |
| Q21 | 22 | 24 |
| Q22 | 0 | 12 |
| Q23 | 15 | 8 |
| Q24 | 0 | 6 |
| Q25 | 0 | 80 |

15 of 25 local live queries returned no rows; zero SQL statements failed. All 25 sample queries returned rows. Empty results do not prove no real player/match qualifies. Nonempty results do not prove complete history, either.

## UI correction and verification

- Show listed matches, matches with scorecards and batting rows before selecting a question.
- Explain the ingestion gap and provide an explicit switch to clearly labeled fictional sample data for the complete assignment demonstration.
- Replace the shared empty message with the selected question’s requirements and imported-data counts. Q9 adds measured all-rounder counts and maxima; Q16 adds the maximum eligible yearly appearances.
- Add a no-network check of all 25 queries with distinct Has results, No qualifying rows and Query failed states.
- Preserve all assignment thresholds and physical separation of real and sample databases.
- Five regression tests cover the one-scorecard scenario, different Q9/Q16 evidence, all 25 sample results, query errors, UI source switching and the all-question check. Full suite: 118 passed locally.

A complete real-history ingestion pipeline remains required for all 25 questions to have meaningful real-world answers. This change makes the limitation inspectable; it does not manufacture historical records or claim that fixture listings are full scorecards.
