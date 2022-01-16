"""
selprotopy: A Protocol Binding Suite for the SEL Protocol Suite.

Supports:
  - SEL Fast Meter
  - SEL Fast Message
  - SEL Fast Operate

To use `telnetlib_support`, without importing `selprotopy` directly, use:

```
telnetlib.Telnet.process_rawq = process_rawq
```
"""

# Socket Support: We need to read without blocking forever!
import socket

def socket_read(sock: socket.socket):
    """Read from the socket without blocking indefinitely."""
    data = b''
    oldata = b''
    timeout = sock.gettimeout()
    sock.settimeout(0.1)
    while True:
        try:
            try:
                # Unix Systems
                data += sock.recv(1024, socket.MSG_DONTWAIT)
            except AttributeError:
                # Windows
                data += sock.recv(1024)
            if data == oldata:
                break
        except socket.timeout:
            break
        oldata = data
    # Finished Collecting
    sock.settimeout(timeout)
    return data