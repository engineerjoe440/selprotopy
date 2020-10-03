"""
selprotopy: A Protocol Binding Suite for the SEL Protocol Suite.

Supports:
  - SEL Fast Meter
  - SEL Fast Message
  - SEL Fast Operate
"""

_name_ = "selprotopy"
_version_ = "0.0"

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
    
    """
    
    def __init__( self, connApi, validConnChecks=5, interdelay=0.025, verbose=False ):
        """ Initialization Method """
        self.conn = connApi
        self.verbose = verbose
        self.check = validConnChecks
        self.delay = interdelay
        # Verify Connection by Searching for Prompt
        if verbose: print('Verifying Connection...')
        self._verify_connection()
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
        # Iteratively attempt to see relay's response
        for _ in range(self.check):
            self.conn.write( commands.CR )
            response = self.conn.read_until( commands.CR )
            if commands.LEVEL_0 in response:
                # Relay Responded
                break
            else:
                time.sleep( self.delay )
    
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