CREATE TABLE threads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title VARCHAR(64),
  created_at DATE,
  updated_at DATE
);

CREATE TABLE posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  thread_id INTEGER NOT NULL,
  name VARCHAR(32),
  email VARCHAR(128),
  text TEXT,
  created_at DATE
);
