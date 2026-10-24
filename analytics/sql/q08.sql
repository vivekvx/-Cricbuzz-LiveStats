SELECT name,host_country,format,start_date,planned_matches FROM series
WHERE start_date>='2024-01-01' AND start_date<'2025-01-01' ORDER BY start_date,name;
