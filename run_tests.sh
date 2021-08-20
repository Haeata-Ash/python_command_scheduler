#!/bin/sh
# pass in as an argument the time that the script should wait after running runner.py
# before terminating and moving to the next test
CONFIG_PATH=~/.runner.conf

populate_conf() {
  :> $CONFIG_PATH
  for i in "$@"; do
    printf '%s\n' "$i" >> $CONFIG_PATH
  done
}

run_test() {
  echo "### Start Test ###"
  python3 runner.py &
  sleep $1

  python3 runstatus.py
  echo "### End Test ###"
  kill $! 2> /dev/null
}

# valid config 1 test 1
line1="at 1601 run /usr/bin/echo 2"
line2="at 1602 run /usr/bin/echo 3"
line3="every Thursday,Friday,Saturday at 1603 run /usr/bin/touch testfile1 testfile2"
populate_conf "$line1" "$line2" "$line3"
run_test 5

# valid config 2
line1="on Friday at 2320 run /usr/bin/ls"
line2="on Saturday,Friday,Sunday at 1602 run /usr/bin/echo here"
line3="every Thursday,Friday,Saturday at 1603 run /usr/bin/touch testfile1 testfile2"
populate_conf "$line1" "$line2" "$line3"
run_test 5


# some edge valid config
line1="at 0000 run /usr/bin/ls"
line2="on Saturday,Friday,Sunday at 1602,0000,1601 run /usr/bin/echo here we have lots of args"
line3="every Thursday,Friday,Saturday at 1603,2359 run /usr/bin/touch testfile1 testfile2 testfile3"
populate_conf "$line1" "$line2" "$line3"
run_test 5

# weird but validwhite space

line1="at     0000      run     /usr/bin/ls"
line2="on Saturday,Friday,Sunday at  1602,0000,1601      run /usr/bin/echo           here we have lots of args"
line3="       every Thursday,Friday,Saturday at 1603,2359 run /usr/bin/touch testfile1 testfile2 testfile3"
populate_conf "$line1" "$line2" "$line3"
run_test 5


# lots of valid lines
line1="at 1301 run /usr/bin/echo 2"
line2="at 1302 run /usr/bin/echo 3"
line3="every Thursday,Friday,Saturday at 1303 run /usr/bin/touch testfile1 testfile2"
line4="on Friday at 2320 run /usr/bin/ls"
line5="on Saturday,Friday,Sunday at 1602 run /usr/bin/echo here"
line6="every Thursday,Friday,Saturday at 1603 run /usr/bin/touch testfile1 testfile2"
line7="at 0000 run /usr/bin/ls"
line8="on Saturday,Friday,Sunday at 1601,0002,1607 run /usr/bin/echo here we have lots of args"
line9="every Thursday,Friday,Saturday at 1629,2359 run /usr/bin/touch testfile1 testfile2 testfile3"
populate_conf "$line1" "$line2" "$line3" "$line4" "$line5" "$line6" "$line7" "$line7" "$line9"
run_test 5

# valid config but bad commands
line1="at 1301 run /notacmmand 2"
line2="at 1302 run /usr/bin/grep"
populate_conf "$line1" "$line2"
run_test 5


# empty config, status request on non running runner.py
populate_conf
run_test 5

# invalid config bad times
line1="at 5000 run /usr/bin/ls"
populate_conf "$line1"
run_test 5

line1="at 2079 run /usr/bin/ls"
populate_conf "$line1"
run_test 5

# missing time
line1="at 2079 run /usr/bin/ls"
populate_conf "$line1"
run_test 5

# missing path
line1="at 1302 run 3"
populate_conf "$line1"
run_test 5

#missing key words
line1="Thursday,Friday,Saturday at 1303 run /usr/bin/touch testfile1 testfile2"
line2="2079 run /usr/bin/ls"
line3="at 1302 /usr/bin/grep"
populate_conf "$line1" "$line2" "$line3"
run_test 5

# duplicate days, times and day/time combinations
line1="on Friday at 2320 run /usr/bin/ls"
line2="on Friday,Friday,Sunday at 1602 run /usr/bin/echo here"
line3="every Thursday,Friday,Saturday at 1603 run /usr/bin/touch testfile1 testfile2"
populate_conf "$line1" "$line2" "$line3"
run_test 5

line1="on Friday at 2320,2320 run /usr/bin/ls"
line2="on Saturday,Friday,Sunday at 1602 run /usr/bin/echo here"
line3="every Thursday,Friday,Saturday at 1603 run /usr/bin/touch testfile1 testfile2"
populate_conf "$line1" "$line2" "$line3"
run_test 5

line1="on Friday at 2320 run /usr/bin/ls"
line2="on Saturday,Friday,Sunday at 1602,2320 run /usr/bin/echo here"
line3="every Thursday,Friday,Saturday at 1603 run /usr/bin/touch testfile1 testfile2"
populate_conf "$line1" "$line2" "$line3"
run_test 5
