SELECT t.name,COUNT(m.id) wins FROM teams t LEFT JOIN matches m ON m.winner_id=t.id AND m.status='Complete'
GROUP BY t.id ORDER BY wins DESC,t.name;
