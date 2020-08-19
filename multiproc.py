import argparse
from apsw import SQLError
from multiprocessing import Process, Queue

from tqdm import tqdm

from pwdb import db, Url, Comment, CommentLinks
from utils import extract_urls


#
# Function run by worker processes
#


def url_worker(urlinput, urloutput):
    for comment_id, body in iter(urlinput.get, 'STOP'):
        url_set = extract_urls(body)
        urloutput.put((comment_id, url_set))


def process_comment_urls(udb, ulimit=100000, number_of_processes=4):
    print('---EXTRACTING COMMENT URLS')
    totalcompleted = 0
    if ulimit == 0:
        ulimit = None
    total_to_process = Comment.select().where(Comment.number_urls.is_null()).count()
    if ulimit is not None and total_to_process > ulimit:
        total_to_process = ulimit
    with tqdm(total=total_to_process) as pbar:
        while totalcompleted < total_to_process:
            with udb.atomic():
                queue_tasks = [(comment.id, comment.body) for comment in Comment.select().where(
                    Comment.number_urls.is_null()).limit(ulimit)]
            # Create queues
            task_queue = Queue()  # ctx.Queue()  #
            done_queue = Queue()  # ctx.Queue()  #

            # Submit tasks
            for task in queue_tasks:
                task_queue.put(task)

            # Start worker processes
            for i in range(number_of_processes):
                Process(target=url_worker, args=(task_queue, done_queue)).start()

            for i in range(len(queue_tasks)):
                comment_id, url_set = done_queue.get()
                try:
                    with udb.atomic():
                        Comment.update(number_urls=len(url_set)).where(Comment.id == comment_id).execute()
                        for url in url_set:
                            url, urlcreated = Url.get_or_create(link=url)
                            try:
                                CommentLinks.insert(comment=comment_id, url=url.id).on_conflict_ignore().execute()
                            except SQLError:
                                print(comment_id, url.id)
                                raise
                except KeyboardInterrupt:
                    quit()

                pbar.update(1)
                totalcompleted += 1

            # Tell child processes to stop
            for i in range(number_of_processes):
                task_queue.put('STOP')
    """
    print('Writing new database file')
    now = arrow.now().timestamp
    basedir = "/rpa" if os.environ.get('DOCKER', '0') == '1' else '.'
    newdbname = "{basedir}/{s}_{t}.db".format(basedir=basedir, s=subred, t=now)
    filecon = Connection(newdbname)
    newmem_uri = 'file:memdb?mode=memory&cache=shared'
    newmemcon = Connection(newmem_uri)
    with filecon.backup("main", newmemcon, "main") as newbackup:
        newbackup.step()
    """


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="""Subreddit Comment Extraction Script""", epilog="""
                       This program has the ability to parse all comments for any urls.""")

    parser.add_argument("subreddit", default='opendirectories', type=str,
                        help="""The subreddit name to process.""")

    parser.add_argument("-l", "--limit", default=0, type=int, help="""Max number of comments to process\n""")

    parser.add_argument("-p", "--processes", default=2, type=int, help="""Number of processes to run concurrently\n""")

    parser.add_argument("-i", "--inputfile", action='store_true',
                        help="""A file containing a list of subreddit names to extract.""")

    # this stores our application parameters so it can get passed around to functions
    args = parser.parse_args()
    if args.subreddit:
        subreddit = args.subreddit
    else:
        subreddit = 'usenet'
        print('No subreddit provided, exiting.')
        quit()
    if args.limit:
        limit = args.limit
    else:
        limit = 0
    if args.processes:
        processes = args.processes
    else:
        processes = 2

    if args.inputfile:
        inputfile = args.subreddit
    else:
        inputfile = None

    # subreddit = 'LifeProTips'
    sublist = list()
    if inputfile is not None:
        with open(inputfile, 'r', encoding='UTF-8') as ipfile:
            for ipline in ipfile:
                sublist.append(ipline.rstrip())
    else:
        sublist.append(subreddit)
    for subreddit in sublist:
        print('############   PROCESSING', subreddit, '    #############')
        basedir = "/rpa" if os.environ.get('DOCKER', '0') == '1' else '.'
        mem_uri = basedir + "{}.db".format(subreddit)
        """
        diskcon = Connection(mem_uri)
        mem_uri = 'file:memdb?mode=memory&cache=shared'
        memcon = Connection(mem_uri)
        with memcon.backup("main", diskcon, "main") as backup:
            backup.step()
        """
        db.init(mem_uri, timeout=60, pragmas=(
            ('journal_mode', 'wal'),
            ('page_size', 4096),
            ('temp_store', 'memory'),
            ('synchronous', 'off'),
        ))
        db.connect()
        db.create_tables([Url, Comment, CommentLinks])
        # limit = 0
        try:
            process_comment_urls(db, limit, processes)
        except KeyboardInterrupt:
            quit()
