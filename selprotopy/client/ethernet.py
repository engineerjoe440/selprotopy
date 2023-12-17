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

from selprotopy.client.base import SELClient

__all__ = ["TCPSELClient"]

class TCPSELClient(SELClient):
    """
    `SelClient` Class for Polling an SEL Relay/Intelligent Electronic Device.

    The basic polling class intended to interact with an SEL relay which has
    already been connected to by way of a TCP socket connection.

    Parameters
    ----------
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

    def __init__(
        self,
        **kwargs
    ):
        """Connect over Serial to the SEL Protocol Device."""
        # Establish a TCP Connection
        connection=None # TODO
        # Attach Super Object
        super().__init__(connApi=connection, **kwargs)
