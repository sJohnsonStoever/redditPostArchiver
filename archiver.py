import datetime
import re
import sys
import time

import mistletoe  # replaced snudown
import praw
import yaml
from requests.exceptions import HTTPError

""" 
Customization Configuration

"""
# Default post_id: #
post_id = '15zmjl'
# Path to which to output the file #
output_file_path = './'
# The Path to the stylesheet, relative to where the html file will be stored #
path_to_css = 'css/style.css'

"""
Reddit Post Archiver
By Samuel Johnson Stoever
"""

if len(sys.argv) == 1:
    print('No post ID was provided. Using default post_id.')
elif len(sys.argv) > 2:
    print('Too Many Arguments. Using default post_id.')
else:
    post_id = sys.argv[1]
output_file_path = output_file_path + post_id + '.html'
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
        html_file.write('Posted by <a id="userlink" href="' + post_object.author._path)
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
        html_file.write(' Points. </em><em>(self.<a id="selfLink" href="')
    else:
        html_file.write(' Points. </em><em>(<a id="selfLink" href="')
    html_file.write(post_object.subreddit._path)
    html_file.write('">' + post_object.subreddit.display_name)
    if post_object.is_self:
        html_file.write('</a>)</em><em>')
    else:
        html_file.write('</a> Subreddit)</em><em>')
    html_file.write(' (<a id="postpermalink" href="')
    html_file.write(post_object.permalink)
    html_file.write('">Permalink</a>)</em>\n')
    if post_object.is_self:
        html_file.write('<div class="post">\n')
        nmarkdown = fix_markdown(post_object.selftext)
        html_file.write(mistletoe.markdown(nmarkdown))
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
            html_file.write('<a href="' + reddit_comment.author._path)
            html_file.write('" class="postOP-comment">' + comment_author_name + '</a> <em>')
        else:
            html_file.write('<a href="' + reddit_comment.author._path)
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
    html_file.write('</em></div>\n')
    html_file.write(mistletoe.markdown(fix_markdown(reddit_comment.body)))
    for reply in reddit_comment._replies:
        parse_comment(reply, post_author_name, post_author_exists, False)
    html_file.write('</div>\n')


def fix_markdown(markdown):
    return re.sub('&gt;', '>', str(markdown))


def fix_unicode(text):
    return str(text.encode('utf8'))


credentials = yaml.load(open('./credentials.yml'))

r = praw.Reddit(client_id=credentials['client_id'],
                client_secret=credentials['client_secret'],
                user_agent=credentials['user_agent'])
try:
    the_post = r.submission(id=post_id)
    with open(output_file_path, 'w') as html_file:
        parse_post(the_post)
except HTTPError:
    print('Unable to Archive Post: Invalid PostID or Log In Required (see line 157 of script)')
