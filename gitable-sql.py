#  gitabel
#  the world's smallest project management tool
#  reports relabelling times in github (time in seconds since epoch)
#  thanks to dr parnin
#  todo:
#    - ensure events sorted by time
#    - add issue id
#    - add person handle

"""
You will need to add your authorization token in the code.
Here is how you do it.

1) In terminal run the following command

curl -i -u <your_username> -d '{"scopes": ["repo", "user"], "note": "OpenSciences"}' https://api.github.com/authorizations

2) Enter ur password on prompt. You will get a JSON response. 
In that response there will be a key called "token" . 
Copy the value for that key and paste it on line marked "token" in the attached source code. 

3) Run the python file. 

     python gitable.py

"""

from __future__ import print_function
import urllib2
import json
import re,datetime
import sys
import sqlite3
import ConfigParser
import os.path

def lCompare(item1, item2):
  if item1[0] == item2[0]:
    if item1[1] == item2[1]:
      if item1[2] == item2[2]:
        if item1[3] == item2[3]:
          print('duplicates: '+str(item1))
          return 0
        else:
          return 1 if item1[3] > item2[3] else -1
      else:
        return 1 if item1[2] > item2[2] else -1
    else:
      return int(item1[1] - item2[1])
  else:
    return item1[0] - item2[0]

class L():
  "Anonymous container"
  def __init__(i,**fields) : 
    i.override(fields)
  def override(i,d): i.__dict__.update(d); return i
  def __repr__(i):
    d = i.__dict__
    name = i.__class__.__name__
    return name+'{'+' '.join([':%s %s' % (k,pretty(d[k])) 
                     for k in i.show()])+ '}'
  def show(i):
    lst = [str(k)+" : "+str(v) for k,v in i.__dict__.iteritems() if v != None]
    return ',\t'.join(map(str,lst))

  
def secs(d0):
  d     = datetime.datetime(*map(int, re.split('[^\d]', d0)[:-1]))
  epoch = datetime.datetime.utcfromtimestamp(0)
  delta = d - epoch
  return delta.total_seconds()
 
def dump1(u,issues, config):
  token = config.get('options','token') # <===
  request = urllib2.Request(u, headers={"Authorization" : "token "+token})
  v = urllib2.urlopen(request).read()
  w = json.loads(v)
  if not w: return False
  for event in w:
    identifier = event['id']
    issue_id = event['issue']['number']
    issue_name = event['issue']['title']
    created_at = secs(event['created_at'])
    action = event['event']
    label_name = event['label']['name'] if 'label' in event else event['assignee']['login'] if action == 'assigned' else event['milestone']['title'] if action in ['milestoned', 'demilestoned'] else action
    user = event['actor']['login']
    milestone = event['issue']['milestone']
    if milestone != None : milestone = milestone['title']
    eventObj = L(ident=identifier,
                 when=created_at,
                 action = action,
                 what = label_name,
                 user = user,
                 milestone = milestone)
    issue_obj = issues.get(issue_id)
    if not issue_obj: issue_obj = [issue_name, []]
    all_events = issue_obj[1]
    all_events.append(eventObj)
    issues[issue_id] = issue_obj
  return True

def dump(u,issues,config):
  try:
    return dump1(u, issues, config)
  except Exception as e: 
    print(e)
    print("Contact TA")
    return False

def launchDump():
  if os.path.isfile("./gitable.conf"):
    config = ConfigParser.ConfigParser()
    config.read("./gitable.conf")
  else:
    print("gitable.conf not found, make sure to make one!")
    sys.exit()

  if not (config.has_option('options', 'token') and config.has_option('options', 'repo')):
    print("gitable.conf does not have both token and repo, fix!")
    sys.exit()

  dbFile = config.get('options', 'db') if config.has_option('options','db') else ':memory:'

  conn = sqlite3.connect(dbFile)

  #SQL stuffs
  conn.execute('''CREATE TABLE IF NOT EXISTS issue(id INTEGER, name VARCHAR(128),
        CONSTRAINT pk_issue PRIMARY KEY (id) ON CONFLICT ABORT)''')
  conn.execute('''CREATE TABLE IF NOT EXISTS milestone(id INTEGER, name VARCHAR(128),
        CONSTRAINT pk_milestone PRIMARY KEY(id) ON CONFLICT ABORT)''')

  #unsure if ignoring duplicate event tuples is a good idea, but the unique information is pretty much all we care about
  #duplicates aren't meaningful, so I guess it 's ok
  conn.execute('''CREATE TABLE IF NOT EXISTS event(issueID INTEGER NOT NULL, time DATETIME NOT NULL, action VARCHAR(128),
        label VARCHAR(128), user VARCHAR(128), milestone INTEGER, identifier INTEGER,
        CONSTRAINT pk_event PRIMARY KEY (issueID, time, action, label) ON CONFLICT IGNORE,
        CONSTRAINT fk_event_issue FOREIGN KEY (issueID) REFERENCES issue(id) ON UPDATE CASCADE ON DELETE CASCADE,
        CONSTRAINT fk_event_milestone FOREIGN KEY (milestone) REFERENCES milestone(id) ON UPDATE CASCADE ON DELETE CASCADE)''')
  nameNum = 1
  nameMap = dict()

  milestoneNum = 1
  milestoneMap = dict()

  page = 1
  issues = dict()
  while(True):
    url = 'https://api.github.com/repos/'+config.get('options','repo')+'/issues/events?page=' + str(page)
    doNext = dump(url, issues, config)
    print("page "+ str(page))
    page += 1
    if not doNext : break
  issueTuples = []
  eventTuples = []
  milestoneTuples = []
  for issue, issueObj in issues.iteritems():
    events = issueObj[1]
    issueTuples.append([issue, issueObj[0]]);
    print("ISSUE " + str(issue) + ", " + issueObj[0])
    for event in events:
      print(event.show())
      if not event.user in nameMap:
        nameMap[event.user] = config.get('options','repo')+'/user'+str(nameNum)
        nameNum+=1
      if event.action == 'assigned' and not event.what in nameMap:
        nameMap[event.what] = config.get('options','repo')+'/user'+str(nameNum)
        nameNum+=1
      if 'milestone' in event.__dict__ and not event.milestone in milestoneMap:
        milestoneMap[event.milestone] = milestoneNum
        milestoneTuples.append([milestoneMap[event.milestone], event.milestone])
        milestoneNum += 1
      if event.action in ['milestoned','demilestoned'] and not event.what in milestoneMap:
        milestoneMap[event.what] = milestoneNum
        milestoneTuples.append([milestoneMap[event.what], event.what])
        milestoneNum += 1
      eventTuples.append([issue, event.when, event.action, nameMap[event.what] if event.action == 'assigned' else milestoneMap[event.what] if event.action in ['milestoned','demilestoned'] else event.what, nameMap[event.user], milestoneMap[event.milestone] if 'milestone' in event.__dict__ else None, event.ident])
    print('')
  sorted(eventTuples, cmp=lCompare)
  try:
    conn.executemany('INSERT INTO issue VALUES (?,?)', issueTuples)
    conn.commit()
    conn.executemany('INSERT INTO milestone VALUES (?,?)', milestoneTuples)
    conn.commit()
    conn.executemany('INSERT INTO event VALUES (?, ?, ?, ?, ?, ?, ?)', eventTuples)
    conn.commit()
  except sqlite3.Error as er:
    print(er)

  conn.close()
    
launchDump()

