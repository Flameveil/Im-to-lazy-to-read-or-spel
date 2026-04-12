from concurrent.futures import ThreadPoolExecutor
import time

def worker(task):
    for i in range(10):
        print(f"Task {task} running count: {i}")
        time.sleep(1)

# Create a thread pool with 2 workers
with ThreadPoolExecutor(max_workers=2) as executor:
    # Submit two tasks to run in parallel
    executor.submit(worker, 1)
    executor.submit(worker, 2)