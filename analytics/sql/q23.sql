WITH numbered AS (
 SELECT *,ROW_NUMBER() OVER(PARTITION BY player_id ORDER BY match_date DESC,match_id DESC,number DESC) rn FROM batting_facts),
 form AS (SELECT player_id,AVG(CASE WHEN rn<=5 THEN runs END) last5_average,AVG(runs) last10_average,
 AVG(CASE WHEN rn<=5 THEN strike_rate END) last5_strike_rate,AVG(strike_rate) last10_strike_rate,
 SUM(runs>50) scores_above50,stddev_pop(runs) standard_deviation,COUNT(*) performances
 FROM numbered WHERE rn<=10 GROUP BY player_id)
SELECT p.full_name,f.*,last5_strike_rate-last10_strike_rate strike_rate_trend,
CASE WHEN last5_average>=50 AND last5_average>=last10_average AND last5_strike_rate>=last10_strike_rate AND standard_deviation<=30 AND scores_above50>=3 THEN 'Excellent Form'
 WHEN last5_average>=35 THEN 'Good Form' WHEN last5_average>=20 THEN 'Average Form' ELSE 'Poor Form' END form_classification
FROM form f JOIN players p ON p.id=f.player_id ORDER BY last5_average DESC,p.id;
