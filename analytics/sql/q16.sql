SELECT p.full_name,strftime('%Y',b.match_date) year,1.0*SUM(b.runs)/COUNT(DISTINCT b.match_id) average_runs_per_match,
AVG(b.strike_rate) average_strike_rate,COUNT(DISTINCT b.match_id) matches
FROM batting_facts b JOIN players p ON p.id=b.player_id WHERE b.match_date>='2020-01-01'
GROUP BY p.id,year HAVING COUNT(DISTINCT b.match_id)>=5 ORDER BY p.full_name,year;
