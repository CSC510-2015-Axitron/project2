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
    issue_id = event['issue']['number']
    if not event.get('label'): continue
    created_at = secs(event['created_at'])
    action = event['event']
    label_name = event['label']['name']
    user = event['actor']['login']
    milestone = event['issue']['milestone']
    if milestone != None : milestone = milestone['title']
    eventObj = L(when=created_at,
                 action = action,
                 what = label_name,
                 user = user,
                 milestone = milestone)
    all_events = issues.get(issue_id)
    if not all_events: all_events = []
    all_events.append(eventObj)
    issues[issue_id] = all_events
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
  conn.execute('''CREATE TABLE IF NOT EXISTS event(issueID INTEGER NOT NULL, time DATETIME NOT NULL, action VARCHAR(128),
        label VARCHAR(128), user VARCHAR(128),
        CONSTRAINT pk_event PRIMARY KEY (issueID, time) ON CONFLICT ABORT,
        CONSTRAINT fk_event_issue FOREIGN KEY (issueID) REFERENCES issue(id) ON UPDATE CASCADE ON DELETE CASCADE)''')

  nameMap = {}

  page = 1
  issues = dict()
  while(True):
    url = 'https://api.github.com/repos/'+config.get('options','repo')+'/issues/events?page=' + str(page)
    doNext = dump(url, issues, config)
    print("page "+ str(page))
    page += 1
    if not doNext : break
  for issue, events in issues.iteritems():
    print("ISSUE " + str(issue))
    for event in events: print(event.show())
    print('')
    
launchDump()

