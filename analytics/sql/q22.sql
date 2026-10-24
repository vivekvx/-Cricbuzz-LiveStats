WITH recent AS (
 SELECT *,MIN(team1_id,team2_id) a,MAX(team1_id,team2_id) b FROM matches
 WHERE status='Complete' AND match_date>=date(:as_of,'-3 years') AND match_date<=:as_of),
 eligible AS (SELECT a,b,COUNT(*) meetings FROM recent GROUP BY a,b HAVING COUNT(*)>=5),
 sides AS (SELECT r.*,a team_id,b opponent_id FROM recent r UNION ALL SELECT r.*,b,a FROM recent r)
SELECT t.name team,o.name opponent,e.meetings pair_meetings,v.name venue,
CASE WHEN s.batting_first_id IS NULL THEN 'Unknown' WHEN s.team_id=s.batting_first_id THEN 'Batting first' ELSE 'Bowling first' END approach,
COUNT(*) matches,SUM(CASE WHEN s.winner_id=s.team_id THEN 1 ELSE 0 END) wins,
100.0*SUM(CASE WHEN s.winner_id=s.team_id THEN 1 ELSE 0 END)/COUNT(*) win_percentage,
AVG(CASE WHEN s.winner_id=s.team_id AND s.victory_type='runs' THEN s.margin END) average_winning_margin_runs,
AVG(CASE WHEN s.winner_id=s.team_id AND s.victory_type='wickets' THEN s.margin END) average_winning_margin_wickets,
(SELECT COUNT(*) FROM recent r2 WHERE r2.a=s.a AND r2.b=s.b AND r2.winner_id=s.team_id) overall_wins,
100.0*(SELECT COUNT(*) FROM recent r2 WHERE r2.a=s.a AND r2.b=s.b AND r2.winner_id=s.team_id)/e.meetings overall_win_percentage
FROM sides s JOIN eligible e ON e.a=s.a AND e.b=s.b JOIN teams t ON t.id=s.team_id
JOIN teams o ON o.id=s.opponent_id LEFT JOIN venues v ON v.id=s.venue_id
GROUP BY s.a,s.b,s.team_id,s.venue_id,approach ORDER BY t.name,o.name,v.name,approach;
