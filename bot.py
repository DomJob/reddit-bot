import praw, random, time, pickle, sys, os, configparser, datetime

class Bot:
    def __init__(self, botInfo):
        self.botInfo = botInfo
        self.directory = botInfo['directory']
        self.testing = (botInfo['testing'].lower() == 'true')
        if self.testing:
            self.log("Test run initiated")
        
        
        self.todoList = ['getInactiveMembers','selectNewMembers','kickUsers','addUsers','flairUsers','postRecap']
        
        self.doubleCheckSubmissions = True
        self.doubleCheckComments = True
        
        self.toBeKicked = []
        self.toBeAdded = []
        self.userNumbers = {}
        
        self.activeMembers = []
        self.timeLimit = time.time() - int(self.botInfo['hour_limit']) * 60 * 60
    
    def run(self):
        self.log("Running the bot - To do: %s" % ", ".join(self.todoList))
        self.loadReddit()
        
        while self.todoList != []:
            action = self.todoList[0]
            self.log("Next action: %s" % action)
            
            if action == 'getInactiveMembers':
                self.getInactiveMembers()
            if action == 'selectNewMembers':
                self.selectNewMembers()
            if action == 'kickUsers':
                self.kickUsers()
            if action == 'addUsers':
                self.addUsers()
            if action == 'flairUsers':
                self.flairUsers()
            if action == 'postRecap':
                self.postRecap()
            
            self.todoList.pop(0)
            self.logState()
    
    def getInactiveMembers(self):
        self.log("Getting list of inactive members...")
        self.memberList = self.getMemberList()
        self.getActiveMembers()
        number = 1
        
        for username in self.memberList:
            if username not in self.activeMembers:
                kickUser = True
                if self.doubleCheckSubmissions:
                    if self.hasUserPosted(username):
                        kickUser = False
                
                if self.doubleCheckComments:
                    if self.hasUserCommented(username):
                        kickUser = False
            
                if kickUser:
                    self.log("  /u/%s has been inactive" % username)
                    self.toBeKicked.append(username)
                    self.userNumbers[username] = number
            
            number += 1
            
    def selectNewMembers(self):
        numberOfMembersToAdd = int(self.botInfo['membercap']) - len(self.memberList) + len(self.toBeKicked)
        self.log("Getting %d new members" % numberOfMembersToAdd)
        numberPicked = 0
        for comment in self.reddit.subreddit("all").stream.comments():
            username = str(comment.author)
            
            if 'bot' in username.lower():
                continue
            
            karma = comment.author.comment_karma
            
            if karma < 1000 or karma > 75000:
                continue
                
            self.log("  /u/%s selected" % username)
            
            self.toBeAdded.append(username)
            numberPicked+=1
            
            if numberPicked == numberOfMembersToAdd:
                break
        
    def kickUsers(self):
        self.log("Kicking users")
        if self.testing:
            return
        
        for username in self.toBeKicked:
            self.subreddit.contributor.remove(username)
            self.flairUser(username, 'Kicked', 'kicked')
            self.log("Kicked /u/%s" % username)
        
    def addUsers(self):
        self.log("Adding users")
        if self.testing:
            return
            
        for username in self.toBeAdded:
            self.subreddit.contributor.add(username)
            self.log("  Added /u/%s" % username)
        
    def flairUsers(self):
        self.log("Flairing users")
        
        newMemberList = self.getMemberList()
        if self.testing:
            newMemberList += self.toBeAdded
        
        number = 1
        
        for username in newMemberList:
            flairText = "#%d" % number
            self.userNumbers[username] = number
            
            if username in self.toBeAdded:
                flairCSS = 'numbernew'
            else:
                flairCSS = 'number'
                
            self.flairUser(username, flairText, flairCSS)
            number += 1
        
    def postRecap(self):
        self.log("Generating and posting the recap... ", False)
        
        recapTitle = '%s - Bot Recap' % time.strftime('%Y-%m-%d', time.gmtime())
        recapBody = "Kicked users:\n\n"
        
        for username in self.toBeKicked:
            recapBody += "* \#%d - /u/%s\n\n" % (self.userNumbers[username], username)
            
        recapBody += "Added users:\n\n"
        
        for username in self.toBeAdded:
            recapBody += "* \#%d - /u/%s\n\n" % (self.userNumbers[username], username)
        
        if not self.testing:
            self.subreddit.submit(recapTitle, recapBody).mod.distinguish()
        else:
            open('recap_test.txt','w').write(recapBody)
        self.log("posted!")
        
    def flairUser(self, username, flairText, flairCSS):
        if self.testing:
            return
        
        self.log("Flairing /u/%s to %s - CSS %s" % (username, flairText, flairCSS) )
        self.subreddit.flair.set(username, flairText, flairCSS)
        
    def loadReddit(self):
        self.log("Loading reddit...", False)
        
        self.reddit = praw.Reddit(client_id=botInfo['bot']['client_id'],
                                    client_secret=botInfo['bot']['client_secret'],
                                    user_agent=botInfo['bot']['user_agent'],
                                    username=botInfo['bot']['username'],
                                    password=botInfo['bot']['password'])
        self.subreddit = self.reddit.subreddit(self.botInfo['subreddit'])
        
        self.log("done")
        
    def getMemberList(self):
        self.log("Fetching member list...", False)
        memberList = []
        
        for member in self.subreddit.contributor(limit=None):
            username = str(member)
            if username not in ['Kovmar',self.botInfo['bot']['username']]: # Add users in this list to whitelist them
                memberList.append(username)
        
        memberList.reverse()
        self.log("done")
        return memberList
        
    def getActiveMembers(self):
        self.log("Getting all active members")
        
        self.log(" Getting recent submissions...")
        counter = 0
        for submission in self.subreddit.new(limit=1000):
            counter += 1
            author = str(submission.author)
            
            if author not in self.activeMembers:
                self.log("  /u/%s has been active" % author)
                self.activeMembers.append(author)

            if submission.created_utc < self.timeLimit:
                self.doubleCheckSubmissions = False
                break
        
        self.log(" %d submissions" % counter)
        
        self.log(" Getting recent comments")
        
        counter = 0
        for comment in self.subreddit.comments(limit=1000):
            counter += 1
            author = str(comment.author)
            
            if author not in self.activeMembers:
                self.log("  /u/%s has been active" % author)
                self.activeMembers.append(author)
            
            if comment.created_utc < self.timeLimit:
                self.doubleCheckComments = False
                break
        
        self.log(" %d comments" % counter)
        
        if self.doubleCheckSubmissions:
            self.log("  Submissions will be double checked")
        if self.doubleCheckComments:
            self.log("  Comments will be double checked")
        
    def logState(self):
        self.log("Logging the state")
        tmp = [self.reddit, self.subreddit]
        self.reddit, self.subreddit = None, None
        
        stateFile = '%s/botstate.pkl' % (self.directory)
        with open(stateFile, 'wb') as file:
            pickle.dump(self, file, pickle.HIGHEST_PROTOCOL)
        
        self.reddit, self.subreddit = tmp[0], tmp[1]
    
    def hasUserPosted(self, username):
        self.log("Manually checking submissions of /u/%s" % username)
        
        for submission in self.reddit.redditor(username).submissions.new(limit=1000):
            if submission.created_utc < self.timeLimit:
                return False
            elif submission.subreddit.display_name == self.botInfo['subreddit']:
                return True
        
        return False
        
    def hasUserCommented(self, username):
        self.log("Manually checking comments of /u/%s" % username)
        
        for comment in self.reddit.redditor(username).comments.new(limit=1000):
            if comment.created_utc < self.timeLimit:
                return False
            elif comment.subreddit.display_name == self.botInfo['subreddit']:
                return (True, comment.id, comment.created_utc, self.timeLimit)
        
        return False

    def log(self, message, endLine = True):
        currentTime = time.strftime('%H:%M:%S', time.gmtime())
        toLog = "%s : %s" % (currentTime, message)
        if endLine:
            print(toLog)
            toLog += "\n"
        else:
            print(toLog, end=' ')
        date = time.strftime('%Y-%m-%d', time.gmtime())
        open('%s/logs/%s.log' % (self.directory, date),'a').write(toLog)



        
directory = os.path.dirname(os.path.realpath(__file__))
        
config = configparser.ConfigParser()
config.read(directory+'/praw.ini')

botInfo = dict(config._sections['config'])
botInfo['directory'] = directory
botInfo['bot'] = dict(config._sections['bot'])

try:
    os.mkdir(directory+"/logs")
except:
    pass

if __name__ == "__main__":
    if len(sys.argv) == 1:
        bot = Bot(botInfo)
        bot.run()
    else:
        argument = sys.argv[1]
        
        if argument == "-retry":
            stateFile = '%s/botstate.pkl' % (directory)
            
            try:
                with open(stateFile, 'rb') as file:
                    bot = pickle.load(file)
                
                if bot.todoList != []:
                    bot.run()
            except:
                print("No need for bot to restart")
