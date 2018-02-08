from apsw import SQLError
# import psutil
from multiprocessing import Process, Queue, Lock

from tqdm import tqdm

from pwdb import db, Url, Comment, \
    CommentLinks, db_connect, create_tables
from utils import extract_urls


#
# Function run by worker processes
#


def url_worker(urlinput, urloutput):
    for comment_id, body in iter(urlinput.get, 'STOP'):
        # result = calculate(func, args)
        url_set = extract_urls(body)
        urloutput.put((comment_id, url_set))


def process_comment_urls(pdb, udbname, ulimit=100000):
    print('---EXTRACTING COMMENT URLS')
    # ctx = get_context('spawn')
    lock = Lock()  # ctx.Lock()
    # NUMBER_OF_PROCESSES = psutil.cpu_count()
    NUMBER_OF_PROCESSES = 4
    # TASKS1 = [(comment.id, comment.body) for comment in Comment.select().where(Comment.number_urls.is_null()).limit(ulimit)]
    # TASKS2 = [(plus, (i, 8)) for i in range(10)]
    totalcompleted = 0
    lock.acquire()
    pdb = db_connect(pdb, udbname)
    pdb = create_tables(pdb)
    lock.release()
    lock.acquire()
    total_to_process = Comment.select().where(Comment.number_urls.is_null()).count()
    lock.release()
    with tqdm(total=total_to_process) as pbar:
        while totalcompleted < total_to_process:
            lock.acquire()
            with pdb.atomic():
                queue_tasks = [(comment.id, comment.body) for comment in Comment.select().where(
                    Comment.number_urls.is_null()).limit(ulimit)]
            lock.release()
            # Create queues
            task_queue = Queue()  # ctx.Queue()  #
            done_queue = Queue()  # ctx.Queue()  #

            # Submit tasks
            for task in queue_tasks:
                task_queue.put(task)

            # Start worker processes
            for i in range(NUMBER_OF_PROCESSES):
                Process(target=url_worker, args=(task_queue, done_queue)).start()

            # Get and print results
            # print('Unordered results:')
            for i in range(len(queue_tasks)):
                comment_id, url_set = done_queue.get()
                lock.acquire()
                try:
                    with pdb.atomic():
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
                except KeyboardInterrupt:
                    quit()
                finally:
                    lock.release()

                pbar.update(1)
                totalcompleted += 1

            # Tell child processes to stop
            for i in range(NUMBER_OF_PROCESSES):
                task_queue.put('STOP')


if __name__ == '__main__':
    # set_start_method('spawn')
    # freeze_support()
    subreddit = 'gonewild'
    dbname = "{}.db".format(subreddit)
    limit = 100000
    process_comment_urls(db, dbname, limit)