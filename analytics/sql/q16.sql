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
