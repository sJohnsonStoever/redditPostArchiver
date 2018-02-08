from apsw import SQLError
# import psutil
from multiprocessing import Process, Queue, Lock, freeze_support

from tqdm import tqdm

from pwdb import db, AuthorFlair, Author, Subreddit, Submission, Url, Domain, SubmissionCommentIDs, Comment, \
    SubmissionLinks, CommentLinks
from utils import extract_urls


#
# Function run by worker processes
#


def url_worker(udbname, input, output, lock):
    udb = db
    udb.init(udbname, timeout=60, pragmas=(
        ('journal_mode', 'wal'),
        ('cache_size', -1024 * 64)))
    udb.connect()
    udb.create_tables(
        [AuthorFlair, Author, Url, Domain, Subreddit, Submission, SubmissionCommentIDs, Comment, SubmissionLinks,
         CommentLinks])
    for comment_id, body in iter(input.get, 'STOP'):
        # result = calculate(func, args)
        url_set = extract_urls(body)
        lock.acquire()
        try:
            with udb.atomic():
                # comment = Comment.get(id=comment_id)
                Comment.update(number_urls=len(url_set)).where(Comment.id == comment_id).execute()
                # comment.number_urls = len(url_set)
                # comment.save()
                for url in url_set:
                    url, urlcreated = Url.get_or_create(link=url)
                    try:
                        # CommentLinks.get_or_create(comment=comment_id, url=url[0].id)
                        CommentLinks.insert(comment=comment_id, url=url.id).on_conflict_ignore().execute()
                    except SQLError:
                        print(comment_id, url.id)
                        raise
        finally:
            lock.release()
        output.put(1)


def process_comment_urls(udbname, ulimit=100000):
    print('---EXTRACTING COMMENT URLS')
    # NUMBER_OF_PROCESSES = psutil.cpu_count()
    NUMBER_OF_PROCESSES = 8
    # TASKS1 = [(comment.id, comment.body) for comment in Comment.select().where(Comment.number_urls.is_null()).limit(ulimit)]
    # TASKS2 = [(plus, (i, 8)) for i in range(10)]
    totalcompleted = 0
    lock = Lock()
    lock.acquire()
    total_to_process = Comment.select().where(Comment.number_urls.is_null()).count()
    lock.release()
    with tqdm(total=total_to_process) as pbar:
        while totalcompleted < total_to_process:
            lock.acquire()
            queue_tasks = [(comment.id, comment.body) for comment in Comment.select().where(
                Comment.number_urls.is_null()).limit(ulimit)]
            lock.release()
            # Create queues
            task_queue = Queue()
            done_queue = Queue()

            # Submit tasks
            for task in queue_tasks:
                task_queue.put(task)

            # Start worker processes
            for i in range(NUMBER_OF_PROCESSES):
                Process(target=url_worker, args=(udbname, task_queue, done_queue, lock)).start()

            # Get and print results
            # print('Unordered results:')
            for i in range(len(queue_tasks)):
                updateint = done_queue.get()
                pbar.update(updateint)
                totalcompleted += updateint

            # Tell child processes to stop
            for i in range(NUMBER_OF_PROCESSES):
                task_queue.put('STOP')


if __name__ == '__main__':
    freeze_support()
    subreddit = 'opendirectories'
    dbname = "{}.db".format(subreddit)
    db.init(dbname, timeout=60, pragmas=(
        ('journal_mode', 'wal'),
        ('cache_size', -1024 * 64)))
    db.connect()
    db.create_tables(
        [AuthorFlair, Author, Url, Domain, Subreddit, Submission, SubmissionCommentIDs, Comment, SubmissionLinks,
         CommentLinks])
    limit = 100000
    process_comment_urls(dbname, limit)