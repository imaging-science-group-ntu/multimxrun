#!/usr/bin/env python
"""McXtrace Simulation Multiprocess Run Utility.

This script allows the user to run several copies of McXtrace in separate
processes. There are two modes that can be used:
(1) Identical simulation file repeated multiple times to achieve greater
statistical accuracy
(2) Simulation parameters determined uniquely for each simulation via a
CSV file with one row for each simulation/process.
If number of concurrent processes to run not specified, it automatically
gets number of CPU cores and uses that for n_process value.

TODO: check if executable is in different dir then working dir is correct
TODO: instead of assuming instrument file ends in .instr, extract the file type from the string

Author: Imaging Research Group, Nottingham Trent University
License: GPL version 3 or later
Version: 0.1
"""

# mcxtrace Single_Hexagonal_Channel.instr
#
# gcc -o ./Single_Hexagonal_Channel.out ./Single_Hexagonal_Channel.c -lm -g -O2 -lm -std=c99
# or
# gcc -o ./Single_Hexagonal_Channel.out ./Single_Hexagonal_Channel.c -lm -UUSE_MPI -g -O2 -lm -std=c99
#
# ./Single_Hexagonal_Channel.out -n 1000 -d data1
#
# mcxtrace -h
# McXtrace version 1.6 (Aug. 13, 2021)
# Compiler of the McXtrace ray-trace simulation package
# Usage:
#   McXtrace [-o file] [-I dir1 ...] [-t] [-p] [-v] [--no-main] [--no-runtime] [--verbose] file
#       -o FILE --output-file=FILE Place C output in file FILE.
#       -I DIR  --search-dir=DIR   Append DIR to the component search list. 
#       -t      --trace            Enable 'trace' mode for instrument display.
#       -v      --version          Prints McXtrace version.
#       --no-main                  Do not create main(), for external embedding.
#       --no-runtime               Do not embed run-time libraries.
#       --verbose                  Display compilation process steps.
#   The file will be processed and translated into a C code program.
#   If run-time libraries are not embedded, you will have to pre-compile
#     them (.c -> .o) before assembling the program.
#   The default component search list is usually defined by the environment
#     variable 'McXtrace 1.6 - Aug. 13, 2021' (default is /usr/share/mcxtrace/1.6) 
#   Use 'mxrun' to both run McXtrace and the C compiler.
#   Use 'mxgui' to run the McXtrace GUI.
# SEE ALSO: mxrun, mxplot, mxdisplay, mxgui, mxformat, mxdoc
# DOC:      Please visit www.mcxtrace.org
#
# ./Single_Hexagonal_Channel.out -h
# Single_Hexagonal_Channel (Single_Hexagonal_Channel.instr) instrument simulation, generated with McXtrace 1.6 - Aug. 13, 2021 (Aug. 13, 2021)
# Usage: ./Single_Hexagonal_Channel.out [options] [parm=value ...]
# Options are:
#   -s SEED   --seed=SEED      Set random seed (must be != 0)
#   -n COUNT  --ncount=COUNT   Set number of xrays to simulate.
#   -d DIR    --dir=DIR        Put all data files in directory DIR.
#   -t        --trace          Enable trace of xrays through instrument.
#   -g        --gravitation    Enable gravitation for all trajectories.
#   --no-output-files          Do not write any data files.
#   -h        --help           Show this help message.
#   -i        --info           Detailed instrument information.
#   --format=FORMAT            Output data files using FORMAT=MCXTRACE
#
# Instrument parameters are:
#   filename        (string) [default='sample.xbd']
#   source_x        (double) [default='0.0']
#   source_y        (double) [default='0.0']
# Known signals are: USR1 (status) USR2 (save) TERM (save and exit)


# commenting and documenting Python code: https://realpython.com/documenting-python-code/

import sys
import subprocess as sp
import shlex
import re
import argparse
import csv
from functools import reduce
from time import time, sleep
from enum import Enum, auto
import os
from datetime import timedelta
from math import log10, ceil
from shutil import copyfileobj, copy, rmtree

class ConsolePrint():
    """
    A class used to take care of print and status on the command line

    A problem occurs when interspersing status updates that need to be
    followed by messages to the user. The status line is overwritten
    by the new message. This class keeps track of previous writes so
    that newline happens depending if it is a print or status. If status
    then a flush of the buffer is also forced.

    Attributes
    ----------
    _nl : bool
        track newline state of previous print (global class attribute!)

    Methods
    -------
    newline()
        Prints newline if previous was not newline
    print(*args_)
        Prints variable number of arguments on the console, each one on a new line
    status(*args_)
        Prints new status line on console and if previous was a status line then overwrite it
    """
    _nl = True
    
    def newline(self):
        if not self._nl:
            self._nl = True
            print()

    def print(self, *args_):
        self.newline()
        print(*args_)

    def status(self, *args_):
        if self._nl: self._nl=False
        print(*args_, end='\r', flush=True)

class State(Enum):
    """
    Enumeration of the possible process states 

    Attributes
    ----------
    WAITING
    RUNNING
    FINISH
    ERROR

    Methods
    -------
    """
    WAITING = auto()
    RUNNING = auto()
    FINISH = auto()
    ERROR = auto()

class ProcManager:
#class Process():
    """
    A base class used to manage and store attributes specific to each process

    At the class level (due to console write only one can run) it is used
    to manage the collection of processes but at the instance level it
    starts and report back the status of the actual popen subprocesses.
    Tested under Linux and includes code to prevent blocking read. Both
    stdout and stderr are captured and parsed for status updates.
    Should be then given specific code to run the actual commands,
    interpret the output, summarise the status and clean up after all the
    processes have run.


    Attributes
    ----------
    console : ConsolePrint
        console instance for printing messages and status on command line
    n_process : int
        number of processes to concurrently run
    procs : list
        list of Process classes
    _proc : gen
        create generator for iterating through process list
    sleep_sec : float
        minimise effect of monitoring process states by sleeping between polling
    verbose : bool
        print out verbose messages e.g. command start and output 

    process : Popen
        actual subprocess in which simulation runs
    status : State
        status of simulation (see State class)
    time : int
        start time

    Methods
    -------
    @classmethod  
    _next_proc(count)
        utility function to step through list of next waiting processes and call invoke_process()
    @classmethod
    gen_init_processes()
        start the initial batch of processes
    @classmethod
    monitor_output_loop()
        go through running process list, check their status and call print_output_summary(), if too few processes running start more form the queue
    invoke_process()
        use gen_command() to run the command line string as a separate process, store the process handle for future use
    check_status_and_process_output()
        checks if processes has finished and update it's status
    @classmethod
    setup_proc(args)
        run all setup code for command line (should be overwritten in child class)
    @classmethod
    print_output_summary()
        called every time the check status loop runs to print and summarise status of processes (should be overwritten in child class)
    @classmethod
    check_and_cleanup()
        called to do any tasks after processes have run (should be overwritten in child class)

    # per proc level stuff
    __init__()
        use command line arguments to set up simulation (should be overwritten in child class)
    gen_command()
        return full command line string from process attributes (should be overwritten in child class)
    process_output(output)
        process any output from the process (should be overwritten in child class)
    """
    # class level proc manager level stuff https://realpython.com/instance-class-and-static-methods-demystified/

    console = ConsolePrint()
    procs = []
    _proc = (_ for _ in procs) # create generator for iterating through waiting process list, keeps track of which process to run next
    sleep_sec = 1.0 # default of 1 second hard coded in if no other value given
    verbose = False

    @classmethod  
    def _next_proc(self, count):
        try:
            if next(self._proc).invoke_process(): count += 1
        except StopIteration:
            return (False,count)
        else:
            return (True,count)

    @classmethod
    def gen_init_processes(self):
        count = 0
        self.console.print(f"Start initial batch of {str(self.n_process)} processes ...") 
        while count<self.n_process:
            (procs_remaining,count) = self._next_proc(count)
            if not procs_remaining: break

    @classmethod
    def monitor_output_loop(cls):
        p_remain = True;
        cls.console.print('Average of the estimated run time from McXtrace (running) and actual finish time (finished) are in the form (hours:minutes:seconds)\n')
        # stay in loop while either there are processes waiting to run or processes still running
        while (p_remain):
            sleep(cls.sleep_sec)
            p_remain = False
            count = 0 # count processes actually running
            for proc in cls.procs:
                proc.check_status_and_process_output()
                s = proc.status
                if State.WAITING==s or State.RUNNING==s: p_remain = True
                if State.RUNNING==s: count += 1
            while count<cls.n_process:
                (procs_remaining,count) = cls._next_proc(count)
                if not procs_remaining: break
            cls.print_output_summary()
        # if last line was status then newline so subsequent print statements do not overwrite previous status line
        cls.console.newline()

    def invoke_process(self):
        """runs subprocess with Popen/poll so that live stdout is shown"""
        try:
            command = shlex.split(self.gen_command())
            if self.verbose: self.console.print(' '.join(command)) # print out the command line to run
            # pipe stdout and stderr to same destination
            process = sp.Popen(command, stdout=sp.PIPE, stderr=sp.STDOUT)
            # https://stackoverflow.com/questions/375427/a-non-blocking-read-on-a-subprocess-pipe-in-python
            os.set_blocking(process.stdout.fileno(), False) # works on unix like os e.g. linux
        except:
            self.console.print(f"ERROR {sys.exc_info()[1]} while running {self.gen_command()}")
            self.process = None
            self.status = State.ERROR
        else:
            self.process = process
            self.status = State.RUNNING
            self.time = time()
        return self.process

    def check_status_and_process_output(self):
        if self.status==State.RUNNING:
            if not None==self.process.poll():
                self.status=State.FINISH
                self.time = time() - self.time
            output = self.process.stdout.readline()
            while output:
                if self.verbose: self.console.print(output.decode()) # print out the command output
                self.process_output(output.decode())
                output = self.process.stdout.readline()

    # these should be overwritten in child class

    @classmethod
    def setup_proc(cls, args): # note use of following '_' to avoid keyword confusion
        # https://www.geeksforgeeks.org/python-os-cpu_count-method/
        cls.n_process = args.n_process if args.n_process else os.cpu_count()
        if cls.n_process<1: sys.exit("error: n_process<1")
        if args.sleep_sec: cls.sleep_sec = args.sleep_sec 
        if args.verbose: cls.verbose = args.verbose 

    @classmethod
    def print_output_summary(cls):
        pass

    @classmethod
    def check_and_cleanup(cls):
        pass

    # per proc level stuff

    def __init__(self):
        self.process = None
        self.status = State.WAITING
        self.time = 0

    def gen_command(self):
        return None

    def process_output(self, output):
        pass

# define arguments, alter according to Program requirements below
# https://docs.python.org/3/library/argparse.html
# https://fabianlee.org/2019/09/14/python-parsing-command-line-arguments-with-argparse/
ap = argparse.ArgumentParser(description=__doc__)

# mandatory args (particular use case specific)
ap.add_argument('sim_file', help="simulation file passed to McXtrace")
# optional args start with hyphen (particular use case specific)
ap.add_argument('-n', '--n_events', default=100000000, type=int, help="number of McXtrace events per process (default: 1E8)")
ap.add_argument('-d', '--dir', help="put all data files into one dir with specified name and delete individual simulation directories")
ap.add_argument('-r', '--remove', action='store_true', help="remove all simulation directories")
ap.add_argument('-o', '--output', help="concatenate all data files into one output file with specified name")
ap.add_argument('-e', '--prefix', default= "sim_data_", help="prefix for auto generated simulation name (default: 'sim_data_'")
ap.add_argument('-a', '--additional', help="additional command line arguments passed to simulation")
group = ap.add_mutually_exclusive_group()
group.add_argument('-c', '--csv_input', help="read specified csv file to set up simulation parameters per process")
group.add_argument('-t', '--t_process', type=int, help="total number of processes run (default: same value as n_process)")

# command line arguments not exclusive to the particular use case
ap.add_argument('-p', '--n_process', type=int, help="number of processes to run concurrently (default: no of CPU cores)")
ap.add_argument('-s', '--sleep_sec', default=1, type=float, help="number of seconds between runs of monitoring loop (default: 1 second)")
ap.add_argument('-v', '--verbose', action='store_true', help="verbose output")

class Program(ProcManager):
    """"""
    """
    A class that encapsulates particulars of the Program in be run in parallel processes, inherits from ProcManager class

    Used in conjunction with and managed by ProcManager class to run the actual McXtrace commands,
    it remove residual directories and files before recompiling the instrument file. Each process
    is then run with out the need to recompile.

    Attributes
    ----------
    n_events : int
        number of events in McXtrace simulation
    params : str
        extra parameters passed to simulation
    sim_file : str
        simulation instrument file as specified on command line
    filename : str
        specified file name passed to simulation instrument file for simulation data
    dir_ : str
        directory for process simulation data
    running_eta : float
        estimated run time for simulation from command output
    running_perc : int
        percentage of simulation completed (check state as well)
    t_process : int
        total number of processes to run
    csv : str
        CSV file specified
    n_process_digit : int
        number of digits required for n_process command line print
    t_process_digit : int
        number of digits required for t_process command line print
    output_file : str
        specified output file for concatenation
    final_dir : str
        specified directory for all simulation data files
    remove : bool
        remove simulation directories

    Methods
    -------
    @classmethod
    setup_proc(args)
        run all the code needed to process the command line arguments and setup ready to start processes
    @classmethod
    remove_dir(state)
        remove all simulation output directories where the process state is as specified
    @classmethod
    compile()
        run mcxtrace and then gcc to create the .out executable
    @classmethod
    print_output_summary()
        utility function to find and print the state of all the processes currently waiting, running and finished
    @classmethod
    check_and_cleanup()
        if requested concatenate data files into one single file, create new dir with all the data files and finally if needed remove the simulation directories
    __init__(params, filename, dir_)
        set up instance of process with process specific command line parameters, filename and simulation directory
    gen_command()
        generate command form stored per process specific invocation details
    process_output(output)
        specific code that uses regular expressions to process the command line output and update process status
    """

    @classmethod
    def setup_proc(cls, args):
        ProcManager.setup_proc(args)
        cls.sim_file = args.sim_file
        cls.sim_file_c = cls.sim_file.replace(".instr",".c")
        cls.sim_file_out = cls.sim_file.replace(".instr",".out")
        cls.remove = args.remove
        cls.csv = None
        if args.csv_input:
            cls.csv = args.csv_input
            if args.t_process:
                sys.exit("error: cannot specify CSV file and t_process at same time")
            else:
                cls.t_process = 0
            with open(cls.csv) as csvfile:
                reader = csv.DictReader(csvfile)
                filename_list = []
                for row in reader:
                    params = ' '
                    filename = None
                    for elem in row.items():
                        if elem[0]=='filename':
                            filename = elem[1]
                            if filename in filename_list:
                                sys.exit("error: you must specify unique filenames for each row in the CSV file")
                            else:
                                filename_list.append(filename)
                        else:
                            params += f"{str(elem[0])}={str(elem[1])} "
                    if not filename: sys.exit("error: you must provide a 'filename' header in the CSV file")
                    cls.procs.append(Program(params, filename, filename.replace('.','_')))
                    cls.t_process += 1 # count nuber of items in file for total number of processes
        else:
            cls.t_process = args.t_process if args.t_process else cls.n_process
            for i in range(cls.t_process):
                filename = 'sim_data_' + str(i+1) + '.dat'
                cls.procs.append(Program('', filename, filename.replace('.','_')))
        if cls.t_process<cls.n_process:
            cls.n_process = cls.t_process
            cls.console.print("Changed n_process = t_process as t_process < n_process OR rows in CSV file < n_process")
        cls.n_process_digit = ceil(log10(cls.n_process)) # minimise length of status line by only using number of digits actually needed
        cls.t_process_digit = ceil(log10(cls.t_process))
        cls.output_file = args.output if args.output else None 
        cls.final_dir = args.dir if args.dir else None
        cls.n_events = args.n_events 
        cls.command = 'mxrun'
        if args.additional: cls.command = f"{cls.command} {args.additional}"
        cls.remove_dir(State.WAITING)
        if os.path.exists(cls.sim_file_c): os.remove(cls.sim_file_c)
        if os.path.exists(cls.sim_file_out): os.remove(cls.sim_file_out)
        cls.compile()

    @classmethod
    def remove_dir(cls, state):
        print('\nRemove data directories ...')
        for proc in cls.procs:
            if state==proc.status and os.path.isdir(proc.dir_):
                print(f"Remove dir '{proc.dir_}'")
                # https://pynative.com/python-delete-non-empty-directory/
                rmtree(proc.dir_)

    @classmethod
    def compile(cls):
        out = sp.run(["mcxtrace", cls.sim_file], capture_output=True)
        if not 0==out.returncode:
            print (out.stderr.decode())
            sys.exit(f"error: when running mcxtrace on {cls.sim_file}")
        out = sp.run(["gcc", "-o", cls.sim_file_out, cls.sim_file_c, "-lm", "-g", "-O2", "-lm", "-std=c99"], capture_output=True)
        if not 0==out.returncode:
            print (out.stderr.decode())
            sys.exit(f"error: when compiling {cls.sim_file_c}")

    @classmethod
    def print_output_summary(cls):
        ProcManager.print_output_summary()
        finish_time = 0
        running_perc = 0
        running_eta = 0
        running_eta_c = 0
        finished = waiting = running = error = 0
        # match case only available in 3.10 onwards! https://towardsdatascience.com/the-match-case-in-python-3-10-is-not-that-simple-f65b350bb025
        for proc in cls.procs: # run through process list and update stats appropriately for each state
            s = proc.status
            if State.FINISH==s:
                    finished += 1
                    finish_time += proc.time
            elif State.WAITING==s:
                    waiting += 1
            elif State.RUNNING==s:
                    running += 1
                    running_perc += proc.running_perc
                    if proc.running_eta:
                        running_eta_c += 1
                        running_eta += proc.running_eta
            elif State.ERROR==s:
                    error += 1
        # https://www.delftstack.com/howto/python/python-leading-zeros/
        # https://stackoverflow.com/questions/775049/how-do-i-convert-seconds-to-hours-minutes-and-seconds
        # https://www.peterbe.com/plog/how-to-pad-fill-string-by-variable-python
        running_perc_avg = running_perc/running if running else 0
        running_eta_avg = running_eta/running_eta_c if running_eta_c else 0
        finished_avg = finish_time/finished if finished else 0
        cls.console.status(f"  {waiting:0{cls.t_process_digit}d} waiting,"\
                           +f" {running:0{cls.n_process_digit}d} running {round(running_perc_avg):02d}% ({str(timedelta(seconds=round(running_eta_avg)))}),"\
                           +f" {finished:0{cls.t_process_digit}d} finished ({str(timedelta(seconds=round(finished_avg)))}),"\
                           +f" {error:0{cls.t_process_digit}d} errors")

    @classmethod
    def check_and_cleanup(cls):
        ProcManager.check_and_cleanup()
        if cls.output_file or cls.final_dir or cls.remove: # TODO: remove dirs even of incomplete simulation?
            # check for valid files before copy and delete
            # use list comprehension (https://www.digitalocean.com/community/tutorials/understanding-list-comprehensions-in-python-3) instead of (reduce https://realpython.com/python-reduce-function/)
            errors = [os.path.join(proc.dir_,proc.filename) for proc in cls.procs if (State.FINISH==proc.status and not os.path.isfile(os.path.join(proc.dir_,proc.filename)))]
            if errors:
                print()
                for e in errors: print(f"ERROR {e} is not a valid file")
            # TODO: check why occasional simulation run error when specifying -t instead of csv file
            if not (cls.csv and errors): # only abort copy of file/data if csv file and errors
                if cls.output_file:
                    print(f"\nConcatenate output files into one file called '{cls.output_file}' ...")
                    # https://stackoverflow.com/questions/13613336/how-do-i-concatenate-text-files-in-python
                    with open(cls.output_file,'wb') as wfd:
                        for proc in cls.procs:
                            if State.FINISH==proc.status and os.path.isfile(os.path.join(proc.dir_,proc.filename)):
                                print(f"Add file '{proc.filename}' from dir '{proc.dir_}'")
                                with open(os.path.join(proc.dir_,proc.filename),'rb') as fd:
                                    copyfileobj(fd, wfd)
                if cls.final_dir:
                    print('\nProcess and clean up the directories ...')
                    # https://appdividend.com/2021/07/03/how-to-create-directory-if-not-exist-in-python
                    os.makedirs(cls.final_dir, exist_ok=True)
                    # https://docs.python.org/3/library/shutil.html#shutil.copy
                    for proc in cls.procs:
                        if State.FINISH==proc.status and os.path.isfile(os.path.join(proc.dir_,proc.filename)):
                            print(f"Copy file '{proc.filename}' from dir '{proc.dir_}' to dir '{cls.final_dir}'")
                            copy(os.path.join(proc.dir_,proc.filename),cls.final_dir)
                if cls.remove: cls.remove_dir(State.FINISH) # leave directories where state is State.ERROR

    def __init__(self, params, filename, dir_): # note use of following '_' to avoid keyword confusion
        super(Program, self).__init__()
        (self.params, self.filename, self.dir_) = (params, filename, dir_)
        self.running_eta = 0
        self.running_perc = 0

    def gen_command(self):
        super(Program, self).gen_command()
        # TODO: -c option causes simulation error due to recompile conflct, added delete of .c and .out before sim compile/run and initial run of mcxtrace to regenerate .out
        return f"./{self.sim_file.replace('.instr','.out')} -n {str(self.n_events)} -d {self.dir_} filename={os.path.join(self.dir_,self.filename)}{self.params}"

    def process_output(self, output):
        super(Program, self).process_output(output)
        # sample mxrun output:
        # Trace ETA 7.2 [min] % 2 12 22 32 42
        # Trace ETA 1.55611 [h] % 0
        # Trace ETA 53 [s] % 20 30 40 50 60 70 80 90
        result = re.match(r"^Trace ETA (?P<time>\d+\.?\d*) \[(?P<unit>\w+)\] %.* (?P<percent>\d+)\s*$", output)
        if result and result.group:
            time = 0
            if 's'==result.group('unit'): time = float(result.group('time'))
            if 'min'==result.group('unit'): time = 60*float(result.group('time'))
            if 'h'==result.group('unit'): time = 60*60*float(result.group('time'))
            self.running_eta = time
            self.running_perc = int(result.group('percent'))
        result = re.match(r"^(?P<percent>\d+) $", output)
        if result and result.group:
            self.running_perc = int(result.group('percent'))

def main():
    start_time = time()
    args = ap.parse_args() # parse args TODO: clean up use case for when class imported and not used in script
    Program.setup_proc(args) # create process manager based on the arguments
    Program.gen_init_processes()
    Program.monitor_output_loop()
    Program.check_and_cleanup()
    print(f"\nTotal time elapsed: {str(timedelta(seconds=round(time()-start_time)))} hours:minutes:seconds")

# if started as a command line script then run main loop
if __name__ == '__main__':    
     main()
