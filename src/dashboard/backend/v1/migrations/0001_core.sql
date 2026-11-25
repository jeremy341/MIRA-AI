CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    source TEXT NOT NULL,
    model_name TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    started_at_ts REAL NOT NULL,
    ended_at_ts REAL,
    config_json TEXT,
    notes TEXT
);
CREATE TABLE IF NOT EXISTS detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    ts REAL NOT NULL,
    frame_index INTEGER,
    class_name TEXT NOT NULL,
    confidence REAL NOT NULL,
    x1 INTEGER, y1 INTEGER, x2 INTEGER, y2 INTEGER,
    track_id INTEGER
);
CREATE INDEX IF NOT EXISTS idx_detections_session_ts ON detections(session_id, ts);
CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
    ts REAL NOT NULL,
    fps REAL,
    latency_ms REAL,
    cpu_percent REAL,
    memory_percent REAL,
    temperature_c REAL
);
CREATE INDEX IF NOT EXISTS idx_metrics_session_ts ON metrics(session_id, ts);
CREATE TABLE IF NOT EXISTS hardware_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    cpu_percent REAL,
    memory_percent REAL,
    temperature_c REAL,
    load_1m REAL
);
CREATE INDEX IF NOT EXISTS idx_hardware_ts ON hardware_samples(ts);
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    title TEXT,
    status TEXT NOT NULL,
    progress REAL NOT NULL DEFAULT 0,
    message TEXT,
    created_at_ts REAL NOT NULL,
    finished_at_ts REAL,
    result_json TEXT,
    error TEXT
);
CREATE TABLE IF NOT EXISTS comparisons (
    id TEXT PRIMARY KEY,
    created_at_ts REAL NOT NULL,
    input_name TEXT,
    models_json TEXT NOT NULL,
    results_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS benchmark_runs (
    id TEXT PRIMARY KEY,
    created_at_ts REAL NOT NULL,
    status TEXT NOT NULL,
    config_json TEXT NOT NULL,
    results_json TEXT,
    job_id TEXT
);
CREATE TABLE IF NOT EXISTS arm_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    kind TEXT NOT NULL,
    class_name TEXT,
    track_id INTEGER,
    payload_json TEXT NOT NULL DEFAULT '{}',
    correct INTEGER
);
CREATE INDEX IF NOT EXISTS idx_arm_events_ts ON arm_events(ts);
