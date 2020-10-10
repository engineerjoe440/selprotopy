"""
selprotopy: A Protocol Binding Suite for the SEL Protocol Suite.

Supports:
  - SEL Fast Meter
  - SEL Fast Message
  - SEL Fast Operate

Author(s):
  - Joe Stanley: joe_stanley@selinc.com

Homepage: https://github.com/engineerjoe440/sel-proto-py

SEL Protocol Application Guide: https://selinc.com/api/download/5026/?lang=en
"""

_name_ = "selprotopy"
_version_ = "0.0"
__version__ = _version_ # Alias the Version String

# Local Imports
try:
    from . import commands
    from . import protoparser
except:
    import commands
    import protoparser

# Standard Imports
import time


# Define Simple Polling Client
class PollingClient():
    """
    `PollingClient` Class
    
    The basic polling class intended to interact with an SEL relay which has
    already been connected to by way of a Telnet or Serial connection using one
    of the following Python libraries:
    
    - telnetlib     https://docs.python.org/3/library/telnetlib.html
    - pyserial      https://pyserial.readthedocs.io/en/latest/pyserial.html
    
    Parameters
    ----------
    connApi:            [telnetlib.Telnet, serial.Serial]
                        Telnet or Serial API which will be used to communicate
                        with the SEL relay.
    validConnChecks:    int, optional
                        Integer control to indicate maximum number of connection
                        attempts should be issued to relay in the process of
                        verifying established connection(s). Defaults to 5
    interdelay:         float, optional
                        Floating control which describes the amount of time in
                        seconds between iterative connection verification
                        attempts. Defaults to 0.025 (seconds)
    verbose:            bool, optional
                        Control to dictate whether verbose printing operations
                        should be used (often for debugging and learning purposes).
                        Defaults to False
    
    Attributes
    ----------
    conn:       [telnetlib.Telnet, serial.Serial]
                Connection API
    verbose:    bool
                Verbose information printing record (set by `verbose`)
    check:      int
                Number of connection attempts before indicating failure
                (set by `validConnChecks`)
    delay:      float
                Time (in seconds) to delay between connection attempts
                (set by `interdelay`)
    fid:        str
                Relay's described Firmware ID string (set by connection with relay)
    bfid:       str
                Relay's described BFID string (set by connection with relay)
    cid:        str
                Relay's described CID string (set by connection with relay)
    devid:      str
                Relay's described DEVID string (set by connection with relay)
    partno:     str
                Relay's described part number string (set by connection with relay)
    config:     str
                Relay's described configuration string (set by connection with relay)
    """
    
    def __init__( self, connApi, validConnChecks=5, interdelay=0.025, verbose=False ):
        """ Initialization Method - Returns False if Connection Attempt Fails """
        self.conn = connApi
        self.verbose = verbose
        self.check = validConnChecks
        self.delay = interdelay
        # Verify Connection by Searching for Prompt
        if verbose: print('Verifying Connection...')
        if not self._verify_connection(): return False # Indicate Failure
        if verbose: print('Connection Verified.')
        # Request Relay ID Block
        self.conn.write( commands.ID )
        id_block = protoparser.RelayIdBlock(self._read_to_prompt(),
            encoding='utf-8', verbose=verbose)
        # Store Relay Information
        self.fid    = id_block['FID']
        self.bfid   = id_block['BFID']
        self.cid    = id_block['CID']
        self.devid  = id_block['DEVID']
        self.partno = id_block['PARTNO']
        self.config = id_block['CONFIG']
        # Request Relay Definition
        self.conn.write( commands.RELAY_DEFENITION + commands.CR )
        definition = protoparser.RelayDefinitionBlock(self._read_to_prompt(),
            verbose=verbose)
        print(definition)
        
    # Define Connectivity Check Method
    def _verify_connection( self ):
        # Set Default Indication
        connected = False
        # Iteratively attempt to see relay's response
        for _ in range(self.check):
            self.conn.write( commands.CR )
            response = self.conn.read_until( commands.CR )
            if commands.LEVEL_0 in response:
                # Relay Responded
                connected = True
                break
            else:
                time.sleep( self.delay )
        # Return Status
        return connected
    
    # Define Method to Read All Data to Next Relay Prompt
    def _read_to_prompt( self ):
        response = self.conn.read_until( commands.PROMPT )
        if self.verbose: print(response)
        return response




if __name__ == '__main__':
    import telnetlib
    print('Establishing Connection...')
    with telnetlib.Telnet('192.168.254.10', 23) as tn:
        print('Initializing Client...')
        poller = PollingClient( tn, verbose=True)

# END