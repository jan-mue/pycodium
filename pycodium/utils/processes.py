"""Utility functions for managing processes."""

import contextlib
import time

import psutil

from pycodium.main import logger


def wait_for_port(port: int, timeout: int = 5) -> None:
    """Wait for a specific port to become available."""
    logger.info(f"Waiting for port {port} to become available...")
    start_time = time.time()
    while True:
        if get_process_on_port(port) is not None:
            logger.info(f"Port {port} is now available.")
            return
        if time.time() - start_time > timeout:
            raise TimeoutError(f"Port {port} did not become available within {timeout} seconds.")
        time.sleep(0.1)


def get_process_on_port(port: int) -> psutil.Process | None:
    """Get the process on the given port."""
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            conns = proc.net_connections(kind="inet")
            for conn in conns:
                if conn.laddr.port == port:
                    return proc
    return None


def terminate_or_kill_process_on_port(port: int, timeout: int = 1) -> None:
    """Terminate or kill the process running on a specific port."""
    proc = get_process_on_port(port)
    if proc is None:
        logger.warning(f"No process found on port {port}.")
        return
    proc.terminate()  # Send SIGTERM (terminate)
    try:
        proc.wait(timeout=timeout)
    except psutil.TimeoutExpired:
        logger.warning(f"Process {proc.pid} on port {port} did not terminate in time, sending SIGKILL.")
        proc.kill()  # If still alive, send SIGKILL (kill)
        proc.wait()  # Wait for process to actually terminate
