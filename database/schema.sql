PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS teams(id INTEGER PRIMARY KEY,name TEXT NOT NULL UNIQUE,country TEXT NOT NULL,source TEXT NOT NULL DEFAULT 'manual');
CREATE TABLE IF NOT EXISTS players(
 id INTEGER PRIMARY KEY,full_name TEXT NOT NULL COLLATE NOCASE UNIQUE,country TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('Batsman','Bowler','All-rounder','Wicket-keeper','Unknown')),
 batting_style TEXT NOT NULL,bowling_style TEXT NOT NULL,source TEXT NOT NULL DEFAULT 'manual',external_id INTEGER UNIQUE);
CREATE TABLE IF NOT EXISTS venues(id INTEGER PRIMARY KEY,name TEXT NOT NULL,city TEXT NOT NULL,country TEXT NOT NULL,capacity INTEGER CHECK(capacity>=0),source TEXT NOT NULL,UNIQUE(name,city));
CREATE TABLE IF NOT EXISTS series(id INTEGER PRIMARY KEY,name TEXT NOT NULL,host_country TEXT,format TEXT CHECK(format IN ('Test','ODI','T20I','T20','Other')),start_date TEXT NOT NULL,planned_matches INTEGER CHECK(planned_matches>=0),source TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS matches(
 id INTEGER PRIMARY KEY,description TEXT NOT NULL,team1_id INTEGER NOT NULL REFERENCES teams,
 team2_id INTEGER NOT NULL REFERENCES teams,venue_id INTEGER REFERENCES venues,series_id INTEGER REFERENCES series,
 match_date TEXT NOT NULL,format TEXT NOT NULL CHECK(format IN ('Test','ODI','T20I','T20','Other')),
 status TEXT NOT NULL CHECK(status IN ('Complete','Live','Upcoming','Abandoned')),status_text TEXT,
 winner_id INTEGER REFERENCES teams,margin INTEGER CHECK(margin>=0),victory_type TEXT CHECK(victory_type IN ('runs','wickets','innings','tie')),
 toss_winner_id INTEGER REFERENCES teams,toss_decision TEXT CHECK(toss_decision IN ('bat','bowl')),
 batting_first_id INTEGER REFERENCES teams,source TEXT NOT NULL,
 CHECK(team1_id<>team2_id),CHECK(winner_id IS NULL OR winner_id IN(team1_id,team2_id)),
 CHECK(toss_winner_id IS NULL OR toss_winner_id IN(team1_id,team2_id)),
 CHECK(batting_first_id IS NULL OR batting_first_id IN(team1_id,team2_id)));
CREATE TABLE IF NOT EXISTS participants(match_id INTEGER REFERENCES matches ON DELETE CASCADE,player_id INTEGER REFERENCES players ON DELETE RESTRICT,team_id INTEGER NOT NULL REFERENCES teams,PRIMARY KEY(match_id,player_id));
CREATE TABLE IF NOT EXISTS innings(id INTEGER PRIMARY KEY,match_id INTEGER NOT NULL REFERENCES matches ON DELETE CASCADE,number INTEGER NOT NULL CHECK(number BETWEEN 1 AND 4),team_id INTEGER NOT NULL REFERENCES teams,total_runs INTEGER CHECK(total_runs>=0),wickets INTEGER CHECK(wickets BETWEEN 0 AND 10),balls INTEGER CHECK(balls>=0),UNIQUE(match_id,number));
CREATE TABLE IF NOT EXISTS batting(innings_id INTEGER REFERENCES innings ON DELETE CASCADE,player_id INTEGER REFERENCES players ON DELETE RESTRICT,position INTEGER NOT NULL CHECK(position BETWEEN 1 AND 11),runs INTEGER NOT NULL CHECK(runs>=0),balls INTEGER NOT NULL CHECK(balls>=0),dismissed INTEGER NOT NULL CHECK(dismissed IN(0,1)),PRIMARY KEY(innings_id,player_id),UNIQUE(innings_id,position));
CREATE TABLE IF NOT EXISTS bowling(innings_id INTEGER REFERENCES innings ON DELETE CASCADE,player_id INTEGER REFERENCES players ON DELETE RESTRICT,balls INTEGER NOT NULL CHECK(balls>=0),runs INTEGER NOT NULL CHECK(runs>=0),wickets INTEGER NOT NULL CHECK(wickets BETWEEN 0 AND 10),PRIMARY KEY(innings_id,player_id));
CREATE TABLE IF NOT EXISTS fielding(match_id INTEGER REFERENCES matches ON DELETE CASCADE,player_id INTEGER REFERENCES players ON DELETE RESTRICT,catches INTEGER NOT NULL CHECK(catches>=0),stumpings INTEGER NOT NULL CHECK(stumpings>=0),PRIMARY KEY(match_id,player_id));
CREATE TABLE IF NOT EXISTS player_career_stats(player_id INTEGER REFERENCES players ON DELETE RESTRICT,format TEXT NOT NULL,discipline TEXT NOT NULL CHECK(discipline IN ('batting','bowling')),payload TEXT NOT NULL,fetched_at TEXT NOT NULL,source TEXT NOT NULL,PRIMARY KEY(player_id,format,discipline));
CREATE TABLE IF NOT EXISTS api_snapshots(endpoint TEXT PRIMARY KEY,payload TEXT NOT NULL,fetched_at TEXT NOT NULL,source TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date,format);
CREATE INDEX IF NOT EXISTS idx_batting_player ON batting(player_id);
CREATE INDEX IF NOT EXISTS idx_bowling_player ON bowling(player_id);
CREATE INDEX IF NOT EXISTS idx_innings_match ON innings(match_id);
CREATE VIEW IF NOT EXISTS batting_facts AS
 SELECT b.*,i.match_id,i.team_id,i.number,m.format,m.match_date,m.venue_id,m.winner_id,m.margin,m.victory_type,
 100.0*b.runs/NULLIF(b.balls,0) AS strike_rate
 FROM batting b JOIN innings i ON i.id=b.innings_id JOIN matches m ON m.id=i.match_id;
CREATE VIEW IF NOT EXISTS bowling_facts AS
 SELECT b.*,i.match_id,m.format,m.venue_id,m.match_date,6.0*b.runs/NULLIF(b.balls,0) AS economy
 FROM bowling b JOIN innings i ON i.id=b.innings_id JOIN matches m ON m.id=i.match_id;
CREATE VIEW IF NOT EXISTS career AS
 WITH formats AS (SELECT DISTINCT player_id,format FROM batting_facts UNION SELECT DISTINCT player_id,format FROM bowling_facts
 UNION SELECT DISTINCT f.player_id,m.format FROM fielding f JOIN matches m ON m.id=f.match_id
 UNION SELECT DISTINCT p.player_id,m.format FROM participants p JOIN matches m ON m.id=p.match_id),
 bat AS (SELECT player_id,format,SUM(runs) runs,SUM(balls) balls,SUM(dismissed) dismissals,SUM(runs>=100) centuries,MAX(runs) highest FROM batting_facts GROUP BY player_id,format),
 bowl AS (SELECT player_id,format,SUM(wickets) wickets,SUM(runs) conceded,SUM(balls) bowled_balls FROM bowling_facts GROUP BY player_id,format),
 field AS (SELECT f.player_id,m.format,SUM(catches) catches,SUM(stumpings) stumpings FROM fielding f JOIN matches m ON m.id=f.match_id GROUP BY player_id,m.format),
 apps AS (SELECT p.player_id,m.format,COUNT(*) matches FROM participants p JOIN matches m ON m.id=p.match_id GROUP BY p.player_id,m.format)
 SELECT f.player_id,f.format,COALESCE(a.matches,0) matches,b.runs,b.balls,b.dismissals,b.centuries,b.highest,
 1.0*b.runs/NULLIF(b.dismissals,0) batting_average,100.0*b.runs/NULLIF(b.balls,0) strike_rate,
 w.wickets,w.conceded,w.bowled_balls,1.0*w.conceded/NULLIF(w.wickets,0) bowling_average,
 6.0*w.conceded/NULLIF(w.bowled_balls,0) economy,COALESCE(d.catches,0) catches,COALESCE(d.stumpings,0) stumpings
 FROM formats f LEFT JOIN bat b USING(player_id,format) LEFT JOIN bowl w USING(player_id,format) LEFT JOIN field d USING(player_id,format) LEFT JOIN apps a USING(player_id,format);
