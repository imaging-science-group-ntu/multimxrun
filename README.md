# multimxrun
Utility to run several copies of the McXtrace simulation utility in seporate processes

usage: multimxrun.py [-h] [-n N_EVENTS] [-d DIR] [-r] [-o OUTPUT] [-e PREFIX] [-a ADDITIONAL] [-c CSV_INPUT | -t T_PROCESS]
                     [-p N_PROCESS] [-s SLEEP_SEC] [-v]
                     sim_file

McXtrace Simulation Multiprocess Run Utility. This script allows the user to run several copies of McXtrace in separate processes.
There are two modes that can be used: (1) Identical simulation file repeated multiple times to achieve greater statistical
accuracy (2) Simulation parameters determined uniquely for each simulation via a CSV file with one row for each
simulation/process. If number of concurrent processes to run not specified, it automatically gets number of CPU cores and uses
that for n_process value.

positional arguments:

sim_file: simulation file passed to McXtrace

optional arguments:

-h, --help: show this help message and exit

-n N_EVENTS, --n_events N_EVENTS: number of McXtrace events per process (default: 1E8)

-d DIR, --dir DIR: put all data files into one dir with specified name and delete individual simulation directories

-r, --remove: remove all simulation directories

-o OUTPUT, --output OUTPUT: concatenate all data files into one output file with specified name
 
-e PREFIX, --prefix PREFIX: prefix for auto generated simulation name (default: 'sim_data_'
 
-a ADDITIONAL, --additional ADDITIONAL: additional command line arguments passed to simulation
 
-c CSV_INPUT, --csv_input CSV_INPUT: read specified csv file to set up simulation parameters per process
 
-t T_PROCESS, --t_process T_PROCESS: total number of processes run (default: same value as n_process)
 
-p N_PROCESS, --n_process N_PROCESS: number of processes to run concurrently (default: no of CPU cores)
  
-s SLEEP_SEC, --sleep_sec SLEEP_SEC: number of seconds between runs of monitoring loop (default: 1 second)
  
-v, --verbose: verbose output

TODO: check if executable is in different dir then working dir is correct

TODO: instead of assuming instrument file ends in .instr, extract the file type from the string

Author: Imaging Research Group, Nottingham Trent University

License: GPL version 3 or later

Version: 0.1
