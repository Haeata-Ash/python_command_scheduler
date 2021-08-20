#!/usr/bin/bash python3

import sys,os,signal,time,datetime,re

# filenames
HOME = os.environ["HOME"]
CONFIG_PATH = f"{HOME}/.runner.conf"
STATUS_PATH = f"{HOME}/.runner.status"
PID_FILE_PATH = f"{HOME}/.runner.pid"




class Command():
    """Command class that holds all relevant information to a command,
    including it's arguments or parameters, path, whether the command should be repeated (every)
    or removed after execution (on), and the its time to execute as a datetime object
    """
    command_queue = []
    ran_error_status_messages = []

    def __init__(self, weekday, time, path, args, origin_line, retain = False):
        self.weekdays = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday"
        ]
        self.weekday = weekday
        self.time = time
        self.path = path
        self.args = args
        self.origin_line = origin_line
        self.retain = retain
        self.dt = self.build_datetime()

    def run_command(self):
        """Runs a program by via fork then exec, and adds ran/error status message to list of
        status messages"""

        # program variables
        path = self.path
        params = self.args

        # message variables
        execution_time = time.ctime()
        msg_params = " ".join(params)

        #try to fork
        try:
            pid = os.fork()
        except (OSError):
            message = f"error {execution_time} {path} {msg_params}"

        # parent process code
        if pid > 0:
            ppid = os.getpid()

            # wait for child process to finish
            ret_value = os.wait()

            #success
            if ret_value[1] == 0:
                message = f"ran {execution_time} {path} {msg_params}"

            #error
            else:
                message = f"error {execution_time} {path} {msg_params}"

        # child process code
        elif pid == 0:

            # try to exec
            try:
                os.execv(path, [path] + params)
            except (OSError):
                sys.exit(1)

        # fork failed without exception
        else:
            message = f"error {execution_time} {path} {msg_params}"

        # set command datetime to next week if it is to be retained
        if self.retain:
            self.dt = self.dt + datetime.timedelta(days=7)

        # append status message
        Command.ran_error_status_messages.append(message)

    def build_datetime(self):
        """ creates a datetime object representing when the command next runs"""

        now = datetime.datetime.now()

        # parse time attribute and form time object
        new_time = datetime.time(int(self.time[0:2]),int(self.time[2:]),0)

        # find the next valid occurrence for a command
        if not self.weekday:
            # no day specified
            if new_time < now.time():
                tmp = now.date() + datetime.timedelta(days=1)
            else:
                tmp = now.date()

        # day specified
        else:
            day_index = self.weekdays.index(self.weekday)
            next_day = day_index - now.weekday()
            if next_day < 0:
                next_day += 7
            elif next_day == 0 and new_time < now.time():
                next_day += 7

            # create date object
            tmp = now.date() + datetime.timedelta(days=next_day)

        # create datetime object
        dt = datetime.datetime.combine(tmp, new_time)

        return dt

    def is_time(self, other_dt):
        """checks if it is time for the command to run"""

        # check date, hour then minute
        if other_dt.date() == self.dt.date():
            if (other_dt.time().hour == self.dt.time().hour):
                if (other_dt.time().minute == self.dt.time().minute):
                    return True

        return False

    def sort_queue():
        """sorts the command queue by datetime attribute such that
        the earliest command is at the front of the queue"""

        Command.command_queue.sort(key=lambda x: x.dt)

    def get_all_status_messages():
        """parse command queue and form status messages for each command, then
        append them to status message list"""

        future_stat_messages = []

        for cmd in Command.command_queue:
            params = " ".join(cmd.args)
            message = f"will run at {cmd.dt.ctime()} {cmd.path} {params}"
            future_stat_messages.append(message)

        return Command.ran_error_status_messages + future_stat_messages

    def build_commands():
        lines = read_file(CONFIG_PATH)
        is_valid, valid_cmds = validate_config(lines)

        commands = []

        # invalid config
        if not is_valid:
            invalid_line = valid_cmds
            message = f"error in configuration: {invalid_line}"
            unexpected_error(message)

        #valid config
        else:
            for cmd in valid_cmds:
                if not cmd["days"]:
                    time_child_commands = Command.get_child_commands(cmd, "times")
                    for ccmd in time_child_commands:
                        time = ccmd["times"]
                        path = ccmd["path"]
                        args = ccmd["params"]
                        origin_line = ccmd["origin_line"]
                        retain = ccmd["every_or_on"]
                        c = Command(None, time, path, args, origin_line, retain)
                        commands.append(c)
                else:
                    day_child_commands = Command.get_child_commands(cmd, "days")
                    for day_cmd in day_child_commands:
                        time_child_commands = Command.get_child_commands(day_cmd, "times")
                        for ccmd in time_child_commands:
                            weekday = ccmd["days"]
                            time = ccmd["times"]
                            path = ccmd["path"]
                            args = ccmd["params"]
                            origin_line = ccmd["origin_line"]
                            retain = ccmd["every_or_on"]
                            c = Command(weekday, time, path, args, origin_line, retain)
                            commands.append(c)

        # check if there are duplicate day/time combinations
        i = 0
        while i < len(commands):
            cmd = commands[i]
            # iterate through each command before the current command
            c = 0
            while (c < i):
                prev_command = commands[c]
                if cmd.is_time(prev_command.dt):
                    # duplicate found
                    message = f"error in configuration: {cmd.origin_line}"
                    unexpected_error(message)

                c += 1
            i += 1

        # add to commands to queue
        Command.command_queue = commands

    def get_child_commands(parent_command, child_key):
        num_child_commands = len(parent_command[child_key])
        child_commands = []
        child_command = {
            "every_or_on": None,
            "days": None,
            "times": None,
            "path": None,
            "params": None
        }

        if num_child_commands > 1:
            for elem in parent_command[child_key]:
                for key in parent_command.keys():
                    if key != child_key:
                        child_command[key] = parent_command[key]
                    else:
                        child_command[child_key] = elem

                child_commands.append(dict(child_command))

        else:
            for key in parent_command.keys():
                if key == child_key:
                    child_command[key] = parent_command[key][0]
                else:
                    child_command[key] = parent_command[key]

            child_commands.append(dict(child_command))

        return child_commands


def sig_handle(sig_num, frame):
    """handles signals"""

    # get "will runn" status messages then write all messages to file
    messages = Command.get_all_status_messages()
    write_to_file(STATUS_PATH, messages)

def validate_config(lines):
    """validates config file line by line, returning false
    and the line number if an invalid command exists"""

    ####TO DO####
    # This is hard to read and maintain, need to break it up into smaller components
    # and incorporated into some parsing logic
    config_re = re.compile("[ \t]*(?P<day_timespec>(?P<every_or_on>every|on)[ \t]+" +
    "(?P<days>(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)" +
    "(,(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)){0,6})[ \t]+)?at[ \t]+" +
    "(?P<times>((2[0-3]|[01][0-9])([0-5][0-9]))((,((2[0-3]|[01][0-9])" +
    "([0-5][0-9]))){0,6}))[ \t]+run[ \t]+((?P<path>(/[^/\s]+)+))(?P<params>(([ \t]+[\S]+))*)")

    valid_cmds = []

    for ln in lines:
        cmd = {"every_or_on": None,
            "days": None,
            "times": None,
            "path": None,
            "params": None,
            "origin_line": None
        }

        valid_cmd = config_re.match(ln)

        # if it is not valid
        if not valid_cmd:
            return False, ln

        #check if the days have repeats since regex will match duplicate days
        if valid_cmd.group("day_timespec"):
            day_list = valid_cmd.group("days").split(",")
            if not (len(day_list) == len(set(day_list))):
                return False, ln

        #check if times are duplicated since regex will match duplicate times
        time_list = valid_cmd.group("times").split(",")
        if not (len(time_list) == len(set(time_list))):
            return False, ln

        # populate command fields
        for key in cmd.keys():

            # set execution time if it exists
            if key == "times":
                times = valid_cmd.group(key).split(",")
                cmd[key] = times

            # set day of execution if it exists
            elif key == "days":

                # no day specified
                if valid_cmd.group(key) == None:
                    cmd[key] = None
                else:
                    cmd[key] = valid_cmd.group(key).split(",")
            
            # set parameters to be passed into command
            elif key == "params":
                cmd[key] = valid_cmd.group("params").lstrip().split(" ")
            
            # set field that specifies if the commmand is repeated or should be
            # removed from schedule after executio
            elif key == "every_or_on":
                if not valid_cmd.group(key):
                    cmd[key] = False
                elif valid_cmd.group(key) == "every":
                    cmd[key] = True
                else:
                    cmd[key] = False
            # line from config file the command originated from to be used for error
            # messages
            elif key == "origin_line":
                cmd[key] = ln
            else:
                cmd[key] = valid_cmd.group(key)

        valid_cmds.append(dict(cmd))

    return True, valid_cmds

def read_file(filename):
    try:
        # check config file is empty
        if os.path.getsize(filename) == 0 and filename == CONFIG_PATH:
            message = "configuration file empty\n"
            unexpected_error(message)

        with open(filename, "r") as f:
            lines = f.readlines()
            return lines
    
    #config file doesn't exists
    except (FileNotFoundError):
        if filename == CONFIG_PATH:
            message = "configuration file not found"
        else:
            message = f"file {filename} could not be found."

        unexpected_error(message)


def write_to_file(filename, lines, append=False):
    if append:
        mode = "a"
    else:
        mode = "w"

    try:
        with open(filename, mode) as f:
            for ln in lines:
                f.write(ln + "\n")
    except (FileNotFoundError):
        #do something
        pass

def unexpected_error(message):
    # print error message to stderr and exit runner.py
    print(message, end="", file=sys.stderr)
    sys.exit(1)

def file_setup():
    """check if the neccessary files exists and if not create them"""

    if not os.path.isfile(PID_FILE_PATH):
        with open(PID_FILE_PATH, "w") as pidf:
            pass

    if not os.path.isfile(STATUS_PATH):
        with open(STATUS_PATH, "a"):
            pass



if __name__ == "__main__":
    #signal handler
    signal.signal(signal.SIGUSR1, sig_handle)

    # setup neccessary files
    file_setup()

    # write runners pid to file
    runner_pid = os.getpid()
    write_to_file(PID_FILE_PATH, [f"{runner_pid}"])

    # read in config, create commands and sort to form queue
    Command.build_commands()
    Command.sort_queue()

    # main loop
    while True:
        now = datetime.datetime.now()
        if len(Command.command_queue) == 0:
            print("nothing left to run")
            sys.exit()
        if Command.command_queue[0].is_time(now):
            command = Command.command_queue.pop(0)
            command.run_command()
            if command.retain:
                Command.command_queue.append(command)
        time.sleep(0.5)
