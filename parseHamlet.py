#!/bin/python
# Stuff to install
# apt-get python-bs4 libyaml-dev pythonyaml python-dev libffi-dev libssl-dev


from bs4 import BeautifulSoup 
from pprint import pprint
soup = BeautifulSoup(open("Hamlet.html"))
import re, yaml, sys, codecs
import tweepy
import time
from difflib import SequenceMatcher
from operator import itemgetter, attrgetter, methodcaller

import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()


with open("twitterCredentials.yaml", 'r') as stream:
    try:
    	settings=yaml.load(stream)        
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit(1)

print settings
f = codecs.open('tweetPlan.txt','w', encoding='utf-8')

auth = tweepy.OAuthHandler(settings['key'], settings['secret'])

if not settings['accessToken'] and not settings['accessTokenSecret']:
	try:
		redirect_url = auth.get_authorization_url()
		
		print redirect_url
		verifier = raw_input('Verifier:')
		print auth.get_access_token(verifier)
		sys.exit(0)

	except tweepy.TweepError:
	    print 'Error! Failed to get request token.'
	    sys.exit(1)
		    
auth.secure = True
try:
	auth.set_access_token(settings['accessToken'], unicode(settings['accessTokenSecret']))
except tweepy.TweepError:
    print 'Error! Failed to set access token.'
    sys.exit(1)

api = tweepy.API(auth)


def tweetToTwitter(tweet, original):
	line, tweetID = tweet

	f.write("%s / %s / %s\n" % (line, tweetID, original))

def split_list(a_list):
    half = len(a_list)/2
    return a_list[:half], a_list[half:]


class Dialogue:
	character = ""
	priorCharacter = ""
	dialogue = ""
	stageDirection = ""
	def __init__(self, character=None, priorCharacter=None, dialogue=None, stageDirection=stageDirection):
		self.character=character
		self.priorCharacter=priorCharacter
		self.dialogue=dialogue
		self.stageDirection=stageDirection
	def __str__(self):
		if (self.dialogue):
			return ("%s (to: %s): %s" % (self.character, self.priorCharacter, self.dialogue))
		if (self.stageDirection):
			return ("%s: %s" % (self.character, self.stageDirection))

	def __repr__(self):
		if (self.dialogue):
			return repr("%s (to: %s): %s" % (self.character, self.priorCharacter, self.dialogue))
		if (self.stageDirection):
			return repr("%s: %s" % (self.character, self.stageDirection))


play = []
character=None
priorCharacter=''
for line in soup.findAll(["h3", "a", "blockquote"]):
	if line.name == "h3":
		play.append(Dialogue(character="The Stage", stageDirection=line.text))
		character="The Stage"
	elif line.name == "a":
		if "name" in line.attrs and re.match(r'^speech.*',line['name']):
			priorCharacter=character
			character=line.b.text.strip("\n")			
	elif line.name == "blockquote":
		for dial in line.findAll(["a","i"]):
			
			if dial.name == "a":
				play.append(Dialogue(character=character, priorCharacter=priorCharacter, dialogue=dial.text))
			if dial.name == "i":
				play.append(Dialogue(character="The Stage", priorCharacter=None, stageDirection=dial.text))

	else:
		print(line, line.name)
	#print(quote.i)
	#print(quote.a)

#character=[]
#for line in play:
#	character.append(line.character)

#print(set(character))
oldTweetID={}
oldTweetID['user']=''
oldTweetID['id']=None


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def searchTweets(term):
	print term
	time.sleep(10)
	maxSimilar=0
	tweets=api.search(q="%s" % (' '.join(term)), rpp=200, lang="en")
	returntweets=[]
	for tweet in tweets:
		similarity=similar(tweet.text, line.dialogue)
		returntweets.append({'text':tweet.text, 'id':tweet.id, 'user':tweet.user.screen_name, 'similar':similarity})
		if similarity > maxSimilar:
			maxSimilar = similarity
	print maxSimilar
	if maxSimilar < .1:
		returntweets = []
		term1, term2 = split_list(term)
		if term1:
			returntweets.append(searchTweets(term1))
		if term2:
			returntweets.append(searchTweets(term2))


		
		

	return returntweets			


	
#for line in play:
#	print line


def tweetToText(tweets, line):	

	for tweetList in tweets:
		if '0' in tweetList and type(tweetList[0]) is list:
			tweetToText(tweetList, line)


	
	sortedTweets = sorted(tweets, key=itemgetter('similar'))		

	if sortedTweets[0]:
		if line.priorCharacter:
			prior = " to %s" % (line.priorCharacter)
		else:
			prior = ""

		return("Retweet: (%s%s): %s" % (line.character, prior, tweets[0]['text']), tweets[0]['id'])
	else:
		return("Tweet: (%s%s): %s" % (line.character, prior, line.dialogue), None)
		
		

for key, line in enumerate(play):
	if key >= 20:
		break

	'''	
	if oldTweetID['user']:
		oldTweetID['user']=".@"+oldTweetID['user']

	if len("%s %s" % (oldTweetID['user'], line.dialogue)) <= 140:

		tweet=api.update_status(status="%s %s" % (oldTweetID['user'], line.dialogue), in_reply_to_status_id=oldTweetID)
		print tweet.id
		pprint(vars(tweet))
		print tweet.user.screen_name
		oldTweetID['id']=tweet.id
		oldTweetID['user']=tweet.user.screen_name
	'''

	if (line.stageDirection):
		tweetToTwitter(("Tweet: %s" % (line.stageDirection), None), line)


	if (line.dialogue):	
		terms = line.dialogue.split(" ")		
		tweets = searchTweets(terms)
		
		tweetToTwitter(tweetToText(tweets, line), line)


		
			
f.close()
	


