## What is it ?
A simple python system to run programs at scheduled times, inspired by the unix cron system

The system consists of two programs:
- runner.py which reads a configuration file which specifies the program to run, program parameters and when it should be run. runner.py will run as a background process
- runstatus.py which retrieves the current status from runner.py and dumps it to standard output

The system uses three files: 
- `$HOME/.runner.conf` for configuration
- `$HOME/.runner.pid` for interprocess communication. runner.py records its pid in this file, which runstatus then reads. runstatus then uses signals to conduct interprocess communication in order to get runner.py's status
- `$HOME/.runner.status` where runner.py dumps the current status when signaled by the runstatus.py program. This file is then read by runstatus.py

Commands are executed by forking then execing the runner.py process into whatever command is specified. Basic error handling for bad commands is implemented

## Configuration
An example configuration file has been provided. The program looks for the configuration file at `$HOME/.runner.conf`

