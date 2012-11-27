
# Project Name #

## A Post Archiver for Reddit ##

**a script written in Python**

***Dependencies:** [PRAW](https://github.com/praw-dev/praw), [snudown](https://github.com/reddit/snudown), Python 2.7 (Python 3.x not supported since snudown doesn't work in 3.x)

## Motivation ##

If you're addicted to reddit, then it's pretty likely stemming from the fact that it changed the way you live your life (or a part of it at least). Contained within their databases lies a huge treasure trove of information: academic, creative, informative, transformative, etc. It's true that a huge amount of the information that is accessible through reddit is through links, but the discussions on those links are often the best part about reddit. And then think about all the .self posts on all of reddit.

* Some future SOPA spin-off could limit the content of the internet, and perhaps make reddit delete old posts. 
* Although it seems unthinkable now, the popularity of reddit could possibly wane (a similar but clearly superior alternative, for example). Waning popularity translates into waning revenues, which might impact their data retention strategy -- older post might simply be deleted after reaching a certain age.
* A zombie apocalypse or mutant super virus eradicates modern civilization, ending the age of the internet, or at least the internet as we know it today. 

Or you can use your imagination. So, if you're looking for a quick, easy way to save for some of this knowledge for yourself, look no further (and I think this should be exclusively for personal use only, I don't know how happy reddit-as-a-business would be if you started mirroring their content while serving up advertisements).

This package provides a quick way to save a specific subset of that knowledge, and to save it in the most future proof way possible, while maintaining the readability of reddit in its original form.

## Operation ##

### Archiving Mode ###

The normal mode of operation for the software.

* Generates HTML files and CSS files that replicate the feeling of reddit without any of the extraneous data. Side-bar information and links, for example, will not be present. 
* An easily parsed file containing the snudown markdown of the post contents and self posts.

**To Do:** A mode that sets the location of the CSS file instead of copying a new one along side the html file every time.

### Archive HTML mode ###

This mode reads the easily-parsed archive files containing the snudown markdown content of comments and self posts and produces HTML output, along with associates CSS files. 

Useful for re-rendering html files after custom changes to this software. 

If file space per archival file is at a premium, then one could potentially only archive the markdown-formatted file and generate the HTML as needed.  
