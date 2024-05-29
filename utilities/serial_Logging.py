import serial
import threading
from multiprocessing import Process, Queue


def func_logging(rs232_port, log_file_name, proc_q):
    print("Start thread %s %s " % (rs232_port, log_file_name))
    hard_serial = serial.Serial(rs232_port, 115200, timeout=1)
    if not hard_serial.is_open:
        print("Error opening port %s" % rs232_port)
        return 127
    log_file = open(log_file_name, 'wb')
    if log_file.closed:
        print("Error opening file %s" % log_file_name)
        return 127
    while proc_q.empty():
        serial_data = hard_serial.read()
        if len(serial_data) > 0:
            log_file.write(serial_data)
            log_file.flush()
    log_file.close()
    print("Exit logging thread")


def serial_logging_start(rs232_port, log_file_name):
    global thread_log, proc_q
    proc_q = Queue()
    thread_log = Process(target=func_logging, args=(rs232_port, log_file_name, proc_q,))
    thread_log.daemon = True
    thread_log.start()


def serial_logging_stop():
    proc_q.put("STOP")
    thread_log.join(timeout=5)


