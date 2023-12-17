################################################################################
"""
selprotopy: A Protocol Binding Suite for the SEL Protocol Suite.

Supports:
    - SEL Fast Meter
    - SEL Fast Message
    - SEL Fast Operate

Author(s):
    - Joe Stanley: engineerjoe440@yahoo.com

Homepage: https://github.com/engineerjoe440/sel-proto-py

SEL Protocol Application Guide: https://selinc.com/api/download/5026/
"""
################################################################################

# Standard Imports
import telnetlib

# Local Imports
from selprotopy.support import telnet

# Describe Package for External Interpretation
__version__ = "0.1.0"

# `telnetlib` Discards Null Characters, but SEL Protocol Requires them
telnetlib.Telnet.process_rawq = telnet.process_rawq
