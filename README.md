# redditPostArchiver  #

### A Post Thread Archiver for Reddit ###

**a script written in Python**

**Dependencies:**
    [PRAW](https://github.com/praw-dev/praw),
    [requests](http://docs.python-requests.org/en/master/),
    [pyyaml](https://github.com/yaml/pyyaml),
    [arrow](http://arrow.readthedocs.io/en/latest/),
    Python 3

## Quick Start ##

As a regular user, install:

    sudo pip install requests
    sudo pip install praw
    sudo pip install pyyaml
    sudo pip install arrow

Visit the PRAW documentation and follow the instructions for a script installation:

https://praw.readthedocs.io/en/latest/getting_started/authentication.html

In short, you need to register a new app with Reddit:

https://www.reddit.com/prefs/apps/

and grab your client ID and client secret from the app page:

![client ID under the blue PRAW OAuth2 Test logo on the top left, client secret beside 'secret', and add a redirect uri at the bottom, which isn't used but still required](https://raw.githubusercontent.com/pl77/redditPostArchiver/master/CreateApp.png "client ID under the blue PRAW OAuth2 Test logo on the top left, client secret beside 'secret', and add a redirect uri at the bottom, which isn't used but still required")

Edit the included "credentials.yml" file to replace "test" with the variables from your reddit account.

#### archive.py ####

Navigate to the folder with archive.py and run the script. An html file will be written into that same folder. To choose what post is to be archived simply provide the post ID as an argument to the script (e.g., `python archiver.py 15zmjl`).

The output is a webpage that looks like this:

![screenshot of the saved thread](https://raw.githubusercontent.com/pl77/redditPostArchiver/master/savedthread.png "screenshot of the saved thread")

#### postids.py ####

Navigate to the folder with postids.py and run the script. A text file will be written into that same folder. To choose which author is to be archived simply provide the author's name (username) as an argument: `python postids.py GallowBoob`

#### subpostids.py ####

Navigate to the folder with subpostids.py and run the script. A CSV file will be written into that same folder. To choose which subreddit is to be archived simply provide the subreddit name as an argument:`python subpostids.py opendirectories`

## Motivation ##

If you're addicted to reddit, then it's pretty likely stemming from the fact that it changed the way you live your life (or a part of it at least). Contained within their databases lies a huge treasure trove of information: academic, creative, informative, transformative, etc. It's true that a huge amount of the information that is accessible through reddit is through links, but the discussions on those links are often the best part about reddit. And then think about all the .self posts on all of reddit.

* Some future SOPA spin-off could limit the content of the internet, and perhaps make reddit delete old posts. 
* Although it seems unthinkable now, the popularity of reddit could possibly wane (a similar but clearly superior alternative, for example). Waning popularity translates into waning revenues, which might impact their data retention strategy -- older post might simply be deleted after reaching a certain age.
* A zombie apocalypse or mutant super virus eradicates modern civilization, ending the age of the internet, or at least the internet as we know it today. 

Or you can use your imagination. So, if you're looking for a quick, easy way to save for some of this knowledge for yourself, look no further (and I think this should be exclusively for personal use only, I don't know how happy reddit-as-a-business would be if you started mirroring their content while serving up advertisements).

This package provides a quick way to save a specific subset of that knowledge, and to save it in the most future proof way possible, while maintaining the readability of reddit in its original form.


