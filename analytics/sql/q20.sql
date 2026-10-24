WITH apps AS (
 SELECT a.player_id,COUNT(*) total_matches,
 SUM(m.format='Test') test_matches,SUM(m.format='ODI') odi_matches,SUM(m.format IN ('T20I','T20')) t20_matches
 FROM participants a JOIN matches m ON m.id=a.match_id GROUP BY a.player_id HAVING COUNT(*)>=20),
 bat AS (SELECT player_id,
 1.0*SUM(CASE WHEN format='Test' THEN runs END)/NULLIF(SUM(CASE WHEN format='Test' THEN dismissed END),0) test_average,
 1.0*SUM(CASE WHEN format='ODI' THEN runs END)/NULLIF(SUM(CASE WHEN format='ODI' THEN dismissed END),0) odi_average,
 1.0*SUM(CASE WHEN format IN ('T20I','T20') THEN runs END)/NULLIF(SUM(CASE WHEN format IN ('T20I','T20') THEN dismissed END),0) t20_average
 FROM batting_facts GROUP BY player_id)
SELECT p.full_name,a.*,b.test_average,b.odi_average,b.t20_average FROM apps a JOIN players p ON p.id=a.player_id
LEFT JOIN bat b ON b.player_id=a.player_id ORDER BY p.full_name;
