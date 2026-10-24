SELECT t.name,CASE WHEN v.country=t.country THEN 'Home' ELSE 'Away' END conditions,COUNT(*) wins
FROM matches m JOIN teams t ON t.id=m.winner_id JOIN venues v ON v.id=m.venue_id
WHERE m.status='Complete' AND v.country<>'Unknown' AND t.country<>'Unknown' GROUP BY t.id,conditions ORDER BY t.name,conditions;
