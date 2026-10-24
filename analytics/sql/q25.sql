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
