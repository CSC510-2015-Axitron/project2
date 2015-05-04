# Project 2 Paper

## 1. Collection

### 1.1 What we collected

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

### 1.2 How we collected it

As recommended, we utilized the gitable.py utility to grab the initial sets of data, but later decided that we would like more data than it could provide. We also agreed that inserting the data into a SQL database for query would be a valuable first step. Our current data collection process proceeds as follows:

1. Start up [gitable-sql.py](https://github.com/CSC510-2015-Axitron/project2/blob/master/gitable-sql.py) (our modified gitable.py) with inputs for the target repo and anonymized group name
2. Retrieve all the data from GitHub's API
3. Preprocess it (anonymization and formatting for insertion into database)
4. Create a SQLite database if one does not already exist, and insert all the data into it

Once this is complete, it will spit out a .db file for that repo which can be transferred through email or any other file sharing means and queried at leisure offline.

## 2. Anonymization

Anonymization was performed on both group names and group users, so the individual groups and users will not be identified. Each group in our database was assigned with a number based on the order in which they were imported in the database. To anonymize users within each group, an empty array was created and each time when user ID was detected, the python program searched the array for the ID. If the user ID was not found in the array the ID would be entered into the array. Then, the user ID was replaced with "user" plus the index number of the ID in the array. The code for anonymization is shown as follows.

```
def anonymize(user):
  if anonymizer:
    if user == None : return ''
    idx = user_list.index(user) if user in user_list else -1
    if idx == -1:
      user_list.append(user)
      return "user"+str(len(user_list) - 1)
    else:
      return "user"+str(idx)
  else:
    return user
```

## 3. Tables

All tables in this project 2 paper are located in [Bad Smells Results](https://github.com/CSC510-2015-Axitron/project2#9-bad-smells-results) section, one table per bad smell. Each table reports stink scores summarized from the results of feature detectors corresponding to the particular bad smell. If the numerical result of feature detector for the group is higher than the defined threshold, a stink score "1" is earned.

## 4. Data

The totals listed in the table below include data from all 9 projects, our own included, and comes directly from summing up the number of entries in each SQL table.

| Milestones | Issues | Events | Comments | Commits |
|-----------:|-------:|-------:|---------:|--------:|
|         47 |    578 |   3883 |     1328 |    1760 |

## 5. Data Samples

The following samples are raw tuples taken from our own project's .db file. Where applicable, some attributes have been shortened where the data is too large to comfortably fit on the page.

#### Milestone
id|title|description|created_at|due_at|closed_at|user|identifier
---|---|---|---|---|---|---|---
1|v0.1|(text)|1424538641|1425013200|1425168047|group9/user1|989453
#### Issue
id|name
---|---
1|User Input (moving smily via keyboard)
#### Event
issueID|time|action|label|user|milestone|identifier
---|---|---|---|---|---|---
1|1423616709|closed|closed|group9/user1||233661242
#### Comment
issueID|user|createtime|updatetime|text|identifier
---|---|---|---|---|---
1|group9/user1|1423608247|1423608247|(text)|73800452
#### Commits
id|time|sha|user|message
---|---|---|---|---
1|1428349546|d924a137ebf530fcd56c73980c9fcfbf6de69cdd|group9/user3|(text)

## 6. Feature Detection

We eventually came up with 13 feature detectors utilizing our data. These detectors are as follows:

#### (1) Long Open Issues

This feature is relatively straightforward, we found the difference between the time that an issue was marked as closed and when the first event occurred on that issue. Expressed in SQL, this feature can be detected via:
```SQL
select cl.issueID, (cl.time - op.time) as timeOpen from event cl, (select issueID, min(time) as time from event group by issueID) op where cl.action == 'closed' AND cl.issueID == op.issueID;
```

#### (2) Issues Missing Milestones

This feature is also fairly straightforward, we found the difference between the time that an issue was marked as closed and when the milstone it was assigned to was due. In SQL, this is expressed as:
```SQL
select ev.issueID, ev.time-milestone.due_at as secondsAfter from
(select issueID, time, milestone from event ev1 where action = 'closed' and milestone not null and time >=
   (select max(time) from event where issueID = ev1.issueID and action = 'closed')
) ev,
milestone where milestone.id = ev.milestone;
```

#### (3) Issue Closed Long Before Milstone Due

This feature is a little bit more complicated than the previous ones. In our project we came up with milestones under the assumption that all work for a particular milestone should be complete before a new milestone was started, and the work for that next milestone should not start until the work for the previous milestone had been completed. Operating under this assumption, we decided that it would be strange if work on a milestone's issues (shown as closed issues) was being done before a milestone was even started, meaning the one previous to it had not finished.
This idea can be expressed as an SQL query as the following:
```SQL
select e1.issueID, (e1.time - (mileDur.due_at - mileDur.duration)) as timeAfterStart, mileDur.duration as duration from
event e1,
(select m2.id, m2.due_at, (m2.due_at - m1.due_at) as duration from milestone m1, milestone m2 where m2.id = m1.id+1) mileDur
where e1.milestone = mileDur.id and e1.action = 'closed' and e1.time >= (select max(time) from event where event.action = 'closed' and issueID = e1.issueID);
```

#### (4) Equal Number of Issue Assignees

Rather straightforward, we decided that finding the number of issues assigned to each user in a project would be helpful information. In SQL, this is expressed as:
```SQL
select label, count(*) from (select issueID, label from event e1 where action = 'assigned' and time >= (select max(time) from event where e1.issueID = issueID and action = 'assigned')) group by label;
```

#### (5) Number of People Commenting on an Issue

We felt that communicating on issues was an important part of team cohesiveness and involvement, and we felt that having a low number of people commenting on any particular issue would be an interesting data point to have. In SQL, we can discover the number of unique (non-repeated) users commenting on any particular issue with:
```SQL
select issueID, count(distinct user) from comment group by issueID;
```

#### (6) Number of Issues Posted by Each User

As with users being assigned issues, we felt that knowing the spread of who identified or created issues was important. In SQL:
```SQL
select user, count(*) from event e1 where time <= (select min(time) from event where issueID = e1.issueID) group by user;
```

#### (7) Bug Label Usage

All software has bugs at some point or another, no matter how good the coder or tools, so we felt that the number of bug reports on a project would be a good metric of how carefully the team was looking for them. This detector outputs the number of issues labeled with any label that looks like "bug", the number of total issues, and the ratio of the two.
```SQL
select bugs, count(distinct issueID) as issues, (bugs+0.0)/count(distinct issueID) as ratio from (select count(*) as bugs from event where lower(label) like '%bug%' and action == 'labeled'), event;
```

#### (8) Number of Comments on an Issue

As with the number of people commenting on an issue, we felt the number of comments on an issue was important information.
```SQL
select issueID, count(*) from comment group by issueID;
```

#### (9) Nonlinear Progress Momentum

This feature is difficult to describe succinctly. It is a relation between a milestone's creation date, due date, and actual completion date. Projects that are more waterfall-y will have a very flat line for milestone creation date, showing that milestones were created all at once at the beginning of the project. Very agile-y projects will have a near-constant gap between milestone creation date and due date, indicating milestones are created every so often as work is proceeding. Projects with good effort estimation will have a very small or nonexistant gap between milestone due dates and completion dates, whereas projects with bad effort estimation will have large or highly variable gaps.

Additional feature detection can be performed on milestone due dates. Assuming each milestones in the project requires euqal amount of the effort, the due dates vs. the milestone numbers when plotted should be linear. To quantify the linearity of such curves, the due dates of milestones were fitted by a second degree polynomial regression equation.

```
y = a * x^2 + b * x + c
```

where variable **a** represents the curvature of the curve. High linearity should result in small value (i.e., a ~ 0).


#### (10) Commit History Linearity

The commit history of a project generally indicates how frequently people are working on the project. A completely linear commit history would indicate that there was exactly constant amounts of work occurring, but life is not quite that perfect, so a linearity of between 0 and 1.0 is to be expected for projects that are proceeding smoothly. Graphs that look more like an exponential function, however, indicate that the team is rushing toward the end of the project.

To determine the linearity of commit history, the area under each graph was determined and then compared to the area of the ideal curve. The equation to calcuate the linearity is shown as follows:

![linearity](http://i.imgur.com/zBDoT1n.png)

#### (11) Percentage of Comments by User

As with other participation measures, the percentage of comments in a repo from any particular user can be quite useful, and is expressed in SQL as the following:
```SQL
select user, count(*) as comments from comment group by user;
```

#### (12) Short Lived Issues

We observed in our own group that sometimes users would mentally assign themselves to a feature but forget to put in an issue for it until after the feature was complete. This could potentially lead to duplicated work or just bad communication.
In SQL we can extract the number of issues that have been open less than an hour and the total number of issues with the following:
```SQL
select numShort, numTotal, (numShort+0.0)/numTotal from (select count(*) as numShort from event cl, (select issueID, min(time) as time from event group by issueID) op where cl.action == 'closed' AND cl.issueID == op.issueID and (cl.time - op.time) < 3600), (select count(distinct issueID) as numTotal from event);
```

#### (13) Effort Estimation Error

This detector was intended to discover if there was a correlation between when a milestone was created, relative to when it was due, and how far off it was from the actual close date. If such a correlation existed, milestones created far away from when they were due would be more frequently missed, and by a larger margin, than milestones created close to when they were due.

## 7. Feature Detection Results

## 8. Bad Smells Detector

We combined our feature extractors to create 5 different bad smell detectors. In this section we will attempt to describe how these detectors were created as well as the motivation for each detector.  The idea was to try to create as many detectors as possible from the feature extractors that we were able to define.

#### Poor Communication
The first detector is for poor communication.  The overall motivation with this as a bad smell is that if a group cannot communicate well, it will generally affect their productivity over the long term.  People in this sort of situation generally work at cross purposes and can run into issues like commit collisions, or duplication of effort.  It uses three feature extractors:

- The number of posters in issue comments
- The number of comments in issues
- The percentage of comments by each user

For number of posters in issue comments we were looking at the number of of individual users that posted on each issue.  The idea is that if only a small percentage of a group actually discussed issues then there is really poor communication overall.  We set the limit at 50% of of the group, so groups having less than 50% of their members commenting on issues had a bad smell.

Number of comments in issues was gauged a bit differently.  We came to the conclusion that if an issue was important enough to be posted then there should be some kind of discussion of that issue.  We decided that less than 2 comments per issue was a bad smell.  At that point there is no to very little discussion of individual issues.

Percentage of comments by each user is another metric for communication.  If only a few members actually make comments in issues then there are only a few members that are actually communicating.  We decided that if an individual user had less comments than the output of the following function we had a bad smell:  (total number of comments/number of group members * 2). 

#### Poor Milestone Usage
The next detecor is for poor milestone usage.  Milestones can be a great way to set up work for groups by splitting work into achievable sections.  So there can be two major benefits: the first is a simple sense of achievement for a group upon comletion of a milestone, the second is a a deadline to meet to keep work on track.  Additonally milestones can be used to get an idea of whether work is on track or not.  Given all of that poor milestone usage can definitely affect the level of success or failure that a group may find in producing a piece of software.  This detector comibined the following metrics:

- Issues missing milestones
- Non linear progress momentum
- Less than 3 milestones overall
- Milestones left incomplete

For the first of the metrics, issues missing milestones, we decided that a median value over 0 was a poor value for a group.  The idea was that if a few issues were outside of milestones that was acceptable since there are bound to be such issues.  A good example is a bug issue post, that post would likely be outside of any milestone and it is definitely a good thing to have bug posts. 

Non-linear progress momentum was another metric for this.  <PLACEHOLDER>  

If there were less than three milestones overall there was also a case for poor milestone usage.  THe motivation here is that if a group only had three milestones over the entire project lifespan then those three milestones were likely packed with issues and would be unweildy.  Splitting among many reachable milestones was viewed as more positive.

Milestones that were not completed was an obvious bad smell within a project.  If a group left any milestones incomplete they were considered as having a bad smell.  As will be seen below there were some groups that left more than one milestone open and that would be considered as even more negative.

#### Absent Group Member
The idea with this bad smell was that if a group member was not contributing they represented sort of dead weight within a project.  There are many bad effects that come with an absent group member but the most detrimental is poor morale.  If other group members sense that there is a member who isn't pulling their weight, it can negatively affect how the working members feel about the project in general.  Then added to that effect is the simple fact that there are just less hands to work on the project.  The metrics attached to the smell are:

- Number of issue posters
- Percentage of comments by each user
- Equal number of assignees
- Number of posters in issue comments

We used the same calculation for the first three metrics:  (Total number of x / number of group members * 2) where x is either issues, comments, or assignments for each metric.  If any individual user was below the number calculated for that function in either issues, comments, or assignements as matched the case we considered that a bad smell.  

Additionally we looked at the number of posters in issue comments.  If a user was posting in less than 50% of the comments we would also consider that a bad smell.

#### Poor Planning
Poor planning was a big of a hodgepodge of different feature extractors since github was used a good deal for planning throughout the semester.  The motivation here is that if a group had poor planning there could be many different failings that emerge over a semester.  If a group has planned poorly it will severely limit the amount of success they could possibly have over a semester long project.  The main way that takes place is in the lack of thinking about potential roadblocks in a project, if there is no plan in place then projects could get much of the way through development and hit an issue that makes the entire project non-functional.  Also a group may find that the scale of their project is either way above or way below the amount of time available for the project.  The metrics for the smell are:

- Long time between issues opening and closing
- Issues missing milestones
- Equal number of assignnees
- Non-linear progress momentum
- Short time between issues opening and closing
- Commit history linearity

For long time between issues opening and closing, we considered twenty days a poor performance.  At twenty days an issue had been outstanding for quite a long time and represents a bad smell.

We used the same calculations mentioned above for issues missing milestones, equal number of assignees, and non-linear progress momentum. 

With short time between issues opening and closing we considered that if greater than 20% of the issues for a group were open less than an hour, that was a bad smell.

Finally wiht the linearity of commit history, if the error in linearity was greater than 20% we considered that a bad smell.

#### Dictator 
Our dictator bad smell was very similar to our absent bad smell, but with many of the inequality symbols changed around.  If a project has a dictator there are many negative effects that may not be immediately visible.  The first effect is that options are not discussed so a group may not be taking an optimal path to completion of the project.  Secondly group members may not feel that they can contribute to the project simply because they were not consulted and do not have a grasp of all of the technologies involved.  THe metrics for this smell were:

- Number of posters in issue comments
- Number of issue posters
- Equal number of assignees
- Percent of comments by user

For number of posters in issue comments, if a single user had a comment in most of the issues, that was considered a bad smell.  

If a user posted more than the following function of issues that was also a bad smell: (Total number of issues / Number of members * 2)

If a user had more assignments than the following function of assignments that was also a bad smell: (Total number of assignments / Number of members * 2)

If a user posted more than the following function of comments that was also a bad smell: (Total number of comments / Number of members * 2)


## 9. Bad Smells Results

We have used the folowing acronyms for the various features that we were dealing with:

- numpost:  The number of posters in issue comments
- numcom: The number of comments in issues
- percom: The percentage of comments by each user
- missmile: Issues missing milestones
- nonlin:  Non-linear progress momentum
- fewmile:  Less than 3 milestones overall
- incmile:  Milestones left incomplete
- eqassgn:  Equal number of assignees
- longtime:  Lone time between issues opening and closing
- shorttime:  Short time between issues opening and closing
- lincommitt:  Commit history linearity
- numiss :  Number of issue posters

All of the results are listed below in tables.  We chose to represent each feature in boolean fashion.  If a group had a particular feature that met our guideline for a smell in a particular bad smell decector, that group received a 1 for that feature.  Each bad smell has a calculation for a "Stink Score".  The idea there is that each group should be graded in some fashion to see the extent of the bad smell for that particular group.  Simply having one of the features in each bad smell is definitely negative, but it seems more fair to look at the groups with respect to each other on each bad smell.  The graph below shows an overview of all of the bad smells for each group.

![stinkgraph.png](https://github.com/CSC510-2015-Axitron/project2/blob/master/img/stinkgraph.png?raw=true)

This graph helps a bit to understand the data but is difficult to interpret.  The most important takeaway is that all of the groups had some bad smells, and some bad smells were much worse across the board than others.  For example, poor communication was a problem in all of the groups per this data, but the degree of the problem differed across groups.  Another bad smell that afflicted all of the gropus was absent group member.  Again, this was a question of degree with some gropus actually receiving a point for all four features on that smell.  Poor milestone usage ended up being the lowest scoring bad smell overall with 4 groups not receiving any points at all.  

Another attempted metric here was an overall calculation of bad smells.  We tallied up the stink score across all of the bad smells to create this graph.  The important thing here was to remove any duplicate values from the calculation.  Eqassign was a duplicate from poor planning in absent group member, and since the split value in numpost was 50% the values were equivalent in both absent group member and dictator group member.  Aside from those duplications we ended up with the graph below to document the "stink score" for each group overall.

![totalsting.png](https://github.com/CSC510-2015-Axitron/project2/blob/master/img/totalstink.png?raw=true)


It is very difficult to make any sweeping generalizations about this data given the fact that it was anonymized prior to our analysis.  That the data was anonymized makes it difficult to test whether these metrics actually showed poor performance or not.  That said, with the data as it is we would assume that groups 2, 8, and 1 would have had more difficulty in producing what they were able to produce over the semester.  


#### Poor Communication

The table below describes the scoring for each group in the three categories for poor communication:

| Group Number | numpost | numcom | percom | Stink Score |
|:------------:|:-------:|:------:|:------:|:-----------:|
|       1      |    1    |   1    |   1    |      3      |
|       2      |    1    |   1    |   1    |      3      |
|       3      |    1    |   0    |   0    |      1      |
|       4      |    1    |   1    |   1    |      3      |
|       5      |    0    |   0    |   1    |      1      |
|       6      |    1    |   1    |   1    |      3      |
|       7      |    0    |   1    |   0    |      1      |
|       8      |    1    |   0    |   0    |      1      |
|       9      |    1    |   0    |   1    |      2      |


#### Poor Milstone Usage

| Group Number | missmile | nonlin | fewmile | incmile | StinkScore |
|:------------:|:--------:|:------:|:-------:|:-------:|:----------:|
|       1      |    1     |    1   |    0     |     0    |      2     |
|       2      |    1     |    0   |    0     |     0    |      1     |
|       3      |    0     |    0   |    0     |     0    |      0     |
|       4      |    0     |    0   |    0     |     0    |      0     |
|       5      |    0     |    0   |    0     |     0    |      0     |
|       6      |    0     |    0   |    0     |     0    |      0     |
|       7      |    1     |    1   |    0     |     1    |      3     |
|       8      |    1     |    1   |    0     |     1    |      3     |
|       9      |    0     |    0   |    0     |     0    |      0     |

#### Poor Planning

| Group Number | longtime | missmile | eqassgn | nonlin | shorttime | lincommit | Stink Score |
|:------------:|:--------:|:--------:|:-------:|:------:|:---------:|:---------:|:-----------:|
|       1      |    0     |    1     |    0    |   1    |     0     |     0     |      2      |
|       2      |    1     |    1     |    1    |   0    |     0     |     1     |      4      |
|       3      |    0     |    0     |    0    |   0    |     1     |     0     |      1      |
|       4      |    0     |    0     |    1    |   0    |     0     |     0     |      1      |
|       5      |    1     |    0     |    0    |   0    |     0     |     1     |      2      |
|       6      |    0     |    0     |    1    |   0    |     0     |     1     |      2      |
|       7      |    0     |    1     |    0    |   1    |     0     |     0     |      2      |
|       8      |    0     |    1     |    1    |   1    |     1     |     0     |      4      |
|       9      |    0     |    0     |    0    |   0    |     0     |     0     |      0      |

#### Absent Group Member

| Group Number | numiss | percom | eqassgn | numpost | StinkScore |
|:------------:|:------:|:------:|:-------:|:-------:|:----------:|
|       1      |   1    |   1    |    0    |    1    |     3      |
|       2      |   1    |   1    |    1    |    1    |     4      |
|       3      |   1    |   0    |    0    |    1    |     2      |
|       4      |   1    |   1    |    1    |    1    |     4      |
|       5      |   1    |   0    |    0    |    0    |     1      |
|       6      |   1    |   1    |    1    |    1    |     4      |
|       7      |   0    |   1    |    0    |    0    |     1      |
|       8      |   1    |   0    |    1    |    1    |     3      |
|       9      |   0    |   0    |    0    |    1    |     1      |

#### Dictator Group Member

| Group Number | numiss | percom | eqassgn | numpost | StinkScore |
|:------------:|:------:|:------:|:-------:|:-------:|:----------:|
|       1      |   0    |   1    |    0    |    1    |     2      |
|       2      |   1    |   0    |    0    |    1    |     2      |
|       3      |   1    |   0    |    0    |    1    |     2      |
|       4      |   0    |   0    |    1    |    1    |     2      |
|       5      |   0    |   0    |    0    |    0    |     0      |
|       6      |   0    |   0    |    1    |    1    |     2      |
|       7      |   0    |   0    |    0    |    0    |     0      |
|       8      |   1    |   0    |    0    |    1    |     2      |
|       9      |   0    |   0    |    0    |    1    |     1      |

## 10. Early Warning

We examined all 13 feature detectors and picked No.9 (Nonlinear Progress Momentum) as our early warning detector. This detector only looks at the due dates of milestones within each group. Our justification is as follows:

- Most of the groups had planned their milestones about 40 days before the project was due.
- All groups except one have proposed at least 4 milestones.
- Milestones serve as the checkpoints for measuring the progress of the group.
- Each milestones within the group requires equal amount of effort and time to work on.

Based on the above assumption, the linearity of milestone due dates vs. milestone number should reveal the planning strategy of the group. The regression equation for calculating the linearity has been described in the early section. The linearity was measured by the parameter of the second degree polynomial. That is, high linearity is expected to have very small value.

## 11. Early Warning Results

To evaluate the effectiveness of our early warning detector, the total stink score and the exact nonlinearity factor for each group are listed in the following table.

| Group Number | Total StinkScore | nonlin factor |
|:------------:|:----------------:|:-------------:|
|       1      |       12         |      3.21     |
|       2      |       14         |      2.71     |
|       3      |        6         |      0.13     |
|       4      |       10         |      0.25     |
|       5      |        4         |       N/A     |
|       6      |       11         |      1.06     |
|       7      |        7         |      5.74     |
|       8      |       13         |      6.99     |
|       9      |        4         |      0.01     |

It is found that the top three groups having the lowest stink score also have low nonlinerity factor. Respectively, they are 0.01, N/A, and 0.13. Here, the nonlinearity factor for group 5 was not determined because there are only two milestones defined by the group. However, the group having low nonlinearity factor does not necessarily have low stink score, which means that good planning does not guarantee better execution. If we examine the top three groups having highest stink scores (14, 13, and 12) all of them have high nonlinearity in their milestones (2.71, 6.99, and 3.21). This finding agrees with the belief that poor project initation and unrealistic expections is one of the causes for project failure.


---

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
