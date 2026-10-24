SELECT format,MAX(runs) highest_score FROM batting_facts WHERE format IN ('Test','ODI','T20I') GROUP BY format ORDER BY format;
