import threading
import ctypes
import inspect

def async_raise(tid, exctype):
    if not inspect.isclass(exctype):
        raise TypeError("Only types can be raised")
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid),
            ctypes.py_object(exctype))

    if res == 0:
        raise ValueError("invalid tid while attempting to interrupt thread")
    elif res != 1:
        # something terrible happened. feel afraid
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
        raise SystemError("SetAsyncExc failed, cower in fear")

class TriggeredInterrupt(Exception):
    pass

class KillableThread(threading.Thread):
    def _get_my_tid(self):
        if not self.isAlive():
            raise threading.ThreadError("Attempted to fetch tid for an inactive thread")

        if hasattr(self, "_thread_id"):
            return self._thread_id

        for tid, tobj in threading._active.items():
            if tobj is self:
                self._thread_id = tid
                return tid

    def raise_exc(self, exctype):
        async_raise(self._get_my_tid(), exctype)
