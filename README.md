# redditPostArchiver  #

### A Post Thread Archiver for Reddit ###

**a script written in Python**

**Dependencies:** Either

 * [PRAW](https://github.com/praw-dev/praw), [snudown](https://github.com/reddit/snudown), Python 2.7 (Python 3.x not supported in official snudown branch)
 * [PRAW](https://github.com/praw-dev/praw), [Chid's snudown fork](https://github.com/chid/snudown), Python 3

## Quick Start ##

As a regular user, install praw:

    sudo pip install praw  

Snudown was recently removed from the pip database, it seems, so to install snudown:

    git clone https://github.com/reddit/snudown.git
    cd snudown
    sudo python setup.py install

Navigate to the folder with archive.py and run the script. An html file will be written into that same folder. To choose what post is to be archived simply provide the post ID as an argument to the script (e.g., `./archiver 15zmjl`).

As of now, only posts and the associated comment threads can be archived. Saving a specific comment thread, starting with a comment, will be supported in the future. 

## Motivation ##

If you're addicted to reddit, then it's pretty likely stemming from the fact that it changed the way you live your life (or a part of it at least). Contained within their databases lies a huge treasure trove of information: academic, creative, informative, transformative, etc. It's true that a huge amount of the information that is accessible through reddit is through links, but the discussions on those links are often the best part about reddit. And then think about all the .self posts on all of reddit.

* Some future SOPA spin-off could limit the content of the internet, and perhaps make reddit delete old posts. 
* Although it seems unthinkable now, the popularity of reddit could possibly wane (a similar but clearly superior alternative, for example). Waning popularity translates into waning revenues, which might impact their data retention strategy -- older post might simply be deleted after reaching a certain age.
* A zombie apocalypse or mutant super virus eradicates modern civilization, ending the age of the internet, or at least the internet as we know it today. 

Or you can use your imagination. So, if you're looking for a quick, easy way to save for some of this knowledge for yourself, look no further (and I think this should be exclusively for personal use only, I don't know how happy reddit-as-a-business would be if you started mirroring their content while serving up advertisements).

This package provides a quick way to save a specific subset of that knowledge, and to save it in the most future proof way possible, while maintaining the readability of reddit in its original form.


