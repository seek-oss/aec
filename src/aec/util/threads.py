from concurrent.futures import ThreadPoolExecutor

NUM_WORKERS = 20
executor = ThreadPoolExecutor(NUM_WORKERS)
