from concurrent.futures import ThreadPoolExecutor

# used to execute IO in parallel

NUM_WORKERS = 2
executor = ThreadPoolExecutor(NUM_WORKERS)
