from concurrent.futures import ThreadPoolExecutor

NUM_WORKERS = 2
executor = ThreadPoolExecutor(NUM_WORKERS)
