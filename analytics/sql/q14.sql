WITH appearances AS (
 SELECT player_id,venue_id,match_id,SUM(balls) balls,SUM(runs) runs,SUM(wickets) wickets
 FROM bowling_facts GROUP BY player_id,venue_id,match_id HAVING SUM(balls)>=24)
SELECT p.full_name,v.name venue,AVG(6.0*a.runs/NULLIF(a.balls,0)) average_economy,
SUM(a.wickets) wickets,COUNT(*) matches FROM appearances a JOIN players p ON p.id=a.player_id
JOIN venues v ON v.id=a.venue_id GROUP BY a.player_id,a.venue_id HAVING COUNT(*)>=3
ORDER BY p.full_name,v.name;
