# multimxrun
Utility to run several instances of the McXtrace simulation utility in separate processes using ```python 3.6```.

This script allows the user to run several copies of McXtrace in separate processes.

There are two modes that can be used:
1. Identical simulation file repeated multiple times to achieve greater statistical accuracy
2. Simulation parameters determined uniquely for each simulation via a CSV file, with one row for each simulation/process.

## Documentation Contents
* <a href="README.md#Arguments" title="Arguments">Arguments</a>.
* <a href="README.md#CSV-File-Formatting" title="CSV File Formatting">CSV File Formatting</a>.
* <a href="README.md#Examples" title="Examples">Examples</a>.
* <a href="README.md#References" title="References">References</a>.

## Command-Line Syntax Overview
```bash
multimxrun.py [-h] [-n N_EVENTS] [-d DIR] [-r] [-o OUTPUT] [-e PREFIX] [-a ADDITIONAL]
              [-c CSV_INPUT | -t T_PROCESS][-p N_PROCESS] [-s SLEEP_SEC] [-v] sim_file
```

## Arguments
Full documentation for list of command-line arguments for multimxrun.
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
            <td>-h</td>
            <td>Displays help information for multimxrun including all command line arguments and their descriptions.</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-v</td>
            <td>Verbose output</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-n N_EVENT</td>
            <td>Number of events to run per-simulation, replace "N_EVENT" with an integer. Default: 1E8.</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-d DIR</td>
            <td>File Path String for the directory to save all files in, replace "DIR" with the output directory.</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-r</td>
            <td>Delete all individual simulation directories after all simulations complete.</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-o OUT</td>
            <td>File Path String to concatonate all data files into a single output file, replace "OUTPUT" with the output file path.</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-e PREFIX</td>
            <td>Prefix for auto-generated simulation name. Default: "sim_data_".</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-a ADD</td>
            <td>Additional command line options parsed through to the simulation, replace "ADD" with valid MCXTrace command line options.</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-c CSV</td>
            <td>File Path String to a CSV file containing one line per-simulation, replace "CSV" with the file path to the input CSV file. <a href="#CSV-File-Formatting" title="CSV File Formatting">CSV File Formatting</a></td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-t T_PROC</td>
            <td>Total Number of processes to run, replace "T_PROC" with an integer number of simulations to run. Defaults: # CSV rows (CSV file used) or "N_PROC" (no CSV file used).</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-n N_PROC</td>
            <td>Total number of processes to simulate concurrently, replace "N_PROC" with integer number of cores. Default: # CPU cores.</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>-s SLEEP</td>
            <td>Number of seconds between each iteration of the monitoring loop, replace "SLEEP" with integer number of seconds. Default: 1.</td>
            <td>Yes</td>
        </tr>
        <tr>
            <td>sim_file</td>
            <td>File Path String to the instrument file being compiled and then simulated. Must be included as the final argument.</td>
            <td>No, Final argument</td>
        </tr>
    </tbody>
</table>

## CSV File Formatting
### CSV File Formatting Rules
When using a CSV file:
* One simulation will be ran per-line of the CSV file, where the variable values in each individual line of the CSV file are read in and applied during each sequentially started simulation respectively.
* Each individual variable named in the instrument file must correspond to a single column in the CSV file, with the variable names listed one per-column in the first row of the CSV file. This is in order for the script to determine parity between the simulation and CSV file, matching each CSV file column with the corresponding variable in the simulated instrument.
* The data for simulations is entered from the second row of the CSV file, data must form a 'perfect grid' which directly corresponds to the instrument file:
  * All rows must have a value set for all named variables (each column).
  * Each CSV column must have an identical number of rows.
* The ```-t``` argument is automatically set to the number of rows in the CSV file and is no longer required to be specified. 
* ```filename``` is a required named column and can't be substitued for another name, although it can be supplimented by a second text variable in addition; for example, ```PSD_filename``` could be used in addition to ```filename``` when using multiple output data files for multiple monitors during a single execution of a simulated instrument.

### CSV Example
Example instrument definition and corresponding CSV file content.
#### Instrument
An instrument ```Example_Dynamic_CSV_Simulation.instr``` with parameters ```filename```, ```Test_X``` and ```Test_Y```.
```C
DEFINE INSTRUMENT Example_Dynamic_CSV_Simulation(char *filename = "test.xbd", Test_X = 0.0, Test_Y = 0.0)
```

#### Sample CSV File
```Test.csv``` corresponding to the specified instrument ```Example_Dynamic_CSV_Simulation.instr``` above. Note that text fields such as filenames must be quoted as strings when inspected in a raw text editor such as notepad, correct ordering of columns isn't required.
```C
"Test_X","Test_Y","filename"
0.1,0.2,"Test_0.xbd"
0.05,0.1,"Test_1.xbd"
0.0,0.0,"Test_2.xbd"
-0.05,-0.1,"Test_3.xbd"
0.1,-0.2,"Test_4.xbd"
```

In this case, the first simulation will use variables `X = 0.1`, `Y = 0.2`, `filename = "Test_0.xbd"`, the second simulation would then use the variables `X = 0.05`, `Y = 0.1`, `filename = "Test_1.xbd"`, continuing until the final row of the CSV file is reached.

## Examples
### Identical Simulations
Run 8 instances of identical simulations of the instrument file ```Example_Static_Simulation.instr``` across as many CPU cores as possible, number of events is 10E6, concatenate data into a single file ```data.dat``` and then deleting all individual simulation directories afterwards:
```python
./multimxrun.py -n 10000000 -r -o data.dat -t 8 Example_Static_Simulation.instr
```

### Unique Simulations
Use the CSV file ```Test.csv``` to specify parameters for each process of the instrument file ```Example_Dynamic_CSV_Simulation.instr``` on all CPU cores, number of events is 10E6, moving all the data files resulting from the simulations into a single directory called ```out``` and retaining all individual simulation directories afterwards:
```python
./multimxrun.py -n 10000000 -d out -c Test.csv Example_Dynamic_CSV_Simulation.instr
```
For reference CSV file content for this example, see <a href="README.md#CSV-File-Formatting" title="CSV File Formatting">CSV File Formatting</a>.

## To-do
* check if executable is in different dir then working dir is correct
* instead of assuming instrument file ends in .instr, extract the file type from the string

## References
Author: Imaging Science Research Group, Nottingham Trent University\
License: GPL version 3 or later\
Version: 0.1\
Tested using: [Python 3.9](https://www.python.org/downloads/release/python-390/)
