SELECT p.full_name,c.runs,c.wickets,c.format FROM career c JOIN players p ON p.id=c.player_id
WHERE p.role='All-rounder' AND c.runs>1000 AND c.wickets>50 ORDER BY c.format,c.runs DESC,p.id;
