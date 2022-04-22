CREATE DATABASE IF NOT EXISTS photoshare;
USE photoshare;
DROP TABLE IF EXISTS Friends CASCADE;
DROP TABLE IF EXISTS Tagged CASCADE;
DROP TABLE IF EXISTS Comments CASCADE;
DROP TABLE IF EXISTS Likes CASCADE;
DROP TABLE IF EXISTS Pictures CASCADE;
DROP TABLE IF EXISTS Albums CASCADE;
DROP TABLE IF EXISTS Users CASCADE;
DROP TABLE IF EXISTS Tags CASCADE;

CREATE TABLE Users (
    user_id int4  AUTO_INCREMENT,
	first_name VARCHAR(100),
	last_name VARCHAR(100),
    email varchar(255) UNIQUE,
    birth_date DATE,
	hometown VARCHAR(100),
	gender VARCHAR(100),
    password varchar(255),
  CONSTRAINT users_pk PRIMARY KEY (user_id)
);

 CREATE TABLE Friends(
 user_id1 int4,
 user_id2 int4,
 PRIMARY KEY (user_id1, user_id2),
 FOREIGN KEY (user_id1)
 REFERENCES Users(user_id),
 FOREIGN KEY (user_id2)
 REFERENCES Users(user_id)
);

CREATE TABLE Albums(
 albums_id int4 AUTO_INCREMENT,
 name VARCHAR(100),
 date DATE,
 user_id INTEGER NOT NULL,
 PRIMARY KEY (albums_id),
 FOREIGN KEY (user_id)
 REFERENCES Users(user_id)
);

CREATE TABLE Tags(
 tag_id int4 AUTO_INCREMENT,
 name VARCHAR(100),
 PRIMARY KEY (tag_id)
);

CREATE TABLE Pictures
(
	picture_id int4  AUTO_INCREMENT,
	user_id int4,
    albums_id int4,
	imgdata longblob ,
	caption VARCHAR(255),
	INDEX upid_idx (user_id),
	CONSTRAINT pictures_pk PRIMARY KEY (picture_id),
	FOREIGN KEY (albums_id) REFERENCES Albums (albums_id) ON DELETE CASCADE,
	FOREIGN KEY (user_id) REFERENCES Users (user_id)
);

CREATE TABLE Tagged(
 picture_id int4,
 tag_id int4,
 PRIMARY KEY (picture_id, tag_id),
 FOREIGN KEY(picture_id)
 REFERENCES Pictures (picture_id) ON DELETE CASCADE,
 FOREIGN KEY(tag_id)
 REFERENCES Tags (tag_id)
);

CREATE TABLE Comments(
 comment_id int4 AUTO_INCREMENT,
 user_id int4 NOT NULL,
 picture_id int4 NOT NULL,
 text VARCHAR (100),
 date DATE,
 PRIMARY KEY (comment_id),
 FOREIGN KEY (user_id)
 REFERENCES Users (user_id),
 FOREIGN KEY (picture_id)
 REFERENCES Pictures (picture_id)
);

CREATE TABLE Likes(
 picture_id int4,
 user_id int4,
 PRIMARY KEY (picture_id,user_id),
 FOREIGN KEY (picture_id)
 REFERENCES Pictures (picture_id),
 FOREIGN KEY (user_id)
 REFERENCES Users (user_id)
);