"""
selprotopy: A Protocol Binding Suite for the SEL Protocol Suite.

Supports:
  - SEL Fast Meter
  - SEL Fast Message
  - SEL Fast Operate

Author(s):
  - Joe Stanley: joe_stanley@selinc.com

Homepage: https://github.com/engineerjoe440/sel-proto-py

SEL Protocol Application Guide: https://selinc.com/api/download/5026/
"""

# Standard Imports
import telnetlib

# Local Imports
from selprotopy import telnetlib_support
from selprotopy.client import SelClient # Alias class for easy access

# Describe Package for External Interpretation
_name_ = "selprotopy"
_version_ = "0.1"
__version__ = _version_  # Alias the Version String

# `telnetlib` Discards Null Characters, but SEL Protocol Requires them
telnetlib.Telnet.process_rawq = telnetlib_support.process_rawq
