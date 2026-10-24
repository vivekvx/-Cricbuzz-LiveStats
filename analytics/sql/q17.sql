SELECT toss_decision,COUNT(*) matches,SUM(winner_id=toss_winner_id) toss_winner_wins,
100.0*SUM(winner_id=toss_winner_id)/COUNT(*) win_percentage
FROM matches WHERE status='Complete' AND winner_id IS NOT NULL AND toss_winner_id IS NOT NULL
AND toss_decision IS NOT NULL GROUP BY toss_decision ORDER BY toss_decision;
