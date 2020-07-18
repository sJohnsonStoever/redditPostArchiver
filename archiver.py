#!/usr/bin/env python3
import datetime
import os
import sys
import time

import arrow
import praw
import yaml
from prawcore.exceptions import NotFound
from requests.exceptions import HTTPError

""" 
Customization Configuration

"""
# Default post_id: #
post_id = '7i2w7i'
# Path to which to output the file #
# output_file_path = './'
# The Path to the stylesheet, relative to where the html file will be stored #
path_to_css = 'css/style.css'

"""
Reddit Post Archiver
By Samuel Johnson Stoever
"""
bulk_ids = False
postfname = None

if len(sys.argv) == 1:
    print('No post ID was provided. Using default post_id.')
elif len(sys.argv) == 3 and sys.argv[1] == '-i':
    bulk_ids = True
    postfname = sys.argv[2]
    print('Bulk processing detected. Using filename', postfname)
elif len(sys.argv) > 2:
    print('Too Many Arguments. Using default post_id.')
else:
    post_id = sys.argv[1]
monthsList = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
              'November', 'December']


def write_header(posttitle):
    html_file.write('<!DOCTYPE html>\n<html>\n<head>\n')
    html_file.write('\t<meta charset="utf-8"/>\n')
    html_file.write('\t<link type="text/css" rel="stylesheet" href="' + path_to_css + '"/>\n')
    html_file.write('\t<title>' + posttitle + '</title>\n')
    html_file.write('</head>\n<body>\n')


def parse_post(post_object):
    write_header(post_object.title)
    post_object.comments.replace_more()
    post_author_name = ''
    try:
        post_author_name = post_object.author.name
        post_author_exists = 1
    except AttributeError:
        post_author_exists = 0
    html_file.write('<div class="title">\n')
    if post_object.is_self:
        # The post is a self post
        html_file.write(post_object.title)
        html_file.write('\n<br/><strong>')
    else:
        # The post is a link post
        html_file.write('<a id="postlink" href="' + post_object.url)
        html_file.write('">')
        html_file.write(post_object.title)
        html_file.write('</a>\n<br/><strong>')
    if post_author_exists:
        html_file.write('Posted by <a id="userlink" href="https://www.reddit.com/' + post_object.author._path)
        html_file.write('">')
        html_file.write(post_author_name)
        html_file.write('</a>. </strong><em>')
    else:
        html_file.write('Posted by [Deleted]. </strong><em>')
    html_file.write('Posted at ')
    post_date = time.gmtime(post_object.created_utc)
    html_file.write(str(post_date.tm_hour) + ':')
    html_file.write(str(post_date.tm_min) + ' UTC on ')
    html_file.write(monthsList[post_date.tm_mon - 1] + ' ')
    html_file.write(str(post_date.tm_mday) + ', ' + str(post_date.tm_year))
    html_file.write('. ' + str(post_object.ups - post_object.downs))
    if post_object.is_self:
        html_file.write(' Points. </em><em>(self.<a id="selfLink" href="https://www.reddit.com/')
    else:
        html_file.write(' Points. </em><em>(<a id="selfLink" href="https://www.reddit.com/')
    html_file.write(post_object.subreddit._path)
    html_file.write('">' + post_object.subreddit.display_name)
    if post_object.is_self:
        html_file.write('</a>)</em><em>')
    else:
        html_file.write('</a> Subreddit)</em><em>')
    html_file.write(' (<a id="postpermalink" href="https://www.reddit.com')
    html_file.write(post_object.permalink)
    html_file.write('">Permalink</a>)</em>\n')
    if post_object.is_self and post_object.selftext_html:
        html_file.write('<div class="post">\n')
        html_file.write(post_object.selftext_html)
        html_file.write('</div>\n')
    elif post_object.is_self:
        html_file.write('<div class="post">\n')
        html_file.write('')
        html_file.write('</div>\n')
    else:
        html_file.write('<div class="post">\n<p>\n')
        html_file.write(post_object.url)
        html_file.write('</p>\n</div>\n')
    html_file.write('</div>\n')
    for comment in post_object._comments:
        parse_comment(comment, post_author_name, post_author_exists)
    html_file.write('<hr id="footerhr">\n')
    html_file.write('<div id="footer"><em>Archived on ')
    html_file.write(str(datetime.datetime.utcnow()))
    html_file.write(' UTC</em></div>')
    html_file.write('\n\n</body>\n</html>\n')


def parse_comment(reddit_comment, post_author_name, post_author_exists, is_root=True):
    comment_author_name = ''
    try:
        comment_author_name = reddit_comment.author.name
        comment_author_exists = 1
    except AttributeError:
        comment_author_exists = 0
    if is_root:
        html_file.write('<div id="' + str(reddit_comment.id))
        html_file.write('" class="comment">\n')
    else:
        html_file.write('<div id="' + str(reddit_comment.id))
        html_file.write('" class="comment" style="margin-bottom:10px;margin-left:0px;">\n')
    html_file.write('<div class="commentinfo">\n')
    if comment_author_exists:
        if post_author_exists and post_author_name == comment_author_name:
            html_file.write('<a href="https://www.reddit.com/' + reddit_comment.author._path)
            html_file.write('" class="postOP-comment">' + comment_author_name + '</a> <em>')
        else:
            html_file.write('<a href="https://www.reddit.com/' + reddit_comment.author._path)
            html_file.write('">' + comment_author_name + '</a> <em>')
    else:
        html_file.write('<strong>[Deleted]</strong> <em>')
    html_file.write(str(reddit_comment.ups - reddit_comment.downs))
    html_file.write(' Points </em><em>')
    html_file.write('Posted at ')
    post_date = time.gmtime(reddit_comment.created_utc)
    html_file.write(str(post_date.tm_hour) + ':')
    html_file.write(str(post_date.tm_min) + ' UTC on ')
    html_file.write(monthsList[post_date.tm_mon - 1] + ' ')
    html_file.write(str(post_date.tm_mday) + ', ' + str(post_date.tm_year))
    html_file.write('<a href=https://www.reddit.com')
    html_file.write(reddit_comment.permalink)
    html_file.write("> (Permalink) </a>")
    html_file.write('</em></div>\n')
    if reddit_comment.body_html:
        html_file.write(reddit_comment.body_html)
    else:
        html_file.write(reddit_comment.body)
    for reply in reddit_comment._replies:
        parse_comment(reply, post_author_name, post_author_exists, False)
    html_file.write('</div>\n')


cred_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.yml')
credentials = yaml.load(open(cred_path))

r = praw.Reddit(client_id=credentials['client_id'],
                client_secret=credentials['client_secret'],
                user_agent=credentials['user_agent'])

if bulk_ids:
    id_list = list()
    with open(postfname, 'r', encoding='UTF-8') as postids:
        for pid in postids:
            pid = pid.rstrip()
            id_list.append(pid.rstrip())
    for post_id in id_list:
        filedate = arrow.now().timestamp
        basedir = "/rpa" if os.environ.get('DOCKER', '0') == '1' else '.'
        output_file_path = "{basedir}/{post_id}_{timestamp}.html".format(basedir=basedir, post_id=post_id, timestamp=filedate)
        try:
            the_post = r.submission(id=post_id)
            with open(output_file_path, 'w', encoding='UTF-8') as html_file:
                parse_post(the_post)
        except NotFound:
            print('User not found with Reddit API.  Most likely deleted.')
        except HTTPError:
            print('Unable to Archive Post: Invalid PostID or Log In Required (see line 157 of script)')
else:
    filedate = arrow.now().timestamp
    basedir = "/rpa" if os.environ.get('DOCKER', '0') == '1' else '.'
    output_file_path = "{basedir}/{post_id}_{timestamp}.html".format(basedir=basedir, post_id=post_id, timestamp=filedate)

    try:
        the_post = r.submission(id=post_id)
        with open(output_file_path, 'w', encoding='UTF-8') as html_file:
            try:
                parse_post(the_post)
            except NotFound:
                print('User not found with Reddit API.  Most likely deleted.')
    except HTTPError:
        print('Unable to Archive Post: Invalid PostID or Log In Required (see line 157 of script)')
