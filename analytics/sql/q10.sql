SELECT m.description,t1.name team1,t2.name team2,w.name winner,m.margin,m.victory_type,v.name venue,m.match_date
FROM matches m JOIN teams t1 ON t1.id=m.team1_id JOIN teams t2 ON t2.id=m.team2_id
LEFT JOIN teams w ON w.id=m.winner_id LEFT JOIN venues v ON v.id=m.venue_id
WHERE m.status='Complete' ORDER BY m.match_date DESC,m.id DESC LIMIT 20;
