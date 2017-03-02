#Bot for auto-managing subreddits

How to set this bot up:

* Install praw if necessary. This bot was made on version 4.3.0, anything below 4.0 isn't compatible.

* Set up your bot's app

* Edit praw.ini.example with your bot's app and customize stuff like membercap and what not

* rename it to praw.ini

* Run bot.py to kick inactive members and add new ones.

Optional: set up a cron to run bot.py automatically.


I also recommend running "bot.py -retry" every 15-30 minutes as a backup in case the bot failed previously,
in which case it will start from where it left off.

If it didn't fail, the script will simply stop without any request being made to reddit's API.

This bot has a small limitation which is good to know:

Reddit prevents any listing being made beyond 1000 items. 
As this bot checks activity by loading all submissions and comments in the last [hour_limit] hours,
The listing will either stop when an item was made more than [hour_limit] hours ago, or at item #1000.

If item #1000 is fetched and was made within the last [hour_limit] hours (which is rare but can realistically happen for comments, especially on a more active subreddit)
there is a failsafe in place so that members who haven't been logged as being active can be given the benefit of the doubt,
and the bot will manually check their overview to see if they have been active in the subreddit or not.

Once again, the 1000 item limitation could theoretically prevent the bot from seeing a valid activity if the user
in question made 1000 comments or submissions and their 1001st comment was made in the subreddit within the allowed time frame.

That would be VERY rare, but still possible. 

I haven't tested it, but there might also be a problem for subreddits with over 1000 members due to this limitation.