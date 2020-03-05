DROP TABLE IF EXISTS query;
DROP TABLE IF EXISTS pnp;
DROP TABLE IF EXISTS configuration;
DROP TABLE IF EXISTS basic_study_search;

CREATE TABLE query (
	query_id INTEGER PRIMARY KEY AUTOINCREMENT, 
	last_name TEXT NOT NULL, 
	first_name TEXT, 
	dob TEXT,
	start_date TEXT, 
	stop_date TEXT, 
	modality TEXT
);

CREATE TABLE pnp (
    pnp_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE configuration (
  configuration_id INTEGER PRIMARY KEY  AUTOINCREMENT,
  pnp_id INTEGER NOT NULL,
  host_ip TEXT NOT NULL,
  host_port INTEGER NOT NULL,
  client_name TEXT NOT NULL,
  client_ip TEXT,
  client_port INTEGER NOT NULL,
  dcm_storage_path TEXT NOT NULL,
  log_storage_path TEXT NOT NULL,
  query_model TEXT NOT NULL,
  query_break_count INTEGER NOT NULL,
  FOREIGN KEY (pnp_id) REFERENCES pnp (pnp_id)
);


CREATE TABLE basic_study_search (
    basic_study_search_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pnp_id INTEGER NOT NULL,
    query_retrieve_level TEXT NOT NULL,
    patient_name TEXT NOT NULL,
    patient_id TEXT,
    patient_birth_date TEXT,
    study_date TEXT,
    study_id TEXT,
    study_instance_uid TEXT,
    study_description TEXT,
    modality TEXT
);