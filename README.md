## Introduction
### **Proj1**
MIPS simulator that disassembles bytes to the MIPS codes and perform simulations.

### **Proj2**
MIPS simulator that disassembles bytes to the MIPS codes and perform 4-stages pipeline : 
 *IF => Issue => ALU/ALUB/MEM => WB*


## Requirements
+ python 3.x

## Usage
```
$ python MIPSsim.py ${sample_file_path}
```
> Use **Unix(Linux/OSX)** directory format.

> If you are running this python file in **WINDOWS**, please move your sample file to the root directory of MIPSsim.py, and use filename as input file path only. 

### **Proj1**
After executing is finished, you shall get a disassembly.txt file and a simulation.txt file in the directory of the sample.txt.

### **Proj2**
After executing is finished, you shall get a disassembly.txt file and a pipeline.txt file in the directory of the sample.txt.

## Example:
+ **Linux / OSX**

`$ python MIPSsim.py test/sample.txt`

+ **Windows**

`$ python MIPSsim.py sample.txt`
