SELECT p.full_name batter1,q.full_name batter2,a.runs+b.runs combined_runs,a.match_id,a.number innings_number,
'Consecutive-position proxy; not actual stand' measure
FROM batting_facts a JOIN batting_facts b ON a.innings_id=b.innings_id AND b.position=a.position+1
JOIN players p ON p.id=a.player_id JOIN players q ON q.id=b.player_id
WHERE a.runs+b.runs>=100 ORDER BY combined_runs DESC,a.innings_id,a.position;
