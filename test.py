
import telnetlib
import selprotopy

if __name__ == '__main__':
    print('Establishing Connection...')
    with telnetlib.Telnet('192.168.254.10', 23) as tn:
        print('Initializing Client...')
        poller = selprotopy.PollingClient( tn, verbose=True)