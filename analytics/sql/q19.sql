SELECT p.full_name,AVG(b.runs) average_runs,stddev_pop(b.runs) standard_deviation,COUNT(*) innings
FROM batting_facts b JOIN players p ON p.id=b.player_id WHERE b.match_date>='2022-01-01' AND b.balls>=10
GROUP BY p.id ORDER BY standard_deviation,p.id;
