# Project 2 Paper

##Collection

###What we collected

We collected a wealth of data from GitHub for each team. This data was kept organized in mostly the same way that GitHub organizes it, and consists of the following:

* Issues
 + Issue ID
 + Issue Name
 + Creation Time (time of first event)
 + Action Performed (label/unlabel/milestone/closed, etc)
 + User associated with action
* Milestones
 + Milestone ID
 + Description
 + Creation Time
 + Due Time
 + Closed Time
 + User who created it
* Comments
 + User
 + Issue comment was on
 + Timestamp
 + Text of the comment
* Commits
 + User
 + Timestamp
 + Message

Github organizes their API in much the same way and we saw no reason to break too far from their pattern. In addition, grabbing the raw data and caching it locally allows for fewer potential issues with network connections or API rate limitations, as opposed to using feature detectors that performed analysis directly after retrieving the data and storing the results.

###How we collected it

As recommended, we utilized the gitable.py utility to grab the initial sets of data, but later decided that we would like more data than it could provide. We also agreed that inserting the data into a SQL database for query would be a valuable first step. Our current data collection process proceeds as follows:

1. Start up gitable-sql.py (our modified gitable.py) with inputs for the target repo and anonymized group name
2. Retrieve all the data from GitHub's API
3. Preprocess it (anonymization and formatting for insertion into database)
4. Create a SQLite database if one does not already exist, and insert all the data into it

Once this is complete, a .db file for that repo which can be transferred through email or any other file sharing means and queried at leisure offline.

##Anonymization

Something something replaced things as we saw them.

##Tables**

##Data

##Data Samples

##Feature Detection**

We eventually came up with 13 feature detectors utilizing our data. These detectors are as follows:

#### 1. Long Open Issues

This feature is relatively straightforward, we found the difference between the time that an issue was marked as closed and when the first event occurred on that issue. Expressed in SQL, this feature can be detected via:
```SQL
select cl.issueID, (cl.time - op.time) as timeOpen from event cl, (select issueID, min(time) as time from event group by issueID) op where cl.action == 'closed' AND cl.issueID == op.issueID;
```

#### 2. Issues Missing Milestones

This feature is also fairly straightforward, we found the difference between the time that an issue was marked as closed and when the milstone it was assigned to was due. In SQL, this is expressed as:
```SQL
select ev.issueID, ev.time-milestone.due_at as secondsAfter from
(select issueID, time, milestone from event ev1 where action = 'closed' and milestone not null and time >=
   (select max(time) from event where issueID = ev1.issueID and action = 'closed')
) ev,
milestone where milestone.id = ev.milestone;
```

#### 3. Issue Closed Long Before Milstone Due

This feature is a little bit more complicated than the previous ones. In our project we came up with milestones under the assumption that all work for a particular milestone should be complete before a new milestone was started, and the work for that next milestone should not start until the work for the previous milestone had been completed. Operating under this assumption, we decided that it would be strange if work on a milestone's issues (shown as closed issues) was being done before a milestone was even started, meaning the one previous to it had not finished.
This idea can be expressed as an SQL query as the following:
```SQL
select e1.issueID, (e1.time - (mileDur.due_at - mileDur.duration)) as timeAfterStart, mileDur.duration as duration from
event e1,
(select m2.id, m2.due_at, (m2.due_at - m1.due_at) as duration from milestone m1, milestone m2 where m2.id = m1.id+1) mileDur
where e1.milestone = mileDur.id and e1.action = 'closed' and e1.time >= (select max(time) from event where event.action = 'closed' and issueID = e1.issueID);
```

#### 4. Equal Number of Issue Assignees

Rather straightforward, we decided that finding the number of issues assigned to each user in a project would be helpful information. In SQL, this is expressed as:
```SQL
select label, count(*) from (select issueID, label from event e1 where action = 'assigned' and time >= (select max(time) from event where e1.issueID = issueID and action = 'assigned')) group by label;
```

#### 5. Number of People Commenting on an Issue

We felt that communicating on issues was an important part of team cohesiveness and involvement, and we felt that having a low number of people commenting on any particular issue would be an interesting data point to have. In SQL, we can discover the number of unique (non-repeated) users commenting on any particular issue with:
```SQL
select issueID, count(distinct user) from comment group by issueID;
```

#### 6. Number of Issues Posted by Each User

As with users being assigned issues, we felt that knowing the spread of who identified or created issues was important. In SQL:
```SQL
select user, count(*) from event e1 where time <= (select min(time) from event where issueID = e1.issueID) group by user;
```

#### 7. Bug Label Usage

All software has bugs at some point or another, no matter how good the coder or tools, so we felt that the number of bug reports on a project would be a good metric of how carefully the team was looking for them. This detector outputs the number of issues labeled with any label that looks like "bug", the number of total issues, and the ratio of the two.
```SQL
select bugs, count(distinct issueID) as issues, (bugs+0.0)/count(distinct issueID) as ratio from (select count(*) as bugs from event where lower(label) like '%bug%' and action == 'labeled'), event;
```

#### 8. Number of Comments on an Issue

As with the number of people commenting on an issue, we felt the number of comments on an issue was important information.
```SQL
select issueID, count(*) from comment group by issueID;
```

#### 9. Nonlinear Progress Momentum

This feature is difficult to describe succinctly. It is a relation between a milestone's creation date, due date, and actual completion date. Projects that are more waterfall-y will have a very flat line for milestone creation date, showing that milestones were created all at once at the beginning of the project. Very agile-y projects will have a near-constant gap between milestone creation date and due date, indicating milestones are created every so often as work is proceeding. Projects with good effort estimation will have a very small or nonexistant gap between milestone due dates and completion dates, whereas projects with bad effort estimation will have large or highly variable gaps.

#### 10. Commit History Linearity

The commit history of a project generally indicates how frequently people are working on the project. A completely linear commit history would indicate that there was exactly constant amounts of work occurring, but life is not quite that perfect, so a linearity of around 0.8 and 0.9 is to be expected for projects that are proceeding smoothly. Graphs that look more like an exponential function, howver, indicate that the team is rushing toward the end of the project.

#### 11. Percentage of Comments by User

As with other participation measures, the percentage of comments in a repo from any particular user can be quite useful, and is expressed in SQL as the following:
```SQL
select user, count(*) as comments from comment group by user;
```

#### 12. Short Lived Issues

We observed in our own group that sometimes users would mentally assign themselves to a feature but forget to put in an issue for it until after the feature was complete. This could potentially lead to duplicated work or just bad communication.
In SQL we can extract the number of issues that have been open less than an hour and the total number of issues with the following:
```SQL
select numShort, numTotal, (numShort+0.0)/numTotal from (select count(*) as numShort from event cl, (select issueID, min(time) as time from event group by issueID) op where cl.action == 'closed' AND cl.issueID == op.issueID and (cl.time - op.time) < 3600), (select count(distinct issueID) as numTotal from event);
```

#### 13. Effort Estimation Error

This detector was intended to discover if there was a correlation between when a milestone was created, relative to when it was due, and how far off it was from the actual close date. If such a correlation existed, milestones created far away from when they were due would be more frequently missed, and by a larger margin, than milestones created close to when they were due.

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
