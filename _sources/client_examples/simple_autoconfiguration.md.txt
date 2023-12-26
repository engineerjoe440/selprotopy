# Performing Automatic Configuration with an SEL Relay

SEL Protocol operates in a self-describing manner wherein the relay or intelligent electronic
device provides a standard interface for binary messages to describe the layout of specific
data regions. This makes it possible for the relay to describe the methods in which a user may
query the device for data, send control operations, or otherwise interact with the relay.

SELProtoPy provides mechanisms for the client objects to negotiate the automatic configuration
process with a device to establish the devices capabilities.

## Autoconfiguration with a Serially-Connected Device

The following example assumes a Linux environment using a USB-to-serial adapter (thus the
`/dev/ttyUSB1`) in use.

```python
# Import the serial client object from SELProtoPy
from selprotopy.client import SerialSELClient

# Define the connection parameters
PORT = '/dev/ttyUSB1'
BAUD = 9600

# Establish the connection - this will NOT start the autoconfiguration
client = SerialSELClient(port=PORT, baudrate=BAUD)

# Start the Automatic Configuration process
client.autoconfigure()

# If no exceptions are raised, the configuration process has succeeded

# Poll the relay using fast-meter
client.poll_fast_meter()
```

## Autoconfiguration with a Ethernet-Connected Device

The following example uses a raw TCP socket connection (does not use `telnetlib`) to
establish a connection with the relay.

```python
# Import the TCP client object from SELProtoPy
from selprotopy.client import TCPSELClient

# Define the connection parameters
IP = '192.168.1.100'
TCP_PORT = 23

# Establish the connection - this will NOT start the autoconfiguration
client = TCPSELClient(ip_address=IP, port=TCP_PORT)

# Start the Automatic Configuration process
client.autoconfigure()

# If no exceptions are raised, the configuration process has succeeded

# Poll the relay using fast-meter
client.poll_fast_meter()
```