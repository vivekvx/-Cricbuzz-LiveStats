WITH per_match AS (
 SELECT player_id,match_id,match_date,SUM(runs) runs,100.0*SUM(runs)/NULLIF(SUM(balls),0) sr
 FROM batting_facts GROUP BY player_id,match_id),
 quarters AS (
 SELECT player_id,CAST(strftime('%Y',match_date) AS INTEGER) year,
 (CAST(strftime('%m',match_date) AS INTEGER)-1)/3+1 quarter,AVG(runs) average_runs,AVG(sr) average_strike_rate,COUNT(*) matches
 FROM per_match GROUP BY player_id,year,quarter HAVING COUNT(*)>=3),
 eligible AS (SELECT player_id FROM quarters GROUP BY player_id HAVING COUNT(*)>=6),
 changes AS (SELECT q.*,average_runs-LAG(average_runs) OVER w runs_change,
 average_strike_rate-LAG(average_strike_rate) OVER w strike_rate_change,
 FIRST_VALUE(average_runs) OVER w first_runs,
 LAST_VALUE(average_runs) OVER(PARTITION BY q.player_id ORDER BY year,quarter ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) last_runs
 FROM quarters q JOIN eligible e ON e.player_id=q.player_id WINDOW w AS(PARTITION BY q.player_id ORDER BY year,quarter))
SELECT p.full_name,c.*,
CASE WHEN runs_change IS NULL THEN 'Baseline' WHEN runs_change>5 THEN 'Improving' WHEN runs_change< -5 THEN 'Declining' ELSE 'Stable' END quarter_trend,
CASE WHEN last_runs-first_runs>10 THEN 'Career Ascending' WHEN last_runs-first_runs< -10 THEN 'Career Declining' ELSE 'Career Stable' END career_trajectory
FROM changes c JOIN players p ON p.id=c.player_id ORDER BY p.full_name,year,quarter;
