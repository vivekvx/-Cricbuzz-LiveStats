# Relational schema

SQLite is the assignment's default: Python includes its connector, setup requires no service or credentials, and modern SQLite supports CTEs/window functions. SQL is intentionally SQLite-specific; the connection factory is centralized in `database/connection.py` and re-exported at the assignment's `utils/db_connection.py`. Porting to PostgreSQL/MySQL requires translating dates, booleans and aggregates, not just changing a connector.

`database/schema.sql` is authoritative. Initialization runs CREATE IF NOT EXISTS statements and records schema_version=1. There are no destructive startup migrations.

| Table | Grain and relationships |
|---|---|
| teams | One team; unique name, represented country, source |
| players | One player; unique case-insensitive full name; nullable unique provider ID; country, role, styles and source |
| venues | One venue; unique name/city; nullable nonnegative capacity |
| series | One series; host, format, start date and planned match count |
| matches | One match; two distinct team FKs, venue/series FKs, winner/toss/batting-first FKs restricted to the participating teams |
| participants | One player per match with team FK; authoritative match appearance grain |
| innings | One numbered innings per match, batting team, totals, wickets and legal balls |
| batting | One batter per innings; unique batting position; runs, balls and dismissal flag |
| bowling | One bowler per innings; aggregated legal balls, runs conceded and wickets |
| fielding | One player-match; catches and stumpings, aggregated before score joins |
| player_career_stats | One player-format-discipline API snapshot; JSON preserves provider table fields |
| api_snapshots | One last successful payload per endpoint with source and UTC fetch time |
| metadata | Schema version, seed version and demo reference date |

The scorecard relations are normalized; raw snapshots are an explicit provenance boundary rather than duplicated statistical facts. Player countries describe representation, not birthplace. Domestic teams do not imply a national country. Unknown provider fields stay unknown. No partnership fact table is created because the assignment's adjacent-position proxy is computed in Q13/Q24; an actual stand is a different fact and would need its own source.

`batting_facts` and `bowling_facts` join innings and match metadata once. `career` includes player/format pairs from participants and fielding even if no batting or bowling record exists. It preaggregates batting, bowling, fielding and participant appearances independently before joining, avoiding multiplication between disciplines. It describes the stored dataset's career coverage. API career snapshots remain separate from this view.

All connections enable foreign keys. Match deletion cascades to dependent innings, participants and fielding. Player deletion is restricted while dependent performance/participation/career rows exist. Statistics CRUD verifies the player belongs to the correct side. Integer checks reject negative counts and invalid wickets/positions. Repository mutations bind parameters. Provider updates use primary-key upserts, not duplicate inserts. Ingestion is transactional, validates complete response structure first, and rejects seeded databases. IDs are local integers; external player IDs have a separate unique column.

Match dates use ISO YYYY-MM-DD; API milliseconds are interpreted in UTC. UI reference dates use an explicit date picker. Overs are stored as **legal balls**: 4.2 overs means 26 balls, never 4.2 decimal overs. Strike rate = 100*runs/balls; batting average = runs/dismissals; economy = 6*conceded/legal balls; bowling average = conceded/wickets. Undefined denominators yield NULL. `stddev_pop` is a registered SQLite aggregate using Welford's stable population variance; all app connections register it.

Indexes cover match date/format, batter, bowler and innings match. SQLite constraints are complemented by repository validation; direct external database writers must preserve participant-side consistency. Names are unique for simple academic duplicate prevention; real production systems would distinguish players sharing a name.

Sample and live modes use separate database files. Manual changes have `source=manual`; seed records use `synthetic-v1`; provider records use `rapidapi-cricbuzz-v1`. The seed marker prevents repeated loading or resurrection of intentionally deleted records. To reset sample data explicitly, stop the app, remove only data/sample.sqlite3, and run the seed module again.
