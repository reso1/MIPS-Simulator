## Introduction
MIPS simulator that disassembles bytes to the MIPS codes and perform simulations.

## Requirements
+ python 3.x

## Usage
```
$ python MIPSsim.py ${sample_file_path}
```
> Use **Unix(Linux/OSX)** directory format.

> If you are running this python file in **WINDOWS**, please move your sample file to the root directory of MIPSsim.py, and use filename as input file path only. 

After executing is finished, you shall get a disassembly.txt file and a simulation.txt file in the directory of the sample.txt.

## Example:
+ **Linux / OSX**

`$ python MIPSsim.py test/sample.txt`

+ **Windows**

`$ python MIPSsim.py sample.txt`
