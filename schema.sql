CREATE TABLE threads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title VARCHAR(64),
  created_at DATETIME,
  updated_at DATETIME
);

CREATE TABLE posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  thread_id INTEGER NOT NULL,
  name VARCHAR(32),
  email VARCHAR(128),
  text TEXT,
  created_at DATETIME
);
