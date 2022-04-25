# multimxrun
Utility to run several instances of the McXtrace simulation utility in separate processes using ```python 3.9```.

## Contents
* <a href="README.md#Arguments" title="Arguments">Arguments</a>.
* <a href="README.md#CSV_File_Formatting" title="CSV File Formatting">CSV File Formatting</a>.
* <a href="README.md#Examples" title="Examples">Examples</a>.
* <a href="README.md#References" title="References">References</a>.

## Example command line syntax
```bash
multimxrun.py [-h] [-n N_EVENTS] [-d DIR] [-r] [-o OUTPUT] [-e PREFIX] [-a ADDITIONAL]
                [-c CSV_INPUT | -t T_PROCESS]
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
            <td>-n N_EVENT | --n_events N_EVENT</td>
            <td>Number of events to run per-simulation, replace "N_EVENT" with an integer. Default: 1E8.</td>
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
            <td>-o OUT | --output OUT</td>
            <td>File Path String to concatonate all data files into a single output file, replace "OUTPUT" with the output file path.</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-e PREFIX | --prefix PREFIX</td>
            <td>Prefix for auto-generated simulation name. Default: "sim_data_".</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-a ADD | --additional ADD</td>
            <td>Additional command line options parsed through to the simulation, replace "ADD" with valid MCXTrace command line options.</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-c CSV | --csv_input CSV</td>
            <td>File Path String to a CSV file containing one line per-simulation, replace "CSV" with the file path to the input CSV file. <a href="README.md#CSV_File_Formatting" title="CSV File Formatting">CSV File Formatting</a></td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-t T_PROC | --t_process T_PROC</td>
            <td>Total Number of processes to run, replace "T_PROC" with an integer number of simulations to run. Defaults: # CSV rows (CSV file used) or "N_PROC" (no CSV file used).</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-n N_PROC | --n_process N_PROC</td>
            <td>Total number of processes to simulate concurrently, replace "N_PROC" with integer number of cores. Default: # CPU cores.</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-s SLEEP | --sleep_sec SLEEP</td>
            <td>Number of seconds between each iteration of the monitoring loop, replace "SLEEP" with integer number of seconds. Default: 1.</td>
            <td>Yes</td>
        </tr>
    </tbody>
</table>

## CSV File Formatting
When using a CSV file:
* one simulation will be ran per-line of the CSV file, where the variable values in each line of the CSV file are read in and applied one simulation at a time.
* The CSV file must consist of named column headers labelling the variables on the first row, this is in order for the script to determine which CSV file column corresponds to each variable in the simulated instrument.
* The CSV file must form a perfect grid, all CSV columns must be the same length with the same number of variables.
* The ```-t``` argument is automatically set to the number of lines in the CSV file and is no longer required to be specified. 
* ```filename``` is a required named column and can't be substitued for another name, although it can be supplimented by another name in addition for multiple output files for different monitors (for example).

Example CSV use for an instrument with parameters ```filename```, ```Test_X``` and ```Test_Y```.
```C
DEFINE INSTRUMENT Example_Dynamic_CSV_Simulation(char *filename = "test.xbd", Test_X = 0.0, Test_Y = 0.0)
```

Example CSV file ```Test.csv``` corresponding to the specified instrument. Note that text fields such as filenames must be quoted as strings when inspected in a raw text editor such as notepad.
```C
X,Y,filename
0.1,0.2,"Test_0.xbd"
0.05,0.1,"Test_1.xbd"
0.0,0.0,"Test_2.xbd"
-0.05,-0.1,"Test_3.xbd"
0.1,-0.2,"Test_4.xbd"
```

In this case, the first simulation will use variables `X = 0.1`, `Y = 0.2`, `filename = "Test_0.xbd`, the second simulation would then use the variables `X = 0.05`, `Y = 0.1`, `filename = "Test_1.xbd`, this continues until the end of the CSV file is reached.

## Examples:
### Identical Simulations
Run 8 total simulations of the instrument file ```Example_Static_Simulation.instr``` across as many CPU cores as possible, number of events is 10E6, concatenate data into a single file 'out.dat' and delete all individual simulation directories afterwards:
```python
./multimxrun.py -r -n 10000000 -o data.dat -t 8 Example_Static_Simulation.instr
```

### Unique Simulations
Use the CSV file ```Test.csv``` to specify parameters for each process of the instrument file ```Example_Dynamic_CSV_Simulation.instr``` on all CPU cores, number of events is 10E6, moving all the data files resulting from the simulations into a single directory called 'out', then deleting all data directories afterwards:
```python
./multimxrun.py -r -n 10000000 -d out -c Test.csv Example_Dynamic_CSV_Simulation.instr
```
For reference CSV file content for this example, see <a href="README.md#CSV_File_Formatting" title="CSV File Formatting">CSV File Formatting</a>.

## To-do
* check if executable is in different dir then working dir is correct
* instead of assuming instrument file ends in .instr, extract the file type from the string

## References
Author: Imaging Science Research Group, Nottingham Trent University

License: GPL version 3 or later

Version: 0.1

Built with: [Python 3.9](https://www.python.org/downloads/release/python-390/)