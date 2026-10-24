SELECT p.full_name,SUM(CASE WHEN c.format='Test' THEN COALESCE(c.runs,0) ELSE 0 END) test_runs,
SUM(CASE WHEN c.format='ODI' THEN COALESCE(c.runs,0) ELSE 0 END) odi_runs,
SUM(CASE WHEN c.format='T20I' THEN COALESCE(c.runs,0) ELSE 0 END) t20i_runs,
1.0*SUM(c.runs)/NULLIF(SUM(c.dismissals),0) overall_batting_average
FROM career c JOIN players p ON p.id=c.player_id WHERE c.matches>0
GROUP BY p.id HAVING COUNT(DISTINCT c.format)>=2 ORDER BY p.full_name;
