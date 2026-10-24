SELECT p.full_name,c.runs career_runs,c.batting_average,c.centuries FROM career c JOIN players p ON p.id=c.player_id
WHERE c.format='ODI' AND c.runs IS NOT NULL ORDER BY c.runs DESC,p.id LIMIT 10;
