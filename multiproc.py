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


def process_comment_urls(udbname, ulimit=100000):
    print('---EXTRACTING COMMENT URLS')
    number_of_processes = 4
    totalcompleted = 0
    if ulimit == 0:
        ulimit = None
    total_to_process = Comment.select().where(Comment.number_urls.is_null()).count()
    with tqdm(total=total_to_process) as pbar:
        while totalcompleted < total_to_process:
            with db.atomic():
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
                    with db.atomic():
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


if __name__ == '__main__':
    subreddit = 'LifeProTips'
    dbname = "{}.db".format(subreddit)
    db.init(dbname, timeout=60, pragmas=(
        ('journal_mode', 'wal'),
        ('cache_size', -1024 * 64)))
    db.connect()
    db.create_tables([Url, Comment, CommentLinks])
    limit = 0
    process_comment_urls(dbname, limit)