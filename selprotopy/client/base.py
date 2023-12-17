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
import time
import logging

# Local Imports
from selprotopy.common import (
    retry, INVALID_COMMAND_STR, RemoteBitControlType, BreakerBitControlType
)
from selprotopy import exceptions
from selprotopy.protocol import commands, parser
from selprotopy.support import socket


# Define Simple Polling Client
class SelClient():
    """
    `SelClient` Class for Polling an SEL Relay/Intelligent Electronic Device.

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
                        should normally be set to True to allow auto-config.
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

    def __init__(self, connApi, logger: logging.Logger = None,
                 verbose: bool = False, debug: bool = False, **kwargs):
        """Prepare SELClient."""
        # Initialize Inputs
        self.conn = connApi
        self.verbose = verbose
        self.logger = logger
        self.debug = debug

        # Initialize Class Options
        self.timeout = 60
        self.__num_con_check__ = 5
        self.__inter_cmd_delay__ = 0.025

        # Initialize Additional Options that May be Made Available
        kwarg_keys = kwargs.keys()
        if 'timeout' in kwarg_keys:
            self.timeout = kwargs['timeout']
        if 'conn_check' in kwarg_keys:
            self.__num_con_check__ = kwargs['conn_check']
        if 'cmd_delay' in kwarg_keys:
            self.__inter_cmd_delay__ = kwargs['cmd_delay']

        # Define Basic Parameter Defaults
        self.fid     = ''
        self.bfid    = ''
        self.cid     = ''
        self.devid   = ''
        self.partno  = ''
        self.config  = ''

        # Define Parameters to Indicate Whether Specific Commands are Supported
        self.fast_meter_supported = False
        self.fast_meter_demand_supported = False
        self.fast_meter_peak_demand_supported = False
        self.fast_operate_supported = False

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

        if hasattr(self.conn, 'settimeout'):
            self.conn.settimeout(self.timeout)

        # Verify Connection by Searching for Prompt
        if 'noverify' not in kwarg_keys:
            if verbose:
                print('Verifying Connection...')
            if not self._verify_connection():
                raise exceptions.ConnVerificationFail("Verification Failed.")
            if verbose:
                print('Connection Verified.')
        self.quit()
        if 'autoconfig' in kwargs:
            # Run Auto-Configuration
            if not isinstance(kwargs['autoconfig'], bool):
                self.autoconfig(verbose=verbose)
            elif bool(kwargs['autoconfig']):
                self.autoconfig(verbose=verbose)

    # Define Connectivity Check Method
    def _verify_connection(self):
        # Set Default Indication
        connected = False
        # Iteratively attempt to see relay's response
        for _ in range(self.__num_con_check__):
            self._write( commands.CR + commands.CR + commands.CR )
            if hasattr(self.conn, "read_until"):
                response = self.conn.read_until( commands.CR )
            elif hasattr(self.conn, 'socket_read'):
                response = socket.socket_read(self.conn)
            else:
                # pySerial Method
                response = self.conn.read_until( commands.CR )
            if self.debug:
                print(response)
            if commands.LEVEL_0 in response:
                # Relay Responded
                connected = True
                break
            time.sleep( self.__inter_cmd_delay__ )
        # Return Status
        return connected

    # Define Method to Handle Eager Reading Between Connection Methods
    def _read_eager(self):
        # Switch on Connection Type
        if hasattr(self.conn, "read_until"):
            return self.conn.read_very_eager()
        elif hasattr(self.conn, 'socket_read'):
            return socket.socket_read(self.conn)
        # pySerial
        return self.conn.read_very_eager()

    # Define Method to "Clear" the Buffer
    def _clear_input_buffer(self):
        try:
            resp = self._read_eager()
            if self.logger:
                self.logger.info(f'Rx: {resp}')
            if self.debug:
                print('Clearing buffer:', resp)
            while b'' != resp:
                time.sleep(self.__inter_cmd_delay__ * 10)
                resp = self._read_eager()
                if self.logger:
                    self.logger.info(f'Rx: {resp}')
                if self.debug:
                    print('Clearing buffer:', resp)
        except Exception:
            # pySerial Method
            self.conn.reset_input_buffer()

    # Define Method to Handle Writing for telnetlib-vs-socket
    def _write(self, data):
        # Switch on Writing Mechanism
        if hasattr(self.conn, "read_until"):
            self.conn.write(data)
        elif hasattr(self.conn, 'sendall'):
            self.conn.sendall(data)
        else:
            # pySerial
            self.conn.write(data)

    # Define Method to Read All Data to Next Relay Prompt
    def _read_to_prompt(self, prompt_str=commands.PROMPT):
        # Telnetlib Supports a Timeout
        if hasattr(self.conn, "read_until"):
            response = self.conn.read_until(prompt_str, timeout=self.timeout)
        elif hasattr(self.conn, 'socket_read'):
            response = socket.socket_read(self.conn)
        # PySerial Does not Support Timeout
        else:
            response = self.conn.read_until(prompt_str)
        if self.logger:
            self.logger.debug(f'Rx: {response}')
        if self.debug:
            print(response)
        return response

    # Define Method to Read All Data After a Command (and to next relay prompt)
    def _read_command_response(self, command, prompt_str=commands.PROMPT):
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
            # Check for Invalid Command Response from Relay
            if INVALID_COMMAND_STR in response:
                raise exceptions.InvalidCommand(
                    f"Relay Reports Invalid Command: '{response}'"
                )
        return response

    # Define Method to Read Until a "Clean" Prompt is Viewed
    def _read_clean_prompt(self):
        """
        Strategy:

        Continue to send <CR><LF> until the counted "clean" responses reaches 3
        or more.
        """
        count = 0
        response = b''
        while count < 3:
            self._write( commands.CR )      # Write
            response += self._read_to_prompt()   # Read
            if self.debug:
                print('Clean prompt response:', response)
            # Count the Number of Clean Prompt Responses
            if parser.clean_prompt(response):
                count += 1
            else:
                count = 0
            time.sleep(self.__inter_cmd_delay__)
        self._clear_input_buffer()  # Empty anything left in the buffer
        time.sleep(self.__inter_cmd_delay__)

    # Define Method to Attempt Reading Everything (only for telnetlib)
    def _read_everything(self):
        response = self._read_eager()
        if self.logger:
            self.logger.info(f'Rx: {response}')
        if self.debug:
            print(response)
        return response

    # Define Method to Identify Current Access Level
    def access_level(self):
        """
        Identify Current Access Level.

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
        self._write( commands.CR )
        resp = self._read_to_prompt()
        self._write( commands.CR )
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
        Quit Method.

        Simple method to send the QUIT command to an
        actively connected relay.

        See Also
        --------
        access_level_1      : Elevate permission to ACC
        access_level_2      : Elevate permission to 2AC
        """
        self._write( commands.QUIT )
        self._read_to_prompt( commands.LEVEL_0 )
        self._read_clean_prompt()

    # Define Method to Access Level 1
    def access_level_1(self, level_1_pass: str = commands.PASS_ACC, **kwargs):
        """
        Go to Access Level 1.

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
        time.sleep(self.__inter_cmd_delay__)
        level, _ = self.access_level()
        if self.debug:
            print("Logging in to ACC")
        self._write( commands.GO_ACC )
        # Provide Password
        if level == 0:
            time.sleep( int(self.__inter_cmd_delay__ * 3) )
            self._write( level_1_pass + commands.CR )
            time.sleep( self.__inter_cmd_delay__ )
        resp = self._read_to_prompt( commands.LEVEL_0 )
        if b'Invalid' in resp:
            if self.debug:
                print("Log-In Failed")
            return False
        else:
            if self.debug:
                print("Log-In Succeeded")
            return True

    # Define Method to Access Level 2
    def access_level_2(self, level_2_pass: str = commands.PASS_2AC, **kwargs):
        """
        Go To Access Level 2.

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
        level, _ = self.access_level()
        # Provide Password
        if level == 0:
            if not self.access_level_1( **kwargs ):
                return False
        if self.debug:
            print("Logging in to 2AC")
        self._write( commands.GO_2AC )
        if level in [0, 1]:
            time.sleep( int(self.__inter_cmd_delay__ * 3) )
            self._write( level_2_pass + commands.CR )
            time.sleep( self.__inter_cmd_delay__ )
        resp = self._read_to_prompt( commands.LEVEL_0 )
        if b'Invalid' in resp:
            if self.debug:
                print("Log-In Failed")
            return False
        else:
            if self.debug:
                print("Log-In Succeeded")
            return True

    # Define Method to Perform Auto-Configuration Process
    def autoconfig( self, attempts: int = 0, verbose: bool = False, **kwargs ):
        """
        Auto-Configure SELClient Instance.

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
        autoconfig_relay_definition     : Auto Configuration for Relay
                                            Definition Block

        Parameters
        ----------
        attempts:       int, optional
                        Number of auto-configuration attempts, setting to `0`
                        will allow for repeated auto-configuration until all
                        stages succeed. Defaults to 0
        verbose:        bool, optional
                        Control to dictate whether verbose printing operations
                        should be used (often for debugging and learning
                        purposes). Defaults to False
        """
        self.quit()
        # Determine Command Strings and Relay Information
        self.autoconfig_relay_definition(attempts=attempts, verbose=self.debug)
        if self.fast_meter_supported:
            self.autoconfig_fastmeter( verbose=self.debug )
        if self.fast_meter_demand_supported:
            self.autoconfig_fastmeter_demand( verbose=self.debug )
        if self.fast_meter_peak_demand_supported:
            self.autoconfig_fastmeter_peakdemand( verbose=self.debug )
        if self.fast_operate_supported:
            self.autoconfig_fastoperate( verbose=self.debug )
        # Determine if Level 0, and Escalate Accordingly
        if self.access_level()[0] == 0:
            # Access Level 1 Required to Request DNA
            self.access_level_1( **kwargs )
        # Request Relay ENA Block
        # TODO
        # Request Relay DNA Block
        self._read_clean_prompt()
        if verbose:
            print("Reading Relay DNA Block...")
        self._write( commands.DNA )
        self.dnaDef = parser.relay_dna_block(
            self._read_command_response(commands.DNA),
            encoding='utf-8',
            verbose=self.debug
        )
        # Request Relay BNA Block
        # TODO
        # Request Relay ID Block
        if verbose:
            print("Reading Relay ID Block...")
        self._write( commands.ID )
        id_block = parser.relay_id_block(
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

    # Define Method to Pack the Config Messages
    @retry(fail_msg="Relay Definition Parsing Failed.")
    def autoconfig_relay_definition(self, attempts: int = 0,
        verbose: bool = False):
        """
        Autoconfigure SEL Client for Relay Definition Block.

        Method to operate the standard auto-configuration process
        with a connected relay to identify the standard messages required to
        interact with the device and poll specific datasets.

        See Also
        --------
        autoconfig                      : Relay Auto Configuration
        autoconfig_fastmeter_demand     : Auto Config for Fast Meter Demand
        autoconfig_fastmeter_peakdemand : Auto Config for Fast Meter Pk Demand
        autoconfig_fastoperate          : Auto Config for Fast Operate

        Parameters
        ----------
        attempts:       int, optional
                        Number of auto-configuration attempts, setting to `0`
                        will allow for repeated auto-configuration until all
                        stages succeed. Defaults to 0
        verbose:        bool, optional
                        Control to dictate whether verbose printing operations
                        should be used (often for debugging purposes).
                        Defaults to False
        """
        # Request Relay Definition
        if verbose:
            print("Reading Relay Definition Block...")
        verbose = verbose or self.debug
        self._write(commands.RELAY_DEFINITION + commands.CR )
        definition = parser.relay_definition_block(
            self._read_command_response(commands.RELAY_DEFINITION),
            verbose=verbose
        )
        # Load the Relay Definition Information and Request the Meter Blocks
        if definition['fmmessagesup'] >= 1:
            if verbose:
                print("Reading Fast Meter Definition Block...")
            self.fmconfigcommand1   = \
                definition['fmcommandinfo'][0]['configcommand']
            self.fmcommand1         = \
                definition['fmcommandinfo'][0]['command']
            self.fast_meter_supported = True
        if definition['fmmessagesup'] >= 2:
            if verbose:
                print("Reading Fast Meter Demand Definition Block...")
            self.fmconfigcommand2   = \
                definition['fmcommandinfo'][1]['configcommand']
            self.fmcommand2         = \
                definition['fmcommandinfo'][1]['command']
            self.fast_meter_demand_supported = True
        if definition['fmmessagesup'] >= 3:
            if verbose:
                print("Reading Fast Meter Peak Demand Definition Block...")
            self.fmconfigcommand3   = \
                definition['fmcommandinfo'][2]['configcommand']
            self.fmcommand3         = \
                definition['fmcommandinfo'][2]['command']
            self.fast_meter_peak_demand_supported = True
        # Interpret the Fast Operate Information if Present
        if definition['fopcommandinfo'] != '':
            if verbose:
                print("Reading Fast Operate Definition Block...")
            self.fopcommandinfo     = definition['fopcommandinfo']
            self.fast_operate_supported = True
        # Interpret the Fast Message Information if Present
        if definition['fmsgcommandinfo'] != '':
            if verbose:
                print("Reading Fast Message Definition Block...")
            self.fmsgcommandinfo    = definition['fmsgcommandinfo']


    # Define Method to Run the Fast Meter Configuration
    @retry(fail_msg="Fast Meter Autoconfig Failed.")
    def autoconfig_fastmeter(self, attempts: int = 0, verbose: bool = False):
        """
        Autoconfigure Fast Meter for SEL Client.

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
        attempts:       int, optional
                        Number of auto-configuration attempts, setting to `0`
                        will allow for repeated auto-configuration until all
                        stages succeed. Defaults to 0
        verbose:        bool, optional
                        Control to dictate whether verbose printing operations
                        should be used (often for debugging purposes).
                        Defaults to False
        """
        # Fast Meter
        self._read_clean_prompt()
        self._write( self.fmconfigcommand1 + commands.CR )
        self.fastMeterDef = parser.fast_meter_configuration_block(
            self._read_to_prompt(),
            verbose=verbose,
        )

    # Define Method to Run the Fast Meter Demand Configuration
    @retry(fail_msg="Fast Meter Demand Autoconfig Failed.")
    def autoconfig_fastmeter_demand(self, attempts: int = 0,
        verbose: bool = False):
        """
        Autoconfigure Fast Meter Demand for SEL Client.

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
        attempts:       int, optional
                        Number of auto-configuration attempts, setting to `0`
                        will allow for repeated auto-configuration until all
                        stages succeed. Defaults to 0
        verbose:        bool, optional
                        Control to dictate whether verbose printing operations
                        should be used (often for debugging purposes).
                        Defaults to False
        """
        # Fast Meter Demand
        self._read_clean_prompt()
        self._write( self.fmconfigcommand2 + commands.CR )
        self.fastDemandDef = parser.fast_meter_configuration_block(
            self._read_to_prompt(),
            verbose=verbose,
        )

    # Define Method to Run the Fast Meter Peak Demand Configuration
    @retry(fail_msg="Fast Meter Peak Demand Autoconfig Failed.")
    def autoconfig_fastmeter_peakdemand(self, attempts: int = 0,
        verbose: bool = False):
        """
        Autoconfigure Fast Meter Peak Demand for SEL Client.

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
        attempts:       int, optional
                        Number of auto-configuration attempts, setting to `0`
                        will allow for repeated auto-configuration until all
                        stages succeed. Defaults to 0
        verbose:        bool, optional
                        Control to dictate whether verbose printing operations
                        should be used (often for debugging purposes).
                        Defaults to False
        """
        # Fast Meter Peak Demand
        self._read_clean_prompt()
        self._write( self.fmconfigcommand3 + commands.CR )
        self.fastPkDemandDef = parser.fast_meter_configuration_block(
            self._read_to_prompt(),
            verbose=verbose,
        )

    # Define Method to Run the Fast Operate Configuration
    @retry(fail_msg="Fast Operate Autoconfig Failed.")
    def autoconfig_fastoperate(self, attempts: int = 0, verbose: bool = False):
        """
        Autoconfigure Fast Operate for SEL Client.

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
        attempts:       int, optional
                        Number of auto-configuration attempts, setting to `0`
                        will allow for repeated auto-configuration until all
                        stages succeed. Defaults to 0
        verbose:        bool, optional
                        Control to dictate whether verbose printing operations
                        should be used (often for debugging purposes).
                        Defaults to False
        """
        # Fast Meter Peak Demand
        self._read_clean_prompt()
        self._write( self.fopcommandinfo + commands.CR )
        self.fastOpDef = parser.fast_op_configuration_block(
            self._read_to_prompt(),
            verbose=verbose,
        )

    # Define Method to Perform Fast Meter Polling
    def poll_fast_meter(self, minAccLevel: bool = 0, verbose: bool = False,
                        **kwargs):
        """
        Poll Fast Meter Data from SEL Relay/IED.

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
        self._write( self.fmcommand1 + commands.CR )
        response = parser.fast_meter_block(
            self._read_command_response(
                self.fmcommand1
            ),
            self.fastMeterDef,
            self.dnaDef,
            verbose=verbose,
        )
        # Return the Response
        return response

    # Define Method to Send Fast Operate Command for Breaker Bit
    def send_breaker_bit_fast_op(
        self,
        control_point: str,
        command: BreakerBitControlType = BreakerBitControlType.TRIP
    ):
        """
        Send a Fast Operate Breaker Bit Control.

        Send a breaker bit using the Fast Operate protocol by describing
        the control point and the control type.

        See Also
        --------
        send_remote_bit_fast_op         : Send Remote Bit Control

        Parameters
        ----------
        control_point:  str
                        Particular Remote Bit point which should be
                        controlled, should be of format 'RBxx' where
                        'xx' represents the remote bit number.
        command:        BreakerBitControlType, optional
                        Command type which will be sent, must be of:
                        ['TRIP', 'CLOSE'].
                        Defaults to 'trip'
        """
        # Write the Command
        command_str = commands.prepare_fastop_command(
            control_type='breaker_bit', control_point=control_point,
            command=command, fastop_def=self.fastOpDef
        )
        if self.verbose:
            print(command_str)
        self._write( command_str )

    # Define Method to Send Fast Operate Command for Remote Bit
    def send_remote_bit_fast_op(
        self,
        control_point: str,
        command: RemoteBitControlType = RemoteBitControlType.PULSE
    ):
        """
        Send a Fast Operate Remote Bit Control.

        Send a remote bit using the Fast Operate protocol by describing
        the control point and the control type.

        See Also
        --------
        send_breaker_bit_fast_op        : Send Breaker Bit Control

        Parameters
        ----------
        control_point:  str
                        Particular Remote Bit point which should be
                        controlled, should be of format 'RBxx' where
                        'xx' represents the remote bit number.
        command:        RemoteBitControlType, optional
                        Command type which will be sent, must be of:
                        ['SET', 'CLEAR', 'PULSE', 'OPEN', 'CLOSE'].
                        Defaults to 'pulse'
        """
        # Write the Command
        command_str = commands.prepare_fastop_command(
            control_type='remote_bit', control_point=control_point,
            command=command, fastop_def=self.fastOpDef
        )
        if self.verbose:
            print(command_str)
        self._write( command_str )


# Define Builtin Test Mechanism
if __name__ == '__main__':
    logging.basicConfig(filename='traffic.log', level=logging.DEBUG)
    logger_obj = logging.getLogger(__name__)
    print('Establishing Connection...')
    # with telnetlib.Telnet('192.168.2.210', 23) as tn:
    #     print('Initializing Client...')
    #     poller = SelClient( tn, logger=logger_obj, verbose=True, debug=True, noverify=True )
    #     poller.autoconfig_relay_definition(verbose=True)
    #     poller.autoconfig(verbose=True)
    #     poller.send_remote_bit_fast_op('RB1', 'pulse')
    #     d = None
    #     for _ in range(10):
    #         d = poller.poll_fast_meter()  # verbose=True)
    #         for name, value in d['analogs'].items():
    #             print(name, value)
    #         time.sleep(1)
    #     poller.send_remote_bit_fast_op('RB1', 'pulse')
    sock = socket.create_connection(('192.168.2.210', 23))
    print('Initializing Client...')
    poller = SelClient( sock, logger=logger_obj, verbose=True, debug=True )
    poller.autoconfig_relay_definition(verbose=True)
    poller.autoconfig(verbose=True)


# END
