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

# Standard Imports
import time
import telnetlib

# Local Imports
from selprotopy import exceptions
from selprotopy import commands
from selprotopy import protoparser
from selprotopy import telnetlib_support

# Describe Package for External Interpretation
_name_ = "selprotopy"
_version_ = "0.1"
__version__ = _version_  # Alias the Version String

# `telnetlib` Discards Null Characters, but SEL Protocol Requires them
telnetlib.Telnet.process_rawq = telnetlib_support.process_rawq


# Define Simple Polling Client
class SelClient():
    """
    `SelClient` Class

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
    autoconfig_now:     bool, optional
                        Control to activate automatic configuration with the
                        connected relay at time of class initialization, this
                        should normally be set to True to allow autoconfig.
                        Defaults to True
    validConnChecks:    int, optional
                        Integer control to indicate maximum number of
                        connection attempts should be issued to relay in the
                        process of verifying established connection(s).
                        Defaults to 5
    interdelay:         float, optional
                        Floating control which describes the amount of time in
                        seconds between iterative connection verification
                        attempts. Defaults to 0.025 (seconds)
    logger:             logging.logger
                        Logging object to record communications messages.
    verbose:            bool, optional
                        Control to dictate whether verbose printing operations
                        should be used (often for debugging and learning
                        purposes). Defaults to False

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
                Relay's described Firmware ID string (set by connection with
                relay)
    bfid:       str
                Relay's described BFID string (set by connection with relay)
    cid:        str
                Relay's described CID string (set by connection with relay)
    devid:      str
                Relay's described DEVID string (set by connection with relay)
    partno:     str
                Relay's described part number string (set by connection with
                relay)
    config:     str
                Relay's described configuration string (set by connection with
                relay)
    """

    def __init__( self, connApi, autoconfig_now=True, validConnChecks=5,
                  interdelay=0.025, logger=None, verbose=False,
                  debug=False, **kwargs ):
        """ Initialization Method - Returns False if Connection Fails """
        # Initialize Inputs
        self.conn = connApi
        self.verbose = verbose
        self.check = validConnChecks
        self.delay = interdelay
        self.logger = logger
        self.debug = debug

        # Initialize Timout if Applicable
        if 'timeout' in kwargs.keys():
            self.timeout = kwargs['timeout']
        else:
            self.timeout = 60

        # Define Basic Parameter Defaults
        self.fid     = ''
        self.bfid    = ''
        self.cid     = ''
        self.devid   = ''
        self.partno  = ''
        self.config  = ''

        # Define the Various Command Defaults
        self.fmconfigcommand1   = commands.FM_CONFIG_BLOCK
        self.fmcommand1         = commands.FM_DEMAND_CONFIG_BLOCK
        self.fmconfigcommand2   = commands.FM_PEAK_CONFIG_BLOCK
        self.fmcommand2         = commands.FAST_METER_REGULAR
        self.fmconfigcommand3   = commands.FAST_METER_DEMAND
        self.fmcommand3         = commands.FAST_METER_PEAK_DEMAND
        self.fopcommandinfo     = commands.FO_CONFIG_BLOCK
        self.fmsgcommandinfo    = commands.FAST_MSG_CONFIG_BLOCK

        # Allocate Space for Relay Definition Responses
        self.fastMeterDef       = None
        self.fastDemandDef      = None
        self.fastPkDemandDef    = None

        # Verify Connection by Searching for Prompt
        if verbose: print('Verifying Connection...')
        if not self._verify_connection():
            raise exceptions.ConnVerificationFail("Verification Failed.")
        if verbose: print('Connection Verified.')
        self.quit()
        if autoconfig_now:
            # Run Auto-Configuration
            self.autoconfig(verbose=verbose)

    # Define Connectivity Check Method
    def _verify_connection( self ):
        # Set Default Indication
        connected = False
        # Iteratively attempt to see relay's response
        for _ in range(self.check):
            self.conn.write( commands.CR + commands.CR + commands.CR )
            response = self.conn.read_until( commands.CR )
            if self.debug: print(response)
            if commands.LEVEL_0 in response:
                # Relay Responded
                connected = True
                break
            else:
                time.sleep( self.delay )
        # Return Status
        return connected

    # Define Method to "Clear" the Buffer
    def _clear_input_buffer( self ):
        try:
            resp = self.conn.read_very_eager()
            if self.logger: self.logger.info(f'Rx: {resp}')
            if self.debug: print('Clearing buffer:', resp)
            while b'' != resp:
                time.sleep(self.delay * 10)
                resp = self.conn.read_very_eager()
                if self.logger: self.logger.info(f'Rx: {resp}')
                if self.debug: print('Clearing buffer:', resp)
        except Exception:
            self.conn.reset_input_buffer()

    # Define Method to Read All Data to Next Relay Prompt
    def _read_to_prompt( self, prompt_str=commands.PROMPT ):
        # Telnetlib Supports a Timeout
        if isinstance(self.conn, telnetlib.Telnet):
            response = self.conn.read_until( commands.PROMPT,
                                             timeout=self.timeout )
        # PySerial Does not Support Timeout
        else:
            response = self.conn.read_until( commands.PROMPT )
        if self.logger: self.logger.info(f'Rx: {response}')
        if self.debug: print(response)
        return response

    # Define Method to Read All Data After a Command (and to next relay prompt)
    def _read_command_response( self, command, prompt_str=commands.PROMPT ):
        if isinstance(command, bytes):
            command = command.replace(b'\n', b'')
            command = command.replace(b'\r', b'')
        elif isinstance(command, str):
            command = command.replace('\n', '')
            command = command.replace('\r', '')
        response = b''
        i = 0
        while (response.find(command) == -1) and (i < 10):
            sz = len(response)  # Capture Previous Size
            response += self._read_to_prompt( prompt_str=prompt_str )
            i = 0 if len(response) != sz else i + 1
        return response

    # Define Method to Read Until a "Clean" Prompt is Viewed
    def _read_clean_prompt( self ):
        count = 0
        response = b''
        while count < 3:
            self.conn.write( commands.CR )      # Write
            response += self._read_to_prompt()   # Read
            if self.debug: print('Clean prompt response:', response)
            # Count the Number of Clean Prompt Responses
            if protoparser.CleanPrompt(response):
                count += 1
            else:
                count = 0
            time.sleep(self.delay)
        self._clear_input_buffer()  # Empty anything left in the buffer
        time.sleep(self.delay)

    # Define Method to Attempt Reading Everything (only for telnetlib)
    def _read_everything( self ):
        response = self.conn.read_very_eager()
        if self.logger: self.logger.info(f'Rx: {response}')
        if self.debug: print(response)
        return response

    # Define Method to Identify Current Access Level
    def access_level(self):
        """
        `access_level`

        Simple method to identify what the current access level
        is for the connected relay. Provides an integer and
        string.

        Returns
        -------
        int:    Integer representing the access level
                as a value in the range of [0, 1, 2, 3]
        desc:   String describing the access level,
                will return empty string for level-0.
        """
        # Retrieve Prompt Twice
        self.conn.write( commands.CR )
        resp = self._read_to_prompt()
        self.conn.write( commands.CR )
        resp += self._read_to_prompt()
        # Look for Each Level, Return Highest Found
        if commands.LEVEL_C in resp:
            return (3, 'CAL')
        elif commands.LEVEL_2 in resp:
            return (2, '2AC')
        elif commands.LEVEL_1 in resp:
            return (1, 'ACC')
        else:
            return (0, '')

    # Define Method to Return to Access Level 0
    def quit(self):
        """
        `quit` Method

        Simple method to send the QUIT command to an
        actively connected relay.

        See Also
        --------
        access_level_1      : Elevate permission to ACC
        access_level_2      : Elevate permission to 2AC
        """
        self.conn.write( commands.QUIT )
        self._read_to_prompt( commands.LEVEL_0 )
        self._read_clean_prompt()

    # Define Method to Access Level 1
    def access_level_1(self, level_1_pass=commands.PASS_ACC, **kwargs):
        """
        `access_level_1` Method

        Used to elevate connection privileges with the connected
        relay to ACC with the appropriate password specified. If
        called when current access level is greater than ACC, this
        method will deescalate the permission level to ACC.

        See Also
        --------
        quit                : Relinquish all permission with relay
        access_level_2      : Elevate permission to 2AC

        Parameters
        ----------
        level_1_pass:       str, optional
                            Password necessary to access the ACC
                            level, only required if accessing ACC
                            from level 0 (i.e. logging in).

        Returns
        -------
        success:            bool
                            Indicator of whether the login failed.
        """
        # Identify Current Access Level
        time.sleep( self.delay )
        level, name = self.access_level()
        if self.debug: print("Logging in to ACC")
        self.conn.write( commands.GO_ACC )
        # Provide Password
        if level == 0:
            time.sleep( int(self.delay * 3) )
            self.conn.write( level_1_pass + commands.CR )
            time.sleep( self.delay )
        resp = self._read_to_prompt( commands.LEVEL_0 )
        if b'Invalid' in resp:
            if self.debug: print("Log-In Failed")
            return False
        else:
            if self.debug: print("Log-In Succeeded")
            return True

    # Define Method to Access Level 2
    def access_level_2(self, level_2_pass=commands.PASS_2AC, **kwargs):
        """
        `access_level_2` Method

        Used to elevate connection privileges with the connected
        relay to 2AC with the appropriate password specified. If
        called when current access level is greater than 2AC, this
        method will deescalate the permission level to 2AC.

        See Also
        --------
        quit                : Relinquish all permission with relay
        access_level_1      : Elevate permission to ACC

        Parameters
        ----------
        level_2_pass:       str, optional
                            Password necessary to access the 2AC
                            level, only required if accessing 2AC
                            from level 1 (i.e. logging in).

        Returns
        -------
        success:            bool
                            Indicator of whether the login failed.
        """
        # Identify Current Access Level
        level, name = self.access_level()
        # Provide Password
        if level == 0:
            if not self.access_level_1( **kwargs ):
                return False
        if self.debug: print("Logging in to 2AC")
        self.conn.write( commands.GO_2AC )
        if level in [0, 1]:
            time.sleep( int(self.delay * 3) )
            self.conn.write( level_2_pass + commands.CR )
            time.sleep( self.delay )
        resp = self._read_to_prompt( commands.LEVEL_0 )
        if b'Invalid' in resp:
            if self.debug: print("Log-In Failed")
            return False
        else:
            if self.debug: print("Log-In Succeeded")
            return True

    # Define Method to Perform Auto-Configuration Process
    def autoconfig( self, verbose=False, **kwargs ):
        """
        `autoconfig` Method

        Method to operate the standard auto-configuration process
        with a connected relay to identify the system parameters of
        the relay. This includes:

        - FID
        - BFID
        - CID
        - DEVID
        - PARTNO
        - CONFIG
        - Relay Definition Block

        This method also automatically interprets the following fast
        meter blocks by way of separate method calls.

        - Fast Meter Configuration Block
        - Fast Meter Demand Configuration Block
        - Fast Meter Peak Demand Configuration Block
        - Fast Operate Configuration Block

        See Also
        --------
        autoconfig_fastmeter            : Auto Configuration for Fast Meter
        autoconfig_fastmeter_demand     : Auto Configuration for Fast Meter
                                            Demand
        autoconfig_fastmeter_peakdemand : Auto Configuration for Fast Meter
                                            Peak Demand
        autoconfig_fastoperate          : Auto Configuration for Fast Operate

        Parameters
        ----------
        verbose:        bool, optional
                        Control to dictate whether verbose printing operations
                        should be used (often for debugging and learning
                        purposes). Defaults to False

        Returns
        -------
        fid:            str
                        Relay's Configured FID as Confirmation of Successful
                        Automatic Configuration
        """
        self.quit()
        # Request Relay Definition
        if verbose: print("Reading Relay Definition Block...")
        self.conn.write( commands.RELAY_DEFENITION + commands.CR )
        definition = protoparser.RelayDefinitionBlock(
            self._read_command_response(commands.RELAY_DEFENITION),
            verbose=self.debug
        )
        # Load the Relay Definition Information and Request the Meter Blocks
        if definition['fmmessagesup'] >= 1:
            if verbose:
                print("Reading Fast Meter Definition Block...")
            self.fmconfigcommand1   = \
                definition['fmcommandinfo'][0]['configcommand']
            self.fmcommand1         = \
                definition['fmcommandinfo'][0]['command']
            self.autoconfig_fastmeter( verbose=self.debug )
        if definition['fmmessagesup'] >= 2:
            if verbose:
                print("Reading Fast Meter Demand Definition Block...")
            self.fmconfigcommand2   = \
                definition['fmcommandinfo'][1]['configcommand']
            self.fmcommand2         = \
                definition['fmcommandinfo'][1]['command']
            self.autoconfig_fastmeter_demand( verbose=self.debug )
        if definition['fmmessagesup'] >= 3:
            if verbose:
                print("Reading Fast Meter Peak Demand Definition Block...")
            self.fmconfigcommand3   = \
                definition['fmcommandinfo'][2]['configcommand']
            self.fmcommand3         = \
                definition['fmcommandinfo'][2]['command']
            self.autoconfig_fastmeter_peakdemand( verbose=self.debug )
        if definition['fopcommandinfo'] != '':
            if verbose:
                print("Reading Fast Operate Definition Block...")
            self.fopcommandinfo     = definition['fopcommandinfo']
            self.autoconfig_fastoperate( verbose=self.debug )
        if definition['fmsgcommandinfo'] != '':
            if verbose:
                print("Reading Fast Message Definition Block...")
            self.fmsgcommandinfo    = definition['fmsgcommandinfo']
        # Determine if Level 0, and Escalate Accordingly
        if self.access_level()[0] == 0:
            # Access Level 1 Required to Request DNA
            self.access_level_1( **kwargs )
        # Request Relay ENA Block
        # TODO
        # Request Relay DNA Block
        self._read_clean_prompt()
        if verbose: print("Reading Relay DNA Block...")
        self.conn.write( commands.DNA )
        self.dnaDef = protoparser.RelayDnaBlock(
            self._read_command_response(commands.DNA),
            encoding='utf-8',
            verbose=self.debug
        )
        # Request Relay BNA Block
        # TODO
        # Request Relay ID Block
        if verbose: print("Reading Relay ID Block...")
        self.conn.write( commands.ID )
        id_block = protoparser.RelayIdBlock(
            self._read_command_response(commands.ID),
            encoding='utf-8',
            verbose=self.debug
        )
        # Store Relay Information
        self.fid    = id_block['FID']
        self.bfid   = id_block['BFID']
        self.cid    = id_block['CID']
        self.devid  = id_block['DEVID']
        self.partno = id_block['PARTNO']
        self.config = id_block['CONFIG']
        # Return the Relay's FID
        return self.fid

    # Define Method to Run the Fast Meter Configuration
    def autoconfig_fastmeter(self, verbose=False):
        """
        `autoconfig_fastmeter` Method

        Method to operate the standard auto-configuration process
        with a connected relay to identify the standard fast meter
        parameters of the relay.

        See Also
        --------
        autoconfig                      : Relay Auto Configuration
        autoconfig_fastmeter_demand     : Auto Config for Fast Meter Demand
        autoconfig_fastmeter_peakdemand : Auto Config for Fast Meter Pk Demand
        autoconfig_fastoperate          : Auto Config for Fast Operate

        Parameters
        ----------
        verbose:        bool, optional
                        Control to dictate whether verbose printing operations
                        should be used (often for debugging purposes).
                        Defaults to False
        """
        # Fast Meter
        self._read_clean_prompt()
        self.conn.write( self.fmconfigcommand1 + commands.CR )
        self.fastMeterDef = protoparser.FastMeterConfigurationBlock(
            self._read_to_prompt(), verbose=verbose
        )

    # Define Method to Run the Fast Meter Demand Configuration
    def autoconfig_fastmeter_demand(self, verbose=False):
        """
        `autoconfig_fastmeter_demand` Method

        Method to operate the standard auto-configuration process
        with a connected relay to identify the fast meter demand
        parameters of the relay.

        See Also
        --------
        autoconfig                      : Relay Auto Configuration
        autoconfig_fastmeter            : Auto Config for Fast Meter
        autoconfig_fastmeter_peakdemand : Auto Config for Fast Meter Pk Demand
        autoconfig_fastoperate          : Auto Config for Fast Operate

        Parameters
        ----------
        verbose:        bool, optional
                        Control to dictate whether verbose printing operations
                        should be used (often for debugging purposes).
                        Defaults to False
        """
        # Fast Meter Demand
        self._read_clean_prompt()
        self.conn.write( self.fmconfigcommand2 + commands.CR )
        self.fastDemandDef = protoparser.FastMeterConfigurationBlock(
            self._read_to_prompt(), verbose=verbose
        )

    # Define Method to Run the Fast Meter Peak Demand Configuration
    def autoconfig_fastmeter_peakdemand(self, verbose=False):
        """
        `autoconfig_fastmeter_peakdemand` Method

        Method to operate the standard auto-configuration process
        with a connected relay to identify the fast meter peak demand
        parameters of the relay.

        See Also
        --------
        autoconfig                      : Relay Auto Configuration
        autoconfig_fastmeter            : Auto Config for Fast Meter
        autoconfig_fastmeter_demand     : Auto Config for Fast Meter Demand
        autoconfig_fastoperate          : Auto Config for Fast Operate

        Parameters
        ----------
        verbose:        bool, optional
                        Control to dictate whether verbose printing operations
                        should be used (often for debugging purposes).
                        Defaults to False
        """
        # Fast Meter Peak Demand
        self._read_clean_prompt()
        self.conn.write( self.fmconfigcommand3 + commands.CR )
        self.fastPkDemandDef = protoparser.FastMeterConfigurationBlock(
            self._read_to_prompt(), verbose=verbose
        )

    # Define Method to Run the Fast Operate Configuration
    def autoconfig_fastoperate(self, verbose=False):
        """
        `autoconfig_fastoperate` Method

        Method to operate the standard auto-configuration process
        with a connected relay to identify the fast operate parameters
        of the relay.

        See Also
        --------
        autoconfig                      : Relay Auto Configuration
        autoconfig_fastmeter            : Auto Config for Fast Meter
        autoconfig_fastmeter_demand     : Auto Config for Fast Meter Demand
        autoconfig_fastmeter_peakdemand : Auto Config for Fast Meter Pk Demand

        Parameters
        ----------
        verbose:        bool, optional
                        Control to dictate whether verbose printing operations
                        should be used (often for debugging purposes).
                        Defaults to False
        """
        # Fast Meter Peak Demand
        self._read_clean_prompt()
        self.conn.write( self.fopcommandinfo + commands.CR )
        self.fastOpDef = protoparser.FastOpConfigurationBlock(
            self._read_to_prompt(), verbose=verbose
        )

    # Define Method to Perform Fast Meter Polling
    def poll_fast_meter(self, minAccLevel=0, verbose=False, **kwargs):
        """
        `poll_fast_meter` Method

        Method to poll the connected relay with the configured protocol
        settings (use `autoconfig` method to configure protocol settings).

        See Also
        --------
        autoconfig                      : Relay Auto Configuration

        Parameters
        ----------
        minAccLevel:    int, optional
                        Control to specify whether a minimum access level must
                        be obtained before polling should be performed.
        verbose:        bool, optional
                        Control to dictate whether verbose printing operations
                        should be used (often for debugging purposes).
                        Defaults to False
        """
        # Verify that Configuration is Valid
        if self.fastMeterDef is None:
            # TODO: Add Custom Exception to be More Explicit
            raise ValueError("Client has not been auto-configured yet!")
        # Raise to Appropriate Access Level if Needed
        if minAccLevel == 1:
            self.access_level_1( **kwargs )
        if minAccLevel == 2:
            self.access_level_2( **kwargs )
        # Poll Client for Data
        self._read_clean_prompt()
        self.conn.write( self.fmcommand1 + commands.CR )
        response = protoparser.FastMeterBlock(
            self._read_command_response(
                self.fmcommand1
            ),
            self.fastMeterDef,
            self.dnaDef,
            verbose=verbose
        )
        # Return the Response
        return response

    # Define Method to Send Fast Operate Command for Breaker Bit
    def send_breaker_bit_fast_op(self, control_point, command='trip'):
        """

        """

    # Define Method to Send Fast Operate Command for Remote Bit
    def send_remote_bit_fast_op(self, control_point, command='pulse'):
        """

        """
        # Write the Command
        command_str = commands.prepare_fastop_command(
            control_type='remote_bit', control_point=control_point,
            command=command, fastop_def=self.fastOpDef
        )
        print(command_str)
        self.conn.write( command_str )


# Define Builtin Test Mechanism
if __name__ == '__main__':
    import logging
    logging.basicConfig(filename='traffic.log', level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    print('Establishing Connection...')
    with telnetlib.Telnet('192.168.254.10', 2323) as tn:
        print('Initializing Client...')
        poller = SelClient( tn, logger=logger, verbose=True, debug=True )
        print( poller.fastOpDef )
        poller.send_remote_bit_fast_op('RB1', 'pulse')
        d = None
        for _ in range(10):
            d = poller.poll_fast_meter()  # verbose=True)
            for name, value in d['analogs'].items():
                print(name, value)
            time.sleep(1)
        poller.send_remote_bit_fast_op('RB1', 'pulse')


# END
