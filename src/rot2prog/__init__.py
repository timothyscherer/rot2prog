"""This is a python interface to the Alfa ROT2Prog Controller. The ROT2Prog is an electronic controller used for turning rotators. The Controller may be connected to one Azimuth and Elevation rotator and operates with direct current motors. The ROT2Prog is designed to work with either an Alfa RAS or BIGRAS or a combination of one azimuth rotator RAU, RAK and a REAL rotator.

This package is responsible for implementing the serial protocol to interact with the ROT2Prog controller. There is also a simulation model of the ROT2Prog controller included in the package, which can be used for testing when hardware is not available.
"""
from rot2prog.rot2prog import ROT2Prog
from rot2prog.rot2prog import ROT2ProgSim