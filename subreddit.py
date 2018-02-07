#!/usr/bin/env python3
import argparse
import os
import sys
from apsw import SQLError
from multiprocessing import get_context

import arrow
import praw
import requests
import yaml
from peewee import IntegrityError, fn
from prawcore.exceptions import RequestException
from requests.exceptions import SSLError, ChunkedEncodingError, ConnectionError
from simplejson.scanner import JSONDecodeError
from tqdm import tqdm

from pwdb import db, AuthorFlair, Author, Subreddit, Submission, Url, Domain, SubmissionCommentIDs, Comment, \
    SubmissionLinks, CommentLinks
from utils import extract_urls

""" 
Customization Configuration

"""


# Default post_id: #
# subreddit = 'gonewild'


def date_parse(string):
    try:
        arrowdate = arrow.get(string, 'YYYY-MM-DD')
        return arrowdate
    except arrow.Arrow.ParserError:
        msg = "%r does not match the expected formatting: YYYY-MM-DD" % string
        raise argparse.ArgumentTypeError(msg)


class ApplicationConfiguration(object):
    """
    Holds configuration values used in various places
    """

    def __init__(self):
        self.__database_name = 'temp.db3'
        self.__base_directory = ''
        self.__subreddit = 'deepfakes'
        self.__reddit = None
        self.__oldestdate = arrow.get('2005-06-23', 'YYYY-MM').timestamp
        self.__newestdate = arrow.now().timestamp
        self.__rsub = True
        self.__rcom = True
        self.__extract = False
        self.__inputfile = None
        self.__loop = False

    path_to_css = 'css/style.css'

    def get_database_name(self):
        return self.__database_name

    def set_database_name(self, database_name):
        self.__database_name = database_name

    database_name = property(get_database_name, set_database_name)

    def get_base_directory(self):
        return self.__base_directory

    def set_base_directory(self, base_directory):
        self.__base_directory = base_directory

    base_directory = property(get_base_directory, set_base_directory)

    def get_subreddit(self):
        return self.__subreddit

    def set_subreddit(self, subreddit):
        self.__subreddit = subreddit

    subreddit = property(get_subreddit, set_subreddit)

    def get_reddit(self):
        return self.__reddit

    def set_reddit(self, reddit):
        self.__reddit = reddit

    reddit = property(get_reddit, set_reddit)

    def get_oldestdate(self):
        return self.__oldestdate

    def set_oldestdate(self, oldestdate):
        self.__oldestdate = oldestdate

    oldestdate = property(get_oldestdate, set_oldestdate)

    def get_newestdate(self):
        return self.__newestdate

    def set_newestdate(self, newestdate):
        self.__newestdate = newestdate

    newestdate = property(get_newestdate, set_newestdate)

    def get_rsub(self):
        return self.__rsub

    def set_rsub(self, rsub):
        self.__rsub = rsub

    rsub = property(get_rsub, set_rsub)

    def get_rcom(self):
        return self.__rcom

    def set_rcom(self, rcom):
        self.__rcom = rcom

    rcom = property(get_rcom, set_rcom)

    def get_extract(self):
        return self.__extract

    def set_extract(self, extract):
        self.__extract = extract

    extract = property(get_extract, set_extract)

    def get_inputfile(self):
        return self.__inputfile

    def set_inputfile(self, inputfile):
        self.__inputfile = inputfile

    inputfile = property(get_inputfile, set_inputfile)

    def get_loop(self):
        return self.__loop

    def set_loop(self, loop):
        self.__loop = loop

    loop = property(get_loop, set_loop)


parser = argparse.ArgumentParser(
    description="""Subreddit Download Script""", epilog="""
                   This program has the ability to scrape all posts and comments from a subreddit and then parse
                   all comments for any urls.  There is no need to script loops in bash or shell for populating by date.
                    The program will happily grab all items from the beginning of Reddit in 2006 through present.""")

parser.add_argument("subreddit", default='opendirectories', type=str,
                    help="""The subreddit name to process.  Alternatively, you put a filename pointing to a text file 
                    containing a list of subreddits to process but you must set the -i flag!""")

parser.add_argument("-i", "--inputfile", action='store_true',
                    help="""A file containing a list of subreddit names to continuously scrape.  
                    Any names added to the file while the scraper is running will be included in the follow up loop""")

parser.add_argument("-l", "--loop", action='store_true',
                    help="""The program will continuously loop the chosen subreddit.  If a filename containing a list 
                    of subreddits has been provided with the -i flag, the program will continously 
                    read and scrape all the subreddits in that list""")

parser.add_argument("-s", "--rsub", action='store_true',
                    help="""No reddit submission updates, only scrape with pushshift.io\n""")

parser.add_argument("-c", "--rcom", action='store_true',
                    help="""No reddit comment updates, only scrape with pushshift.io\n""")

parser.add_argument("-e", "--extract", action='store_true',
                    help="""Extract URLS from comment text. CPU INTENSIVE\n""")

parser.add_argument("-d", "--directory", help="""Database Path. Defaults to script directory.\n""")

parser.add_argument("-o", "--oldestdate", default=None, type=date_parse, help="""The earliest date for which to scrape Reddit date. 
                                            If this date is excluded the program will start scraping from the 
                                            beginning of Reddit. Format YYYY-MM-DD, i.e. -o 2008-12-25\n""")
parser.add_argument("-n", "--newestdate", default=None, type=date_parse, help="""The most recent date for which to scrape Reddit date. 
                                            If this date is excluded the program will start scraping from this moment, 
                                            back to the start date. Format YYYY-MM-DD, i.e. -n 2017-01-31\n""")

# this stores our application parameters so it can get passed around to functions
appconfig = ApplicationConfiguration()
cred_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.yml')
credentials = yaml.load(open(cred_path))
r = praw.Reddit(client_id=credentials['client_id'],
                client_secret=credentials['client_secret'],
                user_agent=credentials['user_agent'])
appconfig.reddit = r
args = parser.parse_args()
if args.subreddit:
    appconfig.subreddit = args.subreddit

if args.newestdate:
    appconfig.newestdate = args.newestdate

if args.oldestdate:
    appconfig.oldestdate = args.oldestdate

if args.directory:
    appconfig.base_directory = args.directory

if args.rsub:
    appconfig.rsub = False

if args.rcom:
    appconfig.rcom = False

if args.extract:
    appconfig.extract = True

appconfig.database_name = "{}.db".format(appconfig.subreddit)
db.init(appconfig.database_name, timeout=60, pragmas=(
    ('journal_mode', 'wal'),
    ('cache_size', -1024 * 64)))
db.connect()
db.create_tables([AuthorFlair, Author, Url, Domain, Subreddit, Submission, SubmissionCommentIDs, Comment,
                  SubmissionLinks, CommentLinks])


def get_sub_post_id_set(subrd, first_id, postcount):
    sub_post_id_set = set()
    if first_id is not None:
        params = dict(after=first_id, count=postcount)
        postgenerators = subrd.new(params=params)
    else:
        postgenerators = subrd.new()
    for post in postgenerators:
        post_id = "{}\n".format(post.id)
        sub_post_id_set.add(post_id)
        postcount += 1
        if postgenerators.yielded == 100:
            try:
                first_id = postgenerators.params['after']
            except KeyError:
                first_id = None

    return sub_post_id_set, first_id, postcount


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def reddit_submission_update(update_length=604800):
    print('---UPDATING SUBMISSIONS WITH DATA FROM THE REDDIT API')
    needs_update = Submission.select().where(
        (Submission.retrieved_on - Submission.created_utc) < update_length)
    needs_update_list = list()
    for dbsubmission in needs_update:
        fullname = "t3_{}".format(dbsubmission.link_id)
        needs_update_list.append(fullname)
    totalnumber = len(needs_update_list)
    needs_update_list = list(chunks(needs_update_list, 100))
    with tqdm(total=totalnumber) as pbar:
        for nlist in needs_update_list:
            try:
                rd_submissions = list(r.info(nlist))
            except RequestException:
                print("Connection Error to Reddit API. Exiting...")
                quit()
                return
            with db.atomic():
                for rdsub in rd_submissions:
                    updatedtime = arrow.now().timestamp
                    if rdsub.author is None and rdsub.selftext == '[deleted]':
                        Submission.update(score=rdsub.score, retrieved_on=updatedtime, deleted=True).where(
                            Submission.link_id == rdsub.id).execute()
                    elif rdsub.selftext == '[deleted]':
                        Submission.update(score=rdsub.score, retrieved_on=updatedtime, deleted=False).where(
                            Submission.link_id == rdsub.id).execute()
                    elif rdsub.author is None:
                        Submission.update(score=rdsub.score, selftext=rdsub.selftext_html, retrieved_on=updatedtime,
                                          deleted=True).where(Submission.link_id == rdsub.id).execute()
                    else:
                        Submission.update(score=rdsub.score, selftext=rdsub.selftext_html, retrieved_on=updatedtime,
                                          deleted=False).where(Submission.link_id == rdsub.id).execute()
                    pbar.update(1)


def reddit_comment_update(update_length=604800):
    print('---UPDATING COMMENTS WITH DATA FROM THE REDDIT API')
    totalnumber = Comment.select().where(
        (Comment.retrieved_on - Comment.created_utc) < update_length).count()
    needs_update_list = list()
    needs_update = Comment.select().where(
        (Comment.retrieved_on - Comment.created_utc) < update_length)
    print('    ---Building Task List.  This could take a while for large subreddits')

    with tqdm(total=totalnumber) as nbar:
        for dbcomment in needs_update:
            fullname = "t1_{}".format(dbcomment.comment_id)
            needs_update_list.append(fullname)
            nbar.update(1)
    needs_update_list = list(chunks(needs_update_list, 100))
    print('    ---Accessing data from Reddit API and entering into database')
    with tqdm(total=totalnumber) as pbar:
        for nlist in needs_update_list:
            try:
                rd_comments = list(r.info(nlist))
            except RequestException:
                print("Connection Error to Reddit API. Exiting...")
                quit()
                return
            with db.atomic():
                for rdcomment in rd_comments:
                    updatedtime = arrow.now().timestamp
                    if rdcomment.author is None and rdcomment.body == '[deleted]':
                        Comment.update(score=rdcomment.score,
                                       retrieved_on=updatedtime,
                                       deleted=True).where(Comment.comment_id == rdcomment.id).execute()
                        """
                    elif rdcomment.body == '[deleted]':
                        Comment.update(score=rdcomment.score,
                                       retrieved_on=updatedtime,
                                       deleted=False).where(Comment.comment_id == rdcomment.id).execute()
                    elif rdcomment.author is None:
                        Comment.update(score=rdcomment.score,
                                       # body=rdcomment.body_html,
                                       retrieved_on=updatedtime,
                                       deleted=True).where(Comment.comment_id == rdcomment.id).execute()
                        """
                    else:
                        Comment.update(score=rdcomment.score,
                                       # body=rdcomment.body_html,
                                       retrieved_on=updatedtime,
                                       deleted=False).where(Comment.comment_id == rdcomment.id).execute()
                    pbar.update(1)


def get_push_submissions(newestdate, oldestdate):
    print('---PROCESSING PUSHSHIFT.IO SUBMISSIONS')
    subnumber = 1  # just to trigger the while loop
    sub, subcreated = Subreddit.get_or_create(name=appconfig.subreddit)
    sub_id = sub.id
    push_post_id_set = set()
    total_available = "https://api.pushshift.io/reddit/search/submission/?subreddit={subreddit}" \
                      "&after={oldestdate}&before={newestdate}&aggs=subreddit&size=0"
    turl = total_available.format(subreddit=appconfig.subreddit, oldestdate=oldestdate, newestdate=newestdate)
    with requests.get(turl) as tp:
        # newestdate = appconfig.newestdate
        if tp.status_code != 200:
            print("Connection Error for Pushshift API, quitting...")
            quit()
        tpush = tp.json()
    try:
        total_submissions = tpush['aggs']['subreddit'][0]['bg_count']
    except KeyError:
        total_submissions = tpush['aggs']['subreddit'][0]['doc_count']
    except (IndexError, KeyError):
        print("No new submissions to process from pushshift API")
        return push_post_id_set
    linktemplate = "https://api.pushshift.io/reddit/search/submission/?subreddit={subreddit}" \
                   "&after={oldestdate}&before={newestdate}&sort=desc&size=500"
    with tqdm(total=total_submissions) as pbar:
        while subnumber > 0:
            url = linktemplate.format(subreddit=appconfig.subreddit, oldestdate=oldestdate, newestdate=newestdate)
            with requests.get(url) as rp:
                if rp.status_code != 200:
                    print("Connection Error for Pushshift API, quitting...")
                    quit()
                push = rp.json()
            subnumber = len(push['data'])
            # pbar.update(subnumber)
            with db.atomic():
                for item in push['data']:
                    post_id = "{}\n".format(item['id'])
                    item['link_id'] = item.pop('id')
                    push_post_id_set.add(post_id)
                    if item['created_utc'] < newestdate:
                        newestdate = item['created_utc']
                    item['subreddit'] = sub_id
                    if item['author_flair_text'] is not None:
                        author_flair, author_flair_created = AuthorFlair.get_or_create(text=item['author_flair_text'])
                        item['author_flair'] = author_flair.id
                    else:
                        item['author_flair'] = None
                    author, author_created = Author.get_or_create(name=item['author'])
                    item['author'] = author.id
                    try:
                        media, mediacreated = Url.get_or_create(link=item['media']['oembed']['thumbnail_url'])
                        item['media'] = media.id
                    except KeyError:
                        item['media'] = None
                    try:
                        domain, domaincreated = Domain.get_or_create(value=item['domain'])
                        item['domain'] = domain.id
                    except KeyError:
                        item['domain'] = None
                    try:
                        preview = item['preview']['images'][0]['source']['url']
                        preview, previewcreated = Url.get_or_create(link=preview)
                        item['preview'] = preview.id
                    except KeyError:
                        item['preview'] = None
                    except TypeError:
                        print(item['link_id'], item['preview'])
                        item['preview'] = None
                    itemfields = Submission._meta.fields.keys()
                    insertdict = dict()
                    for key in item.keys():
                        if key in itemfields:
                            insertdict[key] = item[key]
                    if 'thumbnail' in insertdict.keys():
                        if not insertdict['thumbnail'].startswith('http'):
                            insertdict['thumbnail'] = None
                        else:
                            try:
                                thumb, thumbcreated = Url.get_or_create(link=insertdict['thumbnail'])
                                insertdict['thumbnail'] = thumb.id
                            except KeyError:
                                insertdict['thumbnail'] = None
                    try:
                        link_id = Submission.insert(insertdict).execute()
                    except IntegrityError:
                        submission = Submission.get(link_id=insertdict['link_id'])
                        link_id = submission.id
                        try:
                            if int(submission.retrieved_on.timestamp()) <= insertdict['retrieved_on']:
                                submission.score = insertdict['score']
                                submission.num_comments = insertdict['num_comments']
                                if author.name == '[deleted]':
                                    submission.deleted = True
                                submission.save()
                            elif author.name == '[deleted]':
                                submission.deleted = True
                                submission.save()
                        except AttributeError:
                            # print("Type Error when querying", submission.link_id)
                            submission.retrieved_on = submission.created_utc
                            submission.save()
                            continue
                        except KeyError:
                            # print("Type Error when querying", submission.link_id)
                            submission.retrieved_on = arrow.now().timestamp
                            submission.score = insertdict['score']
                            submission.save()
                            continue
                        # link_id = submission.id
                    # submission, submission_created = Submission.get_or_create(**insertdict)
                    urllist = item['url'].split()
                    for url in urllist:
                        if url.startswith("http"):
                            if url.endswith('?fb'):
                                url = url.replace('?fb', '')
                            elif url.endswith('?noredirect'):
                                url = url.replace('?noredirect', '')
                            elif url.endswith('_d.jpg?maxwidth=640&amp;shape=thumb&amp;fidelity=medium'):
                                url = url.replace('_d.jpg?maxwidth=640&amp;shape=thumb&amp;fidelity=medium', '')
                            elif url.endswith('?s=sms'):
                                url = url.replace('?s=sms', '')
                            if '//m.imgur.com' in url:
                                url = url.replace('//m.imgur.com', '//imgur.com')
                            if url.startswith('https://thumbs.gfycat.com/'):
                                url = url.replace('https://thumbs.gfycat.com/', 'https://gfycat.com/')
                            if url.endswith('-size_restricted.gif'):
                                url = url.replace('-size_restricted.gif', '')
                            if 'imgur.com' in url and ',' in url:
                                imgurlist = url.split(',')
                                url, urlcreated = Url.get_or_create(link=imgurlist[0])
                                SubmissionLinks.get_or_create(post=link_id, url=url.id)
                                for img in imgurlist[1:]:
                                    img = "http://imgur.com/{img}".format(img=img)
                                    url, urlcreated = Url.get_or_create(link=img)
                                    SubmissionLinks.get_or_create(post=link_id, url=url.id)
                            else:
                                url, urlcreated = Url.get_or_create(link=url)
                                try:
                                    SubmissionLinks.get_or_create(post=link_id, url=url.id)
                                except IndexError:
                                    print(url.id)
            pbar.update(subnumber)
            """
            print("Received", subnumber, "posts from", redditsub, " -  Total posts received so far:",
                  totalsubnumber, "with", len(push_post_id_set), "in pushshift.io set. Latest Timestamp:", enddate)
            """
    return push_post_id_set


# https://www.reddit.com/comments/30a7ap/_/cprn5us/.json


def get_push_comments(newestdate, oldestdate):
    print('---PROCESSING PUSHSHIFT.IO COMMENTS')
    subnumber = 1
    sub, subcreated = Subreddit.get_or_create(name=appconfig.subreddit)
    sub_id = sub.id
    totalsubnumber = 0
    push_comment_id_set = set()
    total_available = "https://api.pushshift.io/reddit/search/comment/?subreddit={subreddit}" \
                      "&after={oldestdate}&before={newestdate}&aggs=subreddit&size=0"
    turl = total_available.format(subreddit=appconfig.subreddit, oldestdate=oldestdate, newestdate=newestdate)
    # newestdate = appconfig.newestdate
    with requests.get(turl) as tp:
        if tp.status_code != 200:
            print("Connection Error for Pushshift API, quitting...")
            quit()
        tpush = tp.json()
    try:
        total_submissions = tpush['aggs']['subreddit'][0]['doc_count']
    except (IndexError, KeyError):
        print("No new submissions to process from pushshift API")
        return push_comment_id_set
    linktemplate = "https://api.pushshift.io/reddit/search/comment/?subreddit={subreddit}" \
                   "&after={oldestdate}&before={newestdate}&sort=desc&size=500"
    with tqdm(total=total_submissions) as pbar:
        while subnumber > 0:
            url = linktemplate.format(subreddit=appconfig.subreddit, oldestdate=oldestdate, newestdate=newestdate)
            with requests.get(url) as rp:
                try:
                    push = rp.json()
                except JSONDecodeError:
                    print("JSON DECODE ERROR on Pushshift API Comments", url)
                    return push_comment_id_set
            subnumber = len(push['data'])
            totalsubnumber += subnumber
            commentlinktemplate = 'https://www.reddit.com/comments/{comment_id}/_/{comment_id}/.json\n'
            with db.atomic():
                for item in push['data']:
                    item['comment_id'] = item.pop('id')
                    item['comment_id'] = item['comment_id'].replace('t3_', '')
                    commentlink = commentlinktemplate.format(link_id=item['comment_id'], comment_id=item['comment_id'])
                    push_comment_id_set.add(commentlink)

                    if item['created_utc'] < newestdate:
                        newestdate = item['created_utc']
                    item['subreddit'] = sub_id
                    if 'author_flair_text' in item.keys() and item['author_flair_text'] is not None:
                        author_flair, author_flaircreated = AuthorFlair.get_or_create(text=item['author_flair_text'])
                        item['author_flair'] = author_flair.id
                    else:
                        item['author_flair'] = None
                    author, author_created = Author.get_or_create(name=item['author'])
                    item['author'] = author.id
                    itemfields = Comment._meta.fields.keys()
                    insertdict = dict()
                    for key in item.keys():
                        if key in itemfields:
                            insertdict[key] = item[key]
                    Comment.insert(insertdict).on_conflict_ignore().execute()
            pbar.update(subnumber)
            """
            print("Received", subnumber, "comment from", redditsub, " -  Total comments received so far:",
                  totalsubnumber, "with", len(push_comment_id_set), "in pushshift.io set. Latest Timestamp:", enddate)
            """

    return push_comment_id_set


def url_worker(input_queue, output_queue, lock):

    for comment_id, body in iter(input_queue.get, 'STOP'):
        # result = calculate(func, args)
        url_set = extract_urls(body)
        lock.acquire()
        with db.atomic():
            try:
                Comment.set_by_id(comment_id, dict(number_urls=len(url_set)))
                for url in url_set:
                    try:
                        url_id = Url.insert(link=url).execute()
                    except IntegrityError:
                        url = Url.get(link=url)
                        url_id = url.id
                    # url, urlcreated = Url.get_or_create(link=url)
                    try:
                        CommentLinks.insert(comment=comment_id, url=url_id).on_conflict_ignore().execute()
                    except SQLError:
                        print(comment_id, url_id)
                        raise
            finally:
                lock.release()
            output_queue.put(1)


def process_comment_urls(limit=100000):
    print('---EXTRACTING COMMENT URLS')

    is_windows = hasattr(sys, 'getwindowsversion')
    # print("is Windows?", is_windows)
    ctx = get_context('forkserver')
    number_of_processes = 4
    totalcompleted = 0
    lock = ctx.Lock()
    db.pragma('journal_mode', 'wal')
    db.pragma('cache_size', -1024 * 64)

    total_to_process = Comment.select().where(Comment.number_urls.is_null()).count()

    with tqdm(total=total_to_process) as pbar:
        while totalcompleted < total_to_process:
            queue_tasks = [(comment.id, comment.body) for comment in Comment.select().where(
                Comment.number_urls.is_null()).limit(limit)]
            # Create queues
            task_queue = ctx.Queue()
            done_queue = ctx.Queue()

            # Submit tasks
            for task in queue_tasks:
                task_queue.put(task)

            # Start worker processes
            for i in range(number_of_processes):
                ctx.Process(target=url_worker, args=(task_queue, done_queue, lock)).start()

            # Update progress bar
            for i in range(len(queue_tasks)):
                updateint = done_queue.get()
                pbar.update(updateint)
                totalcompleted += updateint

            # Tell child processes to stop
            for i in range(number_of_processes):
                task_queue.put('STOP')


def process_submissions():
    # Get newest submissions with two week overlap
    try:
        newest_utc = int(Submission.select(fn.MAX(Submission.created_utc)).scalar().timestamp())
    except (TypeError, AttributeError):
        newest_utc = None
    if newest_utc is not None:
        oldestdate = newest_utc  # - 1209600  # two weeks overlap, in seconds
    else:
        oldestdate = appconfig.oldestdate

    try:
        post_id_set = get_push_submissions(appconfig.newestdate, oldestdate)
    except (ConnectionError, SSLError, ChunkedEncodingError):
        post_id_set = None
        print("Connection Error for Pushshift API.  Quitting...")
        quit()

    # Get oldest submissions in case progress was interrupted, with four week overlap
    try:
        oldest_utc = int(Submission.select(fn.MIN(Submission.created_utc)).scalar().timestamp())
    except (TypeError, AttributeError):
        oldest_utc = None
    if oldest_utc is not None:
        newestdate = oldest_utc  # + 2400000  # four week overlap, in seconds
    else:
        newestdate = appconfig.newestdate

    try:
        old_post_id_set = get_push_submissions(newestdate, appconfig.oldestdate)
    except (ConnectionError, SSLError, ChunkedEncodingError):
        old_post_id_set = None
        print("Connection Error for Pushshift API.  Quitting...")
        quit()

    post_id_set |= old_post_id_set
    filedate = arrow.now().timestamp
    output_file_path = "{subreddit}_{timestamp}.csv".format(subreddit=appconfig.subreddit, timestamp=filedate)

    # with open(output_file_path, 'w', encoding='UTF-8') as post_file:
    #     post_file.writelines(post_id_set)

    print("Total posts submitted to", appconfig.subreddit, "in set:", len(post_id_set))
    deleted = Author.get_or_none(name='[deleted]')
    if deleted is not None:
        supdatet = Submission.update(deleted=True).where(
            (Submission.author == deleted.id) & (Submission.deleted.is_null() or Submission.deleted == 0)).execute()
        print('Updated deleted field in submissions.  Set deleted = True for', supdatet, 'records.')
        supdatef = Submission.update(deleted=False).where(
            (Submission.author != deleted.id) & (Submission.deleted.is_null())).execute()
        print('Updated deleted field in submissions.  Set deleted = False for', supdatef, 'records.')


def process_comments():
    # Get newest comments with two week overlap
    try:
        newest_utc = int(Comment.select(fn.MAX(Comment.created_utc)).scalar().timestamp())
    except (TypeError, AttributeError):
        newest_utc = None
    if newest_utc is not None:
        oldestdate = newest_utc  # - 1209600  # two weeks overlap, in seconds
    else:
        oldestdate = appconfig.oldestdate

    try:
        comment_id_set = get_push_comments(appconfig.newestdate, oldestdate)
    except (ConnectionError, SSLError, ChunkedEncodingError):
        comment_id_set = None
        print("Connection Error for Pushshift API.  Quitting...")
        quit()

    # Get oldest comments in case progress was interrupted, with two week overlap
    try:
        oldest_utc = int(Comment.select(fn.MIN(Comment.created_utc)).scalar().timestamp())
    except (TypeError, AttributeError):
        oldest_utc = None
    if oldest_utc is not None:
        newestdate = oldest_utc  # + 1209600  # two weeks overlap, in seconds
    else:
        newestdate = appconfig.newestdate

    try:
        old_comment_id_set = get_push_comments(newestdate, appconfig.oldestdate)
    except (ConnectionError, SSLError, ChunkedEncodingError):
        old_comment_id_set = None
        print("Connection Error for Pushshift API.  Quitting...")
        quit()
    comment_id_set |= old_comment_id_set
    filedate = arrow.now().timestamp
    coutput_file_path = "{subreddit}_comments_{timestamp}.txt".format(subreddit=appconfig.subreddit, timestamp=filedate)

    # with open(coutput_file_path, 'w', encoding='UTF-8') as comment_file:
    #     comment_file.writelines(comment_id_set)
    print("Total comments submitted to", appconfig.subreddit, "in set:", len(comment_id_set))
    deleted = Author.get_or_none(name='[deleted]')
    if deleted is not None:
        cupdatet = Comment.update(deleted=True).where(
            (Comment.author == deleted.id) & (Comment.deleted.is_null() or Comment.deleted == 0)).execute()
        print('Updated deleted field in comments.  Set deleted = True for', cupdatet, 'records.')
        cupdatef = Comment.update(deleted=False).where(
            (Comment.author != deleted.id) & (Comment.deleted.is_null())).execute()
        print('Updated deleted field in comments.  Set deleted = False for', cupdatef, 'records.')


def main():
    process_submissions()
    if appconfig.rsub:
        reddit_submission_update()
    process_comments()
    if appconfig.rcom:
        reddit_comment_update()
    if appconfig.extract:
        process_comment_urls()


if __name__ == '__main__':
    # freeze_support()
    main()
