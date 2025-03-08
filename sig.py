import signal
import sys


def sigint_handler(signum, frame):
    print("Received SIGINT (CTRL+C). Cleaning up...")
    # Perform any necessary cleanup here
    sys.exit(0)


signal.signal(signal.SIGINT, sigint_handler)

print("Server is running. Press CTRL+C to exit.")
# Simulate long-running server loop
while True:
    pass
