CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    accountID INTEGER REFERENCES users(id),
    stack TEXT
);
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    source TEXT,
    uid TEXT UNIQUE,
    content TEXT,
    media TEXT,
    html_snapshot TEXT,
    is_threat_reasoning TEXT,
    is_threat BOOLEAN,
    description TEXT,
    threat_title TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS projects_impacted (
    id SERIAL PRIMARY KEY,
    project_id integer,
    threat_id integer,
    does_impact_analysis TEXT,
    impacted BOOLEAN,
    description_of_relation TEXT
);
CREATE TABLE IF NOT EXISTS queue (
    id SERIAL PRIMARY KEY,
    data TEXT,
    task TEXT,
    status TEXT DEFAULT 'pending',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
