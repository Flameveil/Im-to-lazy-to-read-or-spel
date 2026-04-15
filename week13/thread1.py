import threading
import time

def square(num):
    for i in range(10):
        print(f"Square: {num*num*i}")
        time.sleep(3)

def cube(num):
    for i in range(10):
        print(f"Cube: {num*num*num*i}")
        time.sleep(1)

t1 = threading.Thread(target=square, args=(4,))
t2 = threading.Thread(target=cube, args=(4,))

t1.start()
t2.start()
t1.join()
t2.join()

print("Done!")