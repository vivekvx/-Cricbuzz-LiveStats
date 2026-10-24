WITH pairs AS (
 SELECT MIN(a.player_id,b.player_id) p1,MAX(a.player_id,b.player_id) p2,a.runs+b.runs combined_runs
 FROM batting a JOIN batting b ON a.innings_id=b.innings_id AND b.position=a.position+1),
 summary AS (SELECT p1,p2,COUNT(*) partnerships,AVG(combined_runs) average_combined_runs,
 SUM(combined_runs>50) exceeding50,MAX(combined_runs) highest_score,100.0*SUM(combined_runs>50)/COUNT(*) success_percentage
 FROM pairs GROUP BY p1,p2 HAVING COUNT(*)>=5)
SELECT p.full_name batter1,q.full_name batter2,s.*,
DENSE_RANK() OVER(ORDER BY success_percentage DESC,average_combined_runs DESC) rank,
'Consecutive-position proxy; not actual stand' measure
FROM summary s JOIN players p ON p.id=s.p1 JOIN players q ON q.id=s.p2 ORDER BY rank,s.p1,s.p2;
