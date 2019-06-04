CREATE TABLE IF NOT EXISTS videos (
    id CHAR(11) UNIQUE,
    channelId CHAR(24),
    title TEXT,
    publishedAt DATETIME,
    description TEXT,
    thumbnail TEXT,
    PRIMARY KEY (id),
    FOREIGN KEY (channelId) REFERENCES channels(channelId)
);

CREATE TABLE IF NOT EXISTS channels (
    id CHAR(24) UNIQUE,
    title TEXT,
    description TEXT,
    priority INTEGER,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS patterns (
    id INTEGER PRIMARY KEY UNIQUE,
    channelId CHAR(24),
    regex TEXT,
    FOREIGN KEY (channelId) REFERENCES channels(channelId)
);
