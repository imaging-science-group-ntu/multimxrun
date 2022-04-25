# multimxrun
Utility to run several instances of the McXtrace simulation utility in separate processes
```bash
usage: multimxrun.py [-h] [-n N_EVENTS] [-d DIR] [-r] [-o OUTPUT] [-e PREFIX] [-a ADDITIONAL] [-c CSV_INPUT | -t T_PROCESS]
                     [-p N_PROCESS] [-s SLEEP_SEC] [-v]
                     sim_file
```
McXtrace Simulation Multiprocess Run Utility. This script allows the user to run several copies of McXtrace in separate processes.
There are two modes that can be used: (1) Identical simulation file repeated multiple times to achieve greater statistical
accuracy (2) Simulation parameters determined uniquely for each simulation via a CSV file with one row for each
simulation/process. If number of concurrent processes to run not specified, it automatically gets number of CPU cores and uses
that for n_process value.

## Arguments

<table>
    <thead>
        <tr>
            <th>Argument</th>
            <th>Label</th>
            <th>Optional</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>-h | --help</td>
            <td>Displays help information for multimxrun.</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-v | --verbose</td>
            <td>Verbose output</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>sim_file</td>
            <td>File Path String to the instrument file being compiled and then simulated. Must be included as the final argument.</td>
            <td>No, Final argument</td>
        </tr>
        <tr>
            <td>-n N_EVENTS | --n_events N_EVENTS</td>
            <td>Number of events to run per-simulation, replace "N_EVENTS" with an integer. Default: 1E8.</td>
            <td>No</td>
        </tr>
        <tr>
            <td>-d DIR | --dir DIR</td>
            <td>File Path String for the directory to save all files in, replace "DIR" with the output directory.</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-r | --remove</td>
            <td>Delete all individual simulation directories after all simulations complete.</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-o OUTPUT | --output OUTPUT</td>
            <td>File Path String to concatonate all data files into a single output file, replace "OUTPUT" with the output file path.</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-e PREFIX | --prefix PREFIX</td>
            <td>Prefix for auto-generated simulation name. Default: "sim_data_".</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-a ADDITIONAL | --additional ADDITIONAL</td>
            <td>Additional command line options parsed through to the simulation.</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-c CSV | --csv_input CSV</td>
            <td>File Path String to a CSV file containing one line per-simulation, replace "CSV" with the file path to the input CSV file. <a href="README.md#CSV_File" title="CSV File Formatting">CSV File Formatting</a></td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-t T_PROCESS | --t_process T_PROCESS</td>
            <td>Total Number of processes to run. Defaults: (CSV file used) # CSV rows, (no CSV file used) "N_Process".</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-n N_PROCESS | --n_process N_PROCESS</td>
            <td>Total number of processes to simulate concurrently, replace "N_PROCESS" with integer number of cores. Default: # CPU cores.</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-s SLEEP | --sleep_sec SLEEP</td>
            <td>Number of seconds between each iteration of the monitoring loop, replace "SLEEP" with integer number of seconds. Default: 1.</td>
            <td>Yes</td>
        </tr>
    </tbody>
</table>

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


## To-do
* check if executable is in different dir then working dir is correct
* instead of assuming instrument file ends in .instr, extract the file type from the string

## Example Uses:
### Identical Simulations
Run 8 copies of the instrument file 'Single_Hexagonal_Channel.instr' on all CPU cores, number of events is 10E6, and concatenate data into one file 'out.dat', deleting all data directories afterwards:
```python
./multimxrun.py -r -n 10000000 -o data.dat -t 8 Single_Hexagonal_Channel.instr
```

### Unique Simulations
Use the CSV file 'Test.csv' to specify parameters for each process of the instrument file 'Single_Hexagonal_Channel.instr' on all CPU cores, number of events is 10E6, and moving all the data files resulting from the simulations into a single directory called 'out', then deleting all data directories afterwards:
```python
./multimxrun.py -r -n 10000000 -d out -c Test.csv Single_Hexagonal_Channel.instr
```

## References
Author: Imaging Science Research Group, Nottingham Trent University
License: GPL version 3 or later
Version: 0.1