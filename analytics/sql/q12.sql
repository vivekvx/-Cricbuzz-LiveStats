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
