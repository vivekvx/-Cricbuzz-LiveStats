# All 25 SQL solutions

Dialect: SQLite. Bind :as_of to an ISO date. The stddev_pop aggregate is registered by database/connection.py.

## Shared assumptions

Dataset career totals cover stored scorecards only, not necessarily a complete real career.
All divisions guard zero denominators; an undismissed batter has an undefined (NULL) average.
Formats Test, ODI, T20I and domestic T20 remain distinct; Q18 and Q20 explicitly combine T20I/T20.
Domestic TEST/ODI and unofficial/warm-up games are classified Other, rather than misrepresented as international Tests/ODIs.
Q11 uses Test/ODI/T20I only; Q20 eligibility uses those plus domestic T20, excluding unclassified Other games.
Q13/Q24 use adjacent batting-position combined-score proxies, never actual partnership runs.
Q17 excludes no-result/tie matches with no winner. Q19 uses population standard deviation and >=10 balls per eligible innings.
Q21 missing disciplines and undefined average terms contribute zero; no 25-point bowling bonus is awarded to non-bowlers.
Q23 Excellent: last5 mean >=50, >=last10 mean, last5 SR >=last10 SR, population SD <=30, >=3 scores >50;
otherwise Good >=35, Average >=20, Poor <20. Fewer than ten batting matches are reported with their count; fifty-plus here means >50 per the source document.
Q25 improving/declining means a change strictly above +5/below -5 runs; otherwise stable.
Career ascending/declining means final minus first qualifying quarter strictly above +10/below -10 runs; otherwise stable.
Q23 averages/stddev use match runs (both Test innings combined); fifty-plus counts still refer to individual innings.
Q25 uses a trailing three-year window ending at :as_of. DNB appearances count as matches with zero runs and undefined strike rate.
Quarter changes across missing/nonqualifying quarters are NULL and explicitly marked as a gap.
Sample date windows use a visible 2026-10-24 reference date; live mode defaults to today's local date.


## Q1 — Beginner

Find all players who represent India. Display their full name, playing role, batting style, and bowling style.

```sql
SELECT full_name,role AS playing_role,batting_style,bowling_style FROM players WHERE country='India' ORDER BY full_name;
```

Filter the represented country and project player attributes.

## Q2 — Beginner

Show all cricket matches that were played in the last 30 days. Include the match description, both team names, venue name with city, and the match date. Sort by most recent matches first.

```sql
SELECT m.description,t1.name team1,t2.name team2,v.name venue,v.city,m.match_date
FROM matches m JOIN teams t1 ON t1.id=m.team1_id JOIN teams t2 ON t2.id=m.team2_id
LEFT JOIN venues v ON v.id=m.venue_id
WHERE m.match_date>=date(:as_of,'-30 days') AND m.match_date<=:as_of
AND m.status IN ('Complete','Live') ORDER BY m.match_date DESC,m.id DESC;
```

Join teams and venues; use a bounded 30-day date window.

## Q3 — Beginner

List the top 10 highest run scorers in ODI cricket. Show player name, total runs scored, batting average, and number of centuries. Display the highest run scorer first.

```sql
SELECT p.full_name,c.runs career_runs,c.batting_average,c.centuries FROM career c JOIN players p ON p.id=c.player_id
WHERE c.format='ODI' AND c.runs IS NOT NULL ORDER BY c.runs DESC,p.id LIMIT 10;
```

Aggregate stored scorecards into career ODI totals and order by runs.

## Q4 — Beginner

Display all cricket venues that have a seating capacity of more than 50,000 spectators. Show venue name, city, country, and capacity. Order by largest capacity first.

```sql
SELECT name,city,country,capacity FROM venues WHERE capacity>50000 ORDER BY capacity DESC,name;
```

Apply the strict capacity threshold; unknown capacities are excluded.

## Q5 — Beginner

Calculate how many matches each team has won. Show team name and total number of wins. Display teams with most wins first.

```sql
SELECT t.name,COUNT(m.id) wins FROM teams t LEFT JOIN matches m ON m.winner_id=t.id AND m.status='Complete'
GROUP BY t.id ORDER BY wins DESC,t.name;
```

Left join completed winners so teams with zero wins remain visible.

## Q6 — Beginner

Count how many players belong to each playing role (like Batsman, Bowler, All-rounder, Wicket-keeper). Show the role and count of players for each role.

```sql
SELECT role,COUNT(*) players FROM players GROUP BY role ORDER BY role;
```

Group the unique player dimension by role.

## Q7 — Beginner

Find the highest individual batting score achieved in each cricket format (Test, ODI, T20I). Display the format and the highest score for that format.

```sql
SELECT format,MAX(runs) highest_score FROM batting_facts WHERE format IN ('Test','ODI','T20I') GROUP BY format ORDER BY format;
```

Take the maximum innings score per international format.

## Q8 — Beginner

Show all cricket series that started in the year 2024. Include series name, host country, match type, start date, and total number of matches planned.

```sql
SELECT name,host_country,format,start_date,planned_matches FROM series
WHERE start_date>='2024-01-01' AND start_date<'2025-01-01' ORDER BY start_date,name;
```

Use a half-open 2024 start-date interval.

## Q9 — Intermediate

Find all-rounder players who have scored more than 1000 runs AND taken more than 50 wickets in their career. Display player name, total runs, total wickets, and the cricket format.

```sql
SELECT p.full_name,c.runs,c.wickets,c.format FROM career c JOIN players p ON p.id=c.player_id
WHERE p.role='All-rounder' AND c.runs>1000 AND c.wickets>50 ORDER BY c.format,c.runs DESC,p.id;
```

Filter all-rounders and apply both strict career thresholds per format.

## Q10 — Intermediate

Get details of the last 20 completed matches. Show match description, both team names, winning team, victory margin, victory type (runs/wickets), and venue name. Display most recent matches first.

```sql
SELECT m.description,t1.name team1,t2.name team2,w.name winner,m.margin,m.victory_type,v.name venue,m.match_date
FROM matches m JOIN teams t1 ON t1.id=m.team1_id JOIN teams t2 ON t2.id=m.team2_id
LEFT JOIN teams w ON w.id=m.winner_id LEFT JOIN venues v ON v.id=m.venue_id
WHERE m.status='Complete' ORDER BY m.match_date DESC,m.id DESC LIMIT 20;
```

Join completed match metadata and return the 20 most recent.

## Q11 — Intermediate

Compare each player's performance across different cricket formats. For players who have played at least 2 different formats, show their total runs in Test cricket, ODI cricket, and T20I cricket, along with their overall batting average across all formats.

```sql
SELECT p.full_name,SUM(CASE WHEN c.format='Test' THEN COALESCE(c.runs,0) ELSE 0 END) test_runs,
SUM(CASE WHEN c.format='ODI' THEN COALESCE(c.runs,0) ELSE 0 END) odi_runs,
SUM(CASE WHEN c.format='T20I' THEN COALESCE(c.runs,0) ELSE 0 END) t20i_runs,
1.0*SUM(c.runs)/NULLIF(SUM(c.dismissals),0) overall_batting_average
FROM career c JOIN players p ON p.id=c.player_id WHERE c.matches>0 AND c.format IN ('Test','ODI','T20I')
GROUP BY p.id HAVING COUNT(DISTINCT c.format)>=2 ORDER BY p.full_name;
```

Pivot format totals; overall average is total runs divided by dismissals.

## Q12 — Intermediate

Analyze each international team's performance when playing at home versus playing away. Determine whether each team played at home or away based on whether the venue country matches the team's country. Count wins for each team in both home and away conditions.

```sql
WITH appearances AS (
 SELECT id match_id,team1_id team_id,venue_id,winner_id FROM matches WHERE status='Complete'
 UNION ALL
 SELECT id,team2_id,venue_id,winner_id FROM matches WHERE status='Complete'),
 results AS (
 SELECT a.team_id,CASE WHEN v.country=t.country THEN 'Home' ELSE 'Away' END conditions,
 COUNT(*) matches,SUM(CASE WHEN a.winner_id=a.team_id THEN 1 ELSE 0 END) wins
 FROM appearances a JOIN teams t ON t.id=a.team_id JOIN venues v ON v.id=a.venue_id
 WHERE v.country<>'Unknown' AND t.country<>'Unknown'
 GROUP BY a.team_id,conditions),
 conditions AS (SELECT 'Home' conditions UNION ALL SELECT 'Away')
SELECT t.name,c.conditions,COALESCE(r.matches,0) matches,COALESCE(r.wins,0) wins
FROM teams t CROSS JOIN conditions c
LEFT JOIN results r ON r.team_id=t.id AND r.conditions=c.conditions
WHERE t.id IN (SELECT team_id FROM results)
ORDER BY t.name,c.conditions;
```

Compare venue and team countries using team appearances; retain zero-win teams and both Home/Away rows. Neutral venues count as away.

## Q13 — Intermediate

Identify batting partnerships where two consecutive batsmen (batting positions next to each other) scored a combined total of 100 or more runs in the same innings. Show both player names, their combined partnership runs, and which innings it occurred in.

```sql
SELECT p.full_name batter1,q.full_name batter2,a.runs+b.runs combined_runs,a.match_id,a.number innings_number,
'Consecutive-position proxy; not actual stand' measure
FROM batting_facts a JOIN batting_facts b ON a.innings_id=b.innings_id AND b.position=a.position+1
JOIN players p ON p.id=a.player_id JOIN players q ON q.id=b.player_id
WHERE a.runs+b.runs>=100 ORDER BY combined_runs DESC,a.innings_id,a.position;
```

Self join adjacent positions in one innings. Combined scores are a proxy, not verified partnerships.

## Q14 — Intermediate

Examine bowling performance at different venues. For bowlers who have played at least 3 matches at the same venue, calculate their average economy rate, total wickets taken, and number of matches played at each venue. Focus on bowlers who bowled at least 4 overs in each match.

```sql
WITH appearances AS (
 SELECT player_id,venue_id,match_id,SUM(balls) balls,SUM(runs) runs,SUM(wickets) wickets
 FROM bowling_facts GROUP BY player_id,venue_id,match_id HAVING SUM(balls)>=24)
SELECT p.full_name,v.name venue,AVG(6.0*a.runs/NULLIF(a.balls,0)) average_economy,
SUM(a.wickets) wickets,COUNT(*) matches FROM appearances a JOIN players p ON p.id=a.player_id
JOIN venues v ON v.id=a.venue_id GROUP BY a.player_id,a.venue_id HAVING COUNT(*)>=3
ORDER BY p.full_name,v.name;
```

Aggregate spells to match appearances, require 24 legal balls per appearance, then at least three matches per venue.

## Q15 — Intermediate

Identify players who perform exceptionally well in close matches. A close match is defined as one decided by less than 50 runs OR less than 5 wickets. For these close matches, calculate each player's average runs scored, total close matches played, and how many of those close matches their team won when they batted.

```sql
WITH per_match AS (
 SELECT player_id,match_id,SUM(runs) runs,MAX(team_id=winner_id) won FROM batting_facts
 WHERE (victory_type='runs' AND margin<50) OR (victory_type='wickets' AND margin<5)
 GROUP BY player_id,match_id)
SELECT p.full_name,AVG(a.runs) average_runs,COUNT(*) close_matches,SUM(a.won) team_wins
FROM per_match a JOIN players p ON p.id=a.player_id GROUP BY p.id ORDER BY average_runs DESC,p.id;
```

Apply victory-method-specific margins; aggregate innings to player-match before averaging or counting wins.

## Q16 — Intermediate

Track how players' batting performance changes over different years. For matches since 2020, show each player's average runs per match and average strike rate for each year. Only include players who played at least 5 matches in that year.

```sql
WITH eligible_matches AS (
 SELECT id,match_date FROM matches WHERE match_date>='2020-01-01' AND status<>'Upcoming'),
 appearances AS (
 SELECT a.player_id,strftime('%Y',m.match_date) year,COUNT(*) matches
 FROM participants a JOIN eligible_matches m ON m.id=a.match_id
 GROUP BY a.player_id,year HAVING COUNT(*)>=5),
 batting_by_year AS (
 SELECT b.player_id,strftime('%Y',m.match_date) year,SUM(b.runs) runs,AVG(b.strike_rate) average_strike_rate
 FROM batting_facts b JOIN eligible_matches m ON m.id=b.match_id
 GROUP BY b.player_id,year)
SELECT p.full_name,a.year,1.0*COALESCE(b.runs,0)/a.matches average_runs_per_match,
b.average_strike_rate,a.matches
FROM appearances a JOIN players p ON p.id=a.player_id
LEFT JOIN batting_by_year b ON b.player_id=a.player_id AND b.year=a.year
ORDER BY p.full_name,a.year;
```

Count participant appearances for yearly eligibility and runs-per-match denominator; use the same non-upcoming match set for batting totals. Average strike rates over recorded batting innings.

## Q17 — Advanced

Investigate whether winning the toss gives teams an advantage in winning matches. Calculate what percentage of matches are won by the team that wins the toss, broken down by their toss decision (choosing to bat first or bowl first).

```sql
SELECT toss_decision,COUNT(*) matches,SUM(winner_id=toss_winner_id) toss_winner_wins,
100.0*SUM(winner_id=toss_winner_id)/COUNT(*) win_percentage
FROM matches WHERE status='Complete' AND winner_id IS NOT NULL AND toss_winner_id IS NOT NULL
AND toss_decision IS NOT NULL GROUP BY toss_decision ORDER BY toss_decision;
```

Measure completed decisive matches with known toss information; exclude ties and no-results from denominator.

## Q18 — Advanced

Find the most economical bowlers in limited-overs cricket (ODI and T20 formats). Calculate each bowler's overall economy rate and total wickets taken. Only consider bowlers who have bowled in at least 10 matches and bowled at least 2 overs per match on average.

```sql
SELECT p.full_name,COUNT(DISTINCT b.match_id) matches,6.0*SUM(b.runs)/NULLIF(SUM(b.balls),0) economy,
SUM(b.wickets) wickets,1.0*SUM(b.balls)/6/COUNT(DISTINCT b.match_id) overs_per_match
FROM bowling_facts b JOIN players p ON p.id=b.player_id WHERE b.format IN ('ODI','T20I','T20')
GROUP BY p.id HAVING COUNT(DISTINCT b.match_id)>=10 AND 1.0*SUM(b.balls)/COUNT(DISTINCT b.match_id)>=12
ORDER BY economy,p.id;
```

Combine ODI, T20I and domestic T20 spells; use six times runs conceded divided by legal balls.

## Q19 — Advanced

Determine which batsmen are most consistent in their scoring. Calculate the average runs scored and the standard deviation of runs for each player. Only include players who have faced at least 10 balls per innings and played since 2022. A lower standard deviation indicates more consistent performance.

```sql
SELECT p.full_name,AVG(b.runs) average_runs,stddev_pop(b.runs) standard_deviation,COUNT(*) innings
FROM batting_facts b JOIN players p ON p.id=b.player_id WHERE b.match_date>='2022-01-01' AND b.balls>=10
GROUP BY p.id ORDER BY standard_deviation,p.id;
```

Filter each innings to at least 10 balls since 2022; use population standard deviation.

## Q20 — Advanced

Analyze how many matches each player has played in different cricket formats and their batting average in each format. Show the count of Test matches, ODI matches, and T20 matches for each player, along with their respective batting averages. Only include players who have played at least 20 total matches across all formats.

```sql
WITH apps AS (
 SELECT a.player_id,COUNT(*) total_matches,
 SUM(m.format='Test') test_matches,SUM(m.format='ODI') odi_matches,SUM(m.format IN ('T20I','T20')) t20_matches
 FROM participants a JOIN matches m ON m.id=a.match_id WHERE m.format IN ('Test','ODI','T20I','T20') GROUP BY a.player_id HAVING COUNT(*)>=20),
 bat AS (SELECT player_id,
 1.0*SUM(CASE WHEN format='Test' THEN runs END)/NULLIF(SUM(CASE WHEN format='Test' THEN dismissed END),0) test_average,
 1.0*SUM(CASE WHEN format='ODI' THEN runs END)/NULLIF(SUM(CASE WHEN format='ODI' THEN dismissed END),0) odi_average,
 1.0*SUM(CASE WHEN format IN ('T20I','T20') THEN runs END)/NULLIF(SUM(CASE WHEN format IN ('T20I','T20') THEN dismissed END),0) t20_average
 FROM batting_facts GROUP BY player_id)
SELECT p.full_name,a.*,b.test_average,b.odi_average,b.t20_average FROM apps a JOIN players p ON p.id=a.player_id
LEFT JOIN bat b ON b.player_id=a.player_id ORDER BY p.full_name;
```

Count participant appearances separately from batting innings; pivot averages without multiplying match counts.

## Q21 — Advanced

Create a comprehensive performance ranking system for players. Combine their batting performance (runs scored, batting average, strike rate), bowling performance (wickets taken, bowling average, economy rate), and fielding performance (catches, stumpings) into a single weighted score. Use this formula and rank players:

Batting points: (runs_scored × 0.01) + (batting_average × 0.5) + (strike_rate × 0.3)

Bowling points: (wickets_taken × 2) + (50 - bowling_average) × 0.5) + ((6 - economy_rate) × 2)

Fielding points: (catches × 3) + (stumpings × 5)

Rank the top performers in each cricket format.

```sql
WITH points AS (
 SELECT c.*,COALESCE(runs*0.01,0)+COALESCE(batting_average*0.5,0)+COALESCE(strike_rate*0.3,0) batting_points,
 CASE WHEN bowled_balls>0 THEN COALESCE(wickets*2,0)+COALESCE((50-bowling_average)*0.5,0)+COALESCE((6-economy)*2,0) ELSE 0 END bowling_points,
 catches*3+stumpings*5 fielding_points FROM career c),
 scored AS (SELECT *,batting_points+bowling_points+fielding_points total_score FROM points)
SELECT p.full_name,s.format,s.batting_points,s.bowling_points,s.fielding_points,s.total_score,
DENSE_RANK() OVER(PARTITION BY s.format ORDER BY s.total_score DESC) rank
FROM scored s JOIN players p ON p.id=s.player_id ORDER BY s.format,rank,p.id;
```

Compute batting, bowling and fielding components separately, then dense rank within format. Missing components contribute zero; undefined average terms contribute zero.

## Q22 — Advanced

Build a head-to-head match prediction analysis between teams. For each pair of teams that have played at least 5 matches against each other in the last 3 years, calculate:

Total matches played between them

Wins for each team

Average victory margin when each team wins

Performance when batting first vs bowling first at different venues

Overall win percentage for each team in this head-to-head record

```sql
WITH recent AS (
 SELECT *,MIN(team1_id,team2_id) a,MAX(team1_id,team2_id) b FROM matches
 WHERE status='Complete' AND match_date>=date(:as_of,'-3 years') AND match_date<=:as_of),
 eligible AS (SELECT a,b,COUNT(*) meetings FROM recent GROUP BY a,b HAVING COUNT(*)>=5),
 sides AS (SELECT r.*,a team_id,b opponent_id FROM recent r UNION ALL SELECT r.*,b,a FROM recent r)
SELECT t.name team,o.name opponent,e.meetings pair_meetings,v.name venue,
CASE WHEN s.batting_first_id IS NULL THEN 'Unknown' WHEN s.team_id=s.batting_first_id THEN 'Batting first' ELSE 'Bowling first' END approach,
COUNT(*) matches,SUM(CASE WHEN s.winner_id=s.team_id THEN 1 ELSE 0 END) wins,
100.0*SUM(CASE WHEN s.winner_id=s.team_id THEN 1 ELSE 0 END)/COUNT(*) win_percentage,
AVG(CASE WHEN s.winner_id=s.team_id AND s.victory_type='runs' THEN s.margin END) average_winning_margin_runs,
AVG(CASE WHEN s.winner_id=s.team_id AND s.victory_type='wickets' THEN s.margin END) average_winning_margin_wickets,
(SELECT COUNT(*) FROM recent r2 WHERE r2.a=s.a AND r2.b=s.b AND r2.winner_id=s.team_id) overall_wins,
100.0*(SELECT COUNT(*) FROM recent r2 WHERE r2.a=s.a AND r2.b=s.b AND r2.winner_id=s.team_id)/e.meetings overall_win_percentage
FROM sides s JOIN eligible e ON e.a=s.a AND e.b=s.b JOIN teams t ON t.id=s.team_id
JOIN teams o ON o.id=s.opponent_id LEFT JOIN venues v ON v.id=s.venue_id
GROUP BY s.a,s.b,s.team_id,s.venue_id,approach ORDER BY t.name,o.name,v.name,approach;
```

Qualify canonical team pairs over three years, then report each team at venue/approach grain, with pair-wide win percentages. Run and wicket margins stay separate.

## Q23 — Advanced

Analyze recent player form and momentum. For each player's last 10 batting performances, calculate:

Average runs in their last 5 matches vs their last 10 matches

Recent strike rate trends

Number of scores above 50 in recent matches

A consistency score based on standard deviation

Based on these metrics, categorize players as being in "Excellent Form", "Good Form", "Average Form", or "Poor Form".

```sql
WITH per_match AS (
 SELECT player_id,match_id,match_date,SUM(runs) runs,
 100.0*SUM(runs)/NULLIF(SUM(balls),0) strike_rate,SUM(runs>50) scores_above50
 FROM batting_facts GROUP BY player_id,match_id),
 numbered AS (
 SELECT *,ROW_NUMBER() OVER(PARTITION BY player_id ORDER BY match_date DESC,match_id DESC) rn
 FROM per_match),
 form AS (SELECT player_id,AVG(CASE WHEN rn<=5 THEN runs END) last5_average,AVG(runs) last10_average,
 AVG(CASE WHEN rn<=5 THEN strike_rate END) last5_strike_rate,AVG(strike_rate) last10_strike_rate,
 SUM(scores_above50) scores_above50,stddev_pop(runs) standard_deviation,COUNT(*) performances
 FROM numbered WHERE rn<=10 GROUP BY player_id)
SELECT p.full_name,f.*,last5_strike_rate-last10_strike_rate strike_rate_trend,
CASE WHEN last5_average>=50 AND last5_average>=last10_average AND last5_strike_rate>=last10_strike_rate AND standard_deviation<=30 AND scores_above50>=3 THEN 'Excellent Form'
 WHEN last5_average>=35 THEN 'Good Form' WHEN last5_average>=20 THEN 'Average Form' ELSE 'Poor Form' END form_classification
FROM form f JOIN players p ON p.id=f.player_id ORDER BY last5_average DESC,p.id;
```

Aggregate Test innings into player-match totals before selecting the latest ten batting matches; compare last-five and last-ten match means, strike rates and consistency. Count individual fifty-plus innings within that window. Thresholds appear in assumptions.

## Q24 — Advanced

Study successful batting partnerships to identify the best player combinations. For pairs of players who have batted together as consecutive batsmen (positions differ by 1) in at least 5 partnerships:

Calculate their average partnership runs

Count how many of their partnerships exceeded 50 runs

Find their highest partnership score

Calculate their success rate (percentage of good partnerships)

Rank the most successful batting partnerships.

```sql
WITH pairs AS (
 SELECT MIN(a.player_id,b.player_id) p1,MAX(a.player_id,b.player_id) p2,a.runs+b.runs combined_runs
 FROM batting a JOIN batting b ON a.innings_id=b.innings_id AND b.position=a.position+1),
 summary AS (SELECT p1,p2,COUNT(*) partnerships,AVG(combined_runs) average_combined_runs,
 SUM(combined_runs>50) exceeding50,MAX(combined_runs) highest_score,100.0*SUM(combined_runs>50)/COUNT(*) success_percentage
 FROM pairs GROUP BY p1,p2 HAVING COUNT(*)>=5)
SELECT p.full_name batter1,q.full_name batter2,s.*,
DENSE_RANK() OVER(ORDER BY success_percentage DESC,average_combined_runs DESC) rank,
'Consecutive-position proxy; not actual stand' measure
FROM summary s JOIN players p ON p.id=s.p1 JOIN players q ON q.id=s.p2 ORDER BY rank,s.p1,s.p2;
```

Canonicalize adjacent-position pairs; rank success percentage then average combined runs. Proxy only.

## Q25 — Advanced

Perform a time-series analysis of player performance evolution. Track how each player's batting performance changes over time by:

Calculating quarterly averages for runs and strike rate

Comparing each quarter's performance to the previous quarter

Identifying whether performance is improving, declining, or stable

Determining overall career trajectory over the last few years

Categorizing players' career phase as "Career Ascending", "Career Declining", or "Career Stable"

Only analyze players with data spanning at least 6 quarters and a minimum of 3 matches per quarter.

```sql
WITH per_match AS (
 SELECT a.player_id,a.match_id,m.match_date,COALESCE(SUM(b.runs),0) runs,
 100.0*SUM(b.runs)/NULLIF(SUM(b.balls),0) sr
 FROM participants a JOIN matches m ON m.id=a.match_id
 LEFT JOIN batting_facts b ON b.match_id=a.match_id AND b.player_id=a.player_id
 WHERE m.status<>'Upcoming' AND m.match_date>=date(:as_of,'-3 years') AND m.match_date<=:as_of
 GROUP BY a.player_id,a.match_id),
 quarters AS (
 SELECT player_id,CAST(strftime('%Y',match_date) AS INTEGER) year,
 (CAST(strftime('%m',match_date) AS INTEGER)-1)/3+1 quarter,AVG(runs) average_runs,AVG(sr) average_strike_rate,COUNT(*) matches
 FROM per_match GROUP BY player_id,year,quarter HAVING COUNT(*)>=3),
 eligible AS (SELECT player_id FROM quarters GROUP BY player_id HAVING COUNT(*)>=6),
 changes AS (SELECT q.*,
 LAG(year*4+quarter) OVER w previous_quarter_index,
 CASE WHEN year*4+quarter-LAG(year*4+quarter) OVER w=1 THEN average_runs-LAG(average_runs) OVER w END runs_change,
 CASE WHEN year*4+quarter-LAG(year*4+quarter) OVER w=1 THEN average_strike_rate-LAG(average_strike_rate) OVER w END strike_rate_change,
 FIRST_VALUE(average_runs) OVER w first_runs,
 LAST_VALUE(average_runs) OVER(PARTITION BY q.player_id ORDER BY year,quarter ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) last_runs
 FROM quarters q JOIN eligible e ON e.player_id=q.player_id WINDOW w AS(PARTITION BY q.player_id ORDER BY year,quarter))
SELECT p.full_name,c.*,
CASE WHEN previous_quarter_index IS NULL THEN 'Baseline' WHEN runs_change IS NULL THEN 'Gap: no prior qualifying quarter'
 WHEN runs_change>5 THEN 'Improving' WHEN runs_change< -5 THEN 'Declining' ELSE 'Stable' END quarter_trend,
CASE WHEN last_runs-first_runs>10 THEN 'Career Ascending' WHEN last_runs-first_runs< -10 THEN 'Career Declining' ELSE 'Career Stable' END career_trajectory
FROM changes c JOIN players p ON p.id=c.player_id ORDER BY p.full_name,year,quarter;
```

Use participant match appearances over the trailing three years, retain quarters with three matches and players with six such quarters, then compare only adjacent calendar quarters. Show gaps without inventing quarter-on-quarter changes.
