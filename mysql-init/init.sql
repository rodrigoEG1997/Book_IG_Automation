#-----------------------------------------------------------------
#CREATE QUOTES SECTION
#-----------------------------------------------------------------

CREATE TABLE IF NOT EXISTS Authors (
  id INT AUTO_INCREMENT PRIMARY KEY,
  id_Wikipedia VARCHAR(20) NOT NULL UNIQUE,
  id_OpenLibrary VARCHAR(20) NOT NULL UNIQUE,
  name VARCHAR(50),
  bio TEXT,
  photo VARCHAR(510),
  wikipedia_url TEXT,
  description TEXT,
  img_author VARCHAR(510),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Books (
  id INT AUTO_INCREMENT PRIMARY KEY,
  id_Author INT NOT NULL,
  title VARCHAR(100),
  id_OpenLibrary VARCHAR(20),
  first_publish_year INT,
  edition_count INT,
  cover_id VARCHAR(20),
  cover_url VARCHAR(50),
  ratings_average DECIMAL(10, 4),
  ratings_count INT,
  want_to_read_count INT,
  first_sentence TEXT,
  description TEXT,
  subjects TEXT,
  links TEXT,
  quote_1 VARCHAR(510),
  quote_2 VARCHAR(510),
  quote_3 VARCHAR(510),
  quote_4 VARCHAR(510),
  quote_5 VARCHAR(510),
  available BOOLEAN,
  img_book VARCHAR(510),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (id_Author)
        REFERENCES Authors(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Variables (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50),
  value INT
);

INSERT INTO Variables (name, value) VALUES ('count_background', 1);