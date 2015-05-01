# Project 2 Paper

##Collection

##Anonymization

##Tables

##Data

##Data Samples

##Feature Detection

##Feature Detection Results

##Bad Smells Detector

##Bad Smells Results

##Early Warning

##Early Warning Results





# Project 2 Info (Not part of paper)
repo for storing project 2 data and code

## Usage
To acquire data in easier to process form, you must run gitable-sql.py
But, to do so, you must have a token.

`curl -i -u <your_username> -d '{"scopes": ["repo", "user"], "note": "OpenSciences"}' https://api.github.com/authorizations`

The token returned in the response should be copied and pasted into gitable.conf (copy gitable.conf.example) in the indicated place.

Once the token is installed, you can run the data dumper via python:
```
python gitable-sql.py repo group1
```
With whatever repo you like and an anonymizing group name. After a few minutes of churning over web requests, it'll spit out a sqlite3 database file with the data packed up and ready for query.

## Known limitations
Currently, if one of the many requests made to GitHub for data times out, the entire run is pretty much useless. In the future we hope to capture the error as it is happening and have the data dumper retry timed out queries.
