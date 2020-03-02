DROP TABLE IF EXISTS query; 

CREATE TABLE query (
	query_id INTEGER PRIMARY KEY AUTOINCREMENT, 
	last_name TEXT NOT NULL, 
	first_name TEXT, 
	dob TEXT,
	start_date TEXT, 
	stop_date TEXT, 
	modality TEXT
);


