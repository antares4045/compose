import time
import threading


def throttle(callback, throttle_time_limit=100):

    
    isThrottled = False
    lastArgs = None
    lock = threading.Lock()

    def deferredCall():
        nonlocal lastArgs
        nonlocal isThrottled
        nonlocal lock
        time.sleep(throttle_time_limit / 100)
        lock.acquire()
        isThrottled = False

        if lastArgs is None:
            lock.release()
            return
        args, params = lastArgs
        lastArgs = None
        lock.release()
        callback(*args, **params)



    def inner(*args, **params):
        nonlocal lastArgs
        nonlocal isThrottled
        nonlocal lock

        lock.acquire()
        if isThrottled:
            lastArgs = (args, params)
            lock.release()
            return
        isThrottled = True
        lock.release()
        callback(*args, **params)
        threading.Thread(target=deferredCall).start()

    return inner 