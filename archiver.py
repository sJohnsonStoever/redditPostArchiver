#!/usr/bin/env python
# -*- coding: utf-8 -*-

import praw
import snudown
import datetime
import time
import re
import sys

""" 
Customization Configuration

"""
# Default postID: #
postID='15zmjl'
# Path to which to output the file #
outputFilePath='./'
# The Path to the stylesheet, relative to where the html file will be stored #
pathToCSS='css/style.css'

"""
Reddit Post Archiver
By Samuel Johnson Stoever
"""

if len(sys.argv) == 1:
    print('No post ID was provided. Using default postID.')
elif len(sys.argv) > 2:
    print('Too Many Arguments. Using default postID.')
else:
    postID = sys.argv[1]
outputFilePath = outputFilePath + postID + '.html'
htmlFile = open(outputFilePath,'w')
monthsList = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']


def writeHeader(posttitle):
    htmlFile.write('<!DOCTYPE html>\n<html>\n<head>\n')
    htmlFile.write('\t<meta charset="utf-8"/>\n')
    htmlFile.write('\t<link type="text/css" rel="stylesheet" href="' + pathToCSS +'"/>\n')
    htmlFile.write('\t<title>' + posttitle + '</title>\n')
    htmlFile.write('</head>\n<body>\n')

def parsePost(postObject):
    writeHeader(postObject.title)
    postObject.replace_more_comments()
    postAuthorName = ''
    postAuthorExists = 0
    try:
        postAuthorName = postObject.author.name
        postAuthorExists = 1
    except AttributeError:
    	postAuthorExists = 0
    if postObject.is_self:
        # The post is a self post
        htmlFile.write('<div class="title">\n')
        htmlFile.write(postObject.title)
        htmlFile.write('\n<br/><strong>')
        if postAuthorExists:
            htmlFile.write('Posted by <a id="userlink" href="' + postObject.author._url)
            htmlFile.write('">')
            htmlFile.write(postAuthorName)
            htmlFile.write('</a>. </strong><em>')
        else:
            htmlFile.write('Posted by [Deleted]. </strong><em>')
        htmlFile.write('Posted at ')
        postDate = time.gmtime(postObject.created_utc)
        htmlFile.write(str(postDate.tm_hour) + ':')
        htmlFile.write(str(postDate.tm_min) + ' UTC on ')
        htmlFile.write(monthsList[postDate.tm_mon-1] + ' ')
        htmlFile.write(str(postDate.tm_mday) + ', ' + str(postDate.tm_year))
        htmlFile.write('. ' + str(postObject.ups - postObject.downs))
        htmlFile.write(' Points. </em><em>(self.<a id="selfLink" href="')
        htmlFile.write(postObject.subreddit._url)
        htmlFile.write('">' + postObject.subreddit.display_name)
        htmlFile.write('</a>)</em><em>')
        htmlFile.write(' (<a id="postpermalink" href="')
        htmlFile.write(postObject.permalink)
        htmlFile.write('">Permalink</a>)</em>\n')
        htmlFile.write('<div class="post">\n')
        htmlFile.write(snudown.markdown(fixMarkdown(postObject.selftext)))
        htmlFile.write('</div>\n')
        htmlFile.write('</div>\n')
        for comment in postObject._comments:
            parseComment(comment, postAuthorName, postAuthorExists)
        htmlFile.write('<hr id="footerhr">\n')
        htmlFile.write('<div id="footer"><em>Archived on ')
        htmlFile.write(str(datetime.datetime.utcnow()))
        htmlFile.write(' UTC</em></div>')
        htmlFile.write('\n\n</body>\n</html>\n')
        #Done
    else:
        # The post is a link post
        htmlFile.write('<div class="title">\n')
        htmlFile.write('<a id="postlink" href="' + postObject.url)
        htmlFile.write('">')
        htmlFile.write(postObject.title)
        htmlFile.write('</a>\n<br/><strong>')
        if postAuthorExists:
            htmlFile.write('Posted by <a id="userlink" href="' + postObject.author._url)
            htmlFile.write('">')
            htmlFile.write(postAuthorName)
            htmlFile.write('</a>. </strong><em>')
        else:
            htmlFile.write('Posted by [Deleted]. </strong><em>')
        htmlFile.write('Posted at ')
        postDate = time.gmtime(postObject.created_utc)
        htmlFile.write(str(postDate.tm_hour) + ':')
        htmlFile.write(str(postDate.tm_min) + ' UTC on ')
        htmlFile.write(monthsList[postDate.tm_mon-1] + ' ')
        htmlFile.write(str(postDate.tm_mday) + ', ' + str(postDate.tm_year))
        htmlFile.write('. ' + str(postObject.ups - postObject.downs))
        htmlFile.write(' Points. </em><em>(<a id="selfLink" href="')
        htmlFile.write(postObject.subreddit._url)
        htmlFile.write('">' + postObject.subreddit.display_name)
        htmlFile.write('</a> Subreddit)</em><em>')
        htmlFile.write(' (<a id="postpermalink" href="')
        htmlFile.write(postObject.permalink)
        htmlFile.write('">Permalink</a>)</em>\n')
        htmlFile.write('<div class="post">\n<p>\n')
        htmlFile.write(postObject.url)
        htmlFile.write('</p>\n</div>\n')
        htmlFile.write('</div>\n')
        for comment in postObject._comments:
            parseComment(comment, postAuthorName, postAuthorExists)
        htmlFile.write('<hr id="footerhr">\n')
        htmlFile.write('<div id="footer"><em>Archived on ')
        htmlFile.write(str(datetime.datetime.utcnow()))
        htmlFile.write(' UTC</em></div>')
        htmlFile.write('\n\n</body>\n</html>\n')
def parseComment(redditComment, postAuthorName, postAuthorExists, isRoot=True):
    commentAuthorName = ''
    commentAuthorExists = 0
    try:
        commentAuthorName = redditComment.author.name
        commentAuthorExists = 1
    except AttributeError:
        commentAuthorExists = 0
    if isRoot:
        htmlFile.write('<div id="' + str(redditComment.id))
        htmlFile.write('" class="comment">\n')
    else:
        htmlFile.write('<div id="' + str(redditComment.id)) 
        htmlFile.write('" class="comment" style="margin-bottom:10px;margin-left:0px;">\n')
    htmlFile.write('<div class="commentinfo">\n')
    if commentAuthorExists:
        if postAuthorExists and postAuthorName == commentAuthorName:
            htmlFile.write('<a href="' + redditComment.author._url)
            htmlFile.write('" style="color: #fff; background: #00F; border-radius: 3px;">' + commentAuthorName + '</a> <em>')
        else:
            htmlFile.write('<a href="' + redditComment.author._url)
            htmlFile.write('">' + commentAuthorName + '</a> <em>')
    else:
        htmlFile.write('<strong>[Deleted]</strong> <em>')
    htmlFile.write(str(redditComment.ups - redditComment.downs))
    htmlFile.write(' Points </em><em>')
    htmlFile.write('Posted at ')
    postDate = time.gmtime(redditComment.created_utc)
    htmlFile.write(str(postDate.tm_hour) + ':')
    htmlFile.write(str(postDate.tm_min) + ' UTC on ')
    htmlFile.write(monthsList[postDate.tm_mon-1] + ' ')
    htmlFile.write(str(postDate.tm_mday) + ', ' + str(postDate.tm_year))
    htmlFile.write('</em></div>\n')
    htmlFile.write(snudown.markdown(fixMarkdown(redditComment.body)))
    for reply in redditComment._replies:
        parseComment(reply, postAuthorName, postAuthorExists, False)
    htmlFile.write('</div>\n')
    #Done
def fixMarkdown(markdown):
    newMarkdown = markdown.encode('utf8')
    return re.sub('\&gt;', '>', newMarkdown)
# End Function Definitions
r = praw.Reddit(user_agent='RedditPostArchiver Bot, version 0.93')
parsePost(r.get_submission(submission_id=postID))
htmlFile.close()
