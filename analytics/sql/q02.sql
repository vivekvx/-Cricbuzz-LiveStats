SELECT m.description,t1.name team1,t2.name team2,v.name venue,v.city,m.match_date
FROM matches m JOIN teams t1 ON t1.id=m.team1_id JOIN teams t2 ON t2.id=m.team2_id
LEFT JOIN venues v ON v.id=m.venue_id
WHERE m.match_date>=date(:as_of,'-30 days') AND m.match_date<=:as_of
AND m.status IN ('Complete','Live') ORDER BY m.match_date DESC,m.id DESC;
