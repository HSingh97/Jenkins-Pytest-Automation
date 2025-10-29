#!/usr/bin/env python3
import sys
import os
import subprocess
import argparse
import time
import signal


def get_pid_file_path(port):
    """Generates a consistent PID file path based on the port name."""
    safe_port_name = os.path.basename(port)
    return f"/tmp/serial_log_{safe_port_name}.pid"


def kill_process_on_port(port):
    """Forcefully kills any process currently using the specified serial port."""
    print(f"--- Forcefully clearing port {port} ---", flush=True)
    subprocess.run(f"fuser -k {port} || true", shell=True, check=True)


def start_logger(port, logfile):

    pid_file = get_pid_file_path(port)

    kill_process_on_port(port)

    if os.path.exists(pid_file):
        print(f"Warning: Stale PID file found. Removing {pid_file}", flush=True)
        os.remove(pid_file)

    print(f"Starting logger on {port}, writing to {logfile}...", flush=True)

    command = [
        sys.executable,
        __file__,
        'internal_start_process',
        '--port', port,
        '--logfile', logfile
    ]


    process = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        preexec_fn=os.setpgrp
    )

    try:
        with open(pid_file, 'w') as f:
            f.write(str(process.pid))
        print(f"Success: Logger started with PID {process.pid}", flush=True)
        print(f"PID file: {pid_file}")
    except IOError as e:
        print(f"Error: Could not write PID file: {e}", flush=True)
        os.kill(process.pid, signal.SIGTERM)
        sys.exit(1)


def stop_logger(port):
    pid_file = get_pid_file_path(port)

    if not os.path.exists(pid_file):
        print(f"Error: Logger does not appear to be running (No PID file: {pid_file})", flush=True)
        kill_process_on_port(port)
        return

    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
    except IOError as e:
        print(f"Error: Could not read PID file: {e}", flush=True)
        sys.exit(1)
    except ValueError:
        print(f"Error: PID file contains invalid data.", flush=True)
        sys.exit(1)

    print(f"Stopping logger process with PID {pid} on port {port}...", flush=True)

    try:
        os.kill(pid, signal.SIGTERM)
        print("Process stopped.", flush=True)
    except ProcessLookupError:
        print("Process was already dead.", flush=True)
    except PermissionError:
        print("Permission denied to kill process. Try with sudo.", flush=True)

    os.remove(pid_file)


def serial_logger_process(port, logfile):

    try:
        import serial
    except ImportError:
        print("Error: 'pyserial' library not found. Please install it: pip install pyserial", flush=True)
        sys.exit(1)

    try:
        # Open the log file in append mode, with line buffering (1)
        with open(logfile, 'a', buffering=1) as log_f, \
                serial.Serial(port, 115200, timeout=1) as ser:

            # Write a startup message to the log
            log_f.write(f"\n--- Serial logging started at {time.asctime()} on {port} ---\n")

            while True:
                try:
                    # Read all available data
                    data = ser.read(ser.in_waiting or 1)
                    if data:
                        # Write raw bytes to file
                        log_f.write(data.decode('utf-8', errors='ignore'))
                except serial.SerialException as e:
                    log_f.write(f"\n--- Serial Error: {e}. Stopping log. ---\n")
                    break
                except IOError as e:
                    # e.g., disk full
                    print(f"Log file write error: {e}", flush=True)
                    break
    except serial.SerialException as e:
        print(f"Fatal: Could not open serial port {port}: {e}", flush=True)
        sys.exit(1)
    except IOError as e:
        print(f"Fatal: Could not open log file {logfile}: {e}", flush=True)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Serial Port Logging Manager")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Start command
    start_parser = subparsers.add_parser('start', help="Start a logger process")
    start_parser.add_argument('--port', required=True, help="Serial port (e.g., /dev/ttyUSB0)")
    start_parser.add_argument('--logfile', required=True, help="Log file path")

    # Stop command
    stop_parser = subparsers.add_parser('stop', help="Stop a logger process")
    stop_parser.add_argument('--port', required=True, help="Serial port (e.g., /dev/ttyUSB0)")

    # Internal command (hidden from help)
    internal_parser = subparsers.add_parser('internal_start_process', help=argparse.SUPPRESS)
    internal_parser.add_argument('--port', required=True)
    internal_parser.add_argument('--logfile', required=True)

    args = parser.parse_args()

    if args.command == 'start':
        start_logger(args.port, args.logfile)
    elif args.command == 'stop':
        stop_logger(args.port)
    elif args.command == 'internal_start_process':
        serial_logger_process(args.port, args.logfile)


if __name__ == "__main__":
    main()
