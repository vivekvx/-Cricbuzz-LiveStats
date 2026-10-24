WITH per_match AS (
 SELECT player_id,match_id,SUM(runs) runs,MAX(team_id=winner_id) won FROM batting_facts
 WHERE (victory_type='runs' AND margin<50) OR (victory_type='wickets' AND margin<5)
 GROUP BY player_id,match_id)
SELECT p.full_name,AVG(a.runs) average_runs,COUNT(*) close_matches,SUM(a.won) team_wins
FROM per_match a JOIN players p ON p.id=a.player_id GROUP BY p.id ORDER BY average_runs DESC,p.id;
