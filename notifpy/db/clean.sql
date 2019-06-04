DELETE FROM videos
WHERE id IN (
	SELECT id FROM (
		SELECT id, (
			SELECT COUNT()+1 FROM (
				SELECT publishedAt
					FROM videos as t
					WHERE publishedAt > videos.publishedAt
					AND channelId=videos.channelId
				)
			) AS rank
		FROM videos
		WHERE rank > 50
	)
);
