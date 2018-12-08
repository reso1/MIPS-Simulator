import sys
import src.main as main
import src.utils as utils

sample_path = str(sys.argv[1])

p = main.program(sample_path)

""" Project 1 """
# disassembly_str, simulation_str = p.simulate()
#utils.write(p.DISASSEMBLY_FILENAME, disassembly_str)
#utils.write(p.SIMULATION_FILENAME, simulation_str)

""" Project 2 """
disassembly_str, pipeline_str = p.pipeline()
utils.write(p.DISASSEMBLY_FILENAME, disassembly_str)
utils.write(p.PIPELINE_FILENAME, pipeline_str)