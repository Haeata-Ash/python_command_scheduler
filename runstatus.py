import signal, os, time
from runner import read_file, unexpected_error, PID_FILE_PATH, STATUS_PATH

def status_request(pid):
    """Sends SIGUSR1 signal to runner.py to request status messages"""
    try:
        os.kill(pid, signal.SIGUSR1)

    except (OSError):
        # pid does not exist or runner.py is not running
        message = f"runner.py instance with {pid} not found\n"
        unexpected_error(message)

def get_runner_pid():
    """reads .runner.pid and returns runner.py process ID"""

    lines = read_file(PID_FILE_PATH)

    if lines == []:
        # file is empty, runner is not running / no pid found
        message = f"file {PID_FILE_PATH} is empty"
        unexpected_error(message)

    try:
        pid = int(lines[0])

        if pid < 0:
            #not a valid pid
            raise ValueError

    except ValueError:
        # not a valid pid
        message = f"{pid} is not a valid process ID"
        unexpected_error(message)

    return pid


if __name__ == "__main__":

    # get runners pid
    runner_pid = get_runner_pid()

    # send signal for status
    status_request(runner_pid)

    # read status file then truncate to 0
    time.sleep(5)
    lines = read_file(STATUS_PATH)
    f = open(STATUS_PATH)
    f.close()


    if lines == []:
        # no status messages arrived within 5 seconds
        message = "status timeout"
        unexpected_error(message)

    for ln in lines:
        # print status messages to stdout
        print(ln, end="")
