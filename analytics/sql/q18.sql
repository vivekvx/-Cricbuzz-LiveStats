SELECT p.full_name,COUNT(DISTINCT b.match_id) matches,6.0*SUM(b.runs)/NULLIF(SUM(b.balls),0) economy,
SUM(b.wickets) wickets,1.0*SUM(b.balls)/6/COUNT(DISTINCT b.match_id) overs_per_match
FROM bowling_facts b JOIN players p ON p.id=b.player_id WHERE b.format IN ('ODI','T20I','T20')
GROUP BY p.id HAVING COUNT(DISTINCT b.match_id)>=10 AND 1.0*SUM(b.balls)/COUNT(DISTINCT b.match_id)>=12
ORDER BY economy,p.id;
