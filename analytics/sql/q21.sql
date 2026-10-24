WITH points AS (
 SELECT c.*,COALESCE(runs*0.01,0)+COALESCE(batting_average*0.5,0)+COALESCE(strike_rate*0.3,0) batting_points,
 CASE WHEN bowled_balls>0 THEN COALESCE(wickets*2,0)+COALESCE((50-bowling_average)*0.5,0)+COALESCE((6-economy)*2,0) ELSE 0 END bowling_points,
 catches*3+stumpings*5 fielding_points FROM career c),
 scored AS (SELECT *,batting_points+bowling_points+fielding_points total_score FROM points)
SELECT p.full_name,s.format,s.batting_points,s.bowling_points,s.fielding_points,s.total_score,
DENSE_RANK() OVER(PARTITION BY s.format ORDER BY s.total_score DESC) rank
FROM scored s JOIN players p ON p.id=s.player_id ORDER BY s.format,rank,p.id;
