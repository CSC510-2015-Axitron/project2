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

# whether to enable anonymizer
anonymizer = True
user_list = []

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

def convert(labels):
  array = []
  for label in labels:
    label = label['name']
    if not label : continue
    array.append(label)
  return '|'.join(array)

def dump1(u,issues):
  token = "INSERT TOKEN HERE" # <===
  request = urllib2.Request(u, headers={"Authorization" : "token "+token})
  v = urllib2.urlopen(request).read()
  w = json.loads(v)
  if not w: return False
  for event in w:
    issue_id = event['issue']['number']
    created_at = secs(event['created_at'])
    action = event['event']
    if not event.get('label'):
      label_name = " " #convert(event['issue']['labels'])
    else:
      label_name = event['label']['name']
    user = event['actor']['login']
    milestone = event['issue']['milestone']
    if milestone != None : milestone = milestone['title']
    assignee = event['issue']['assignee']
    if assignee != None : assignee = assignee['login']
    eventObj = L(when = created_at,
                 action = action,
                 what = label_name,
                 user = anonymize(user),
                 milestone = milestone,
                 assignee = anonymize(assignee))
    all_events = issues.get(issue_id)
    if not all_events: all_events = []
    all_events.append(eventObj)
    issues[issue_id] = all_events
  return True

def dump(u,issues):
  try:
    return dump1(u, issues)
  except Exception as e: 
    print(e)
    print("Contact TA")
    return False

def launchDump():
  page = 1
  issues = dict()
  while(True):
    doNext = dump('https://api.github.com/repos/opensciences/opensciences.github.io/issues/events?page=' + str(page), issues)
    print("page "+ str(page))
    page += 1
    if not doNext : break
  for issue, events in issues.iteritems():
    print("ISSUE " + str(issue))
    for event in events: print(event.show())
    print('')
    
launchDump()

