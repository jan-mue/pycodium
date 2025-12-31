"""Integration tests for the PyCodium Tauri application using Selenium WebDriver.

These tests verify that the application can be started and tested with WebDriver.
Note: tauri-driver must be installed via `cargo install tauri-driver --locked`
"""

from __future__ import annotations

import contextlib
import logging
import re
import subprocess
import time
import urllib.request
from typing import TYPE_CHECKING

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

if TYPE_CHECKING:
    from collections.abc import Generator

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def tauri_driver_process() -> Generator[subprocess.Popen[bytes] | None, None, None]:
    """Start tauri-driver process for WebDriver tests.

    Yields:
        The tauri-driver subprocess, or None if not available.
    """
    # Check if tauri-driver is installed
    try:
        subprocess.run(["tauri-driver", "--version"], check=True, capture_output=True, timeout=5)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pytest.skip("tauri-driver is not installed. Install with: cargo install tauri-driver --locked")
        yield None
        return

    # Start tauri-driver
    logger.info("Starting tauri-driver...")
    process = subprocess.Popen(
        ["tauri-driver"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for tauri-driver to start
    time.sleep(2)

    # Check if process is still running
    if process.poll() is not None:
        pytest.skip("tauri-driver failed to start")
        yield None
        return

    yield process

    # Cleanup: stop tauri-driver
    logger.info("Stopping tauri-driver...")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


@pytest.fixture(scope="module")
def app_process() -> Generator[subprocess.Popen[bytes] | None, None, None]:
    """Start the PyCodium application.

    Yields:
        The application subprocess, or None if it fails to start.
    """
    logger.info("Starting PyCodium application...")

    # Start the application using the pycodium command
    process = subprocess.Popen(
        ["uv", "run", "pycodium"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for the application to start
    # The app needs time to start the backend and open the window
    time.sleep(10)

    # Check if process is still running
    if process.poll() is not None:
        pytest.skip("PyCodium application failed to start")
        yield None
        return

    yield process

    # Cleanup: stop the application
    logger.info("Stopping PyCodium application...")
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


@pytest.mark.integration
def test_webdriver_connection(tauri_driver_process: subprocess.Popen[bytes] | None) -> None:
    """Test that tauri-driver is running and accessible.

    Args:
        tauri_driver_process: The running tauri-driver process.
    """
    if tauri_driver_process is None:
        pytest.skip("tauri-driver not available")

    # Verify tauri-driver is still running
    assert tauri_driver_process.poll() is None, "tauri-driver process is not running"

    # Try to connect to the WebDriver endpoint
    try:
        response = urllib.request.urlopen("http://127.0.0.1:4444/status", timeout=5)
        assert response.status == 200, "WebDriver endpoint not responding correctly"
    except OSError as e:
        pytest.fail(f"Failed to connect to WebDriver endpoint: {e}")


@pytest.mark.integration
def test_app_starts_and_frontend_loads(
    tauri_driver_process: subprocess.Popen[bytes] | None,
    app_process: subprocess.Popen[bytes] | None,
) -> None:
    """Test that the application starts and the frontend loads.

    Args:
        tauri_driver_process: The running tauri-driver process.
        app_process: The running application process.
    """
    if tauri_driver_process is None:
        pytest.skip("tauri-driver not available")

    if app_process is None:
        pytest.skip("Application failed to start")

    # Verify processes are running
    assert tauri_driver_process.poll() is None, "tauri-driver process died"
    assert app_process.poll() is None, "Application process died"

    # Connect with WebDriver
    driver = None
    try:
        # Configure capabilities for Tauri
        options = webdriver.ChromeOptions()
        capabilities = {
            "browserName": "wry",
        }

        driver = webdriver.Remote(
            command_executor="http://127.0.0.1:4444",
            options=options,
        )
        driver.capabilities.update(capabilities)

        # Wait for the frontend to load
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except WebDriverException as e:
            pytest.fail(f"Frontend did not load: {e}")

        # Verify body element exists and has content
        body = driver.find_element(By.TAG_NAME, "body")
        assert body is not None, "Body element not found"

        # Check that the UI has loaded (there should be div elements)
        divs = driver.find_elements(By.TAG_NAME, "div")
        assert len(divs) > 0, "No div elements found - UI may not have loaded"

    except WebDriverException as e:
        pytest.fail(f"Failed to connect to application via WebDriver: {e}")

    finally:
        if driver:
            with contextlib.suppress(WebDriverException):
                driver.quit()


@pytest.mark.integration
def test_dark_theme_applied(
    tauri_driver_process: subprocess.Popen[bytes] | None,
    app_process: subprocess.Popen[bytes] | None,
) -> None:
    """Test that the dark theme is applied.

    Args:
        tauri_driver_process: The running tauri-driver process.
        app_process: The running application process.
    """
    if tauri_driver_process is None:
        pytest.skip("tauri-driver not available")

    if app_process is None:
        pytest.skip("Application failed to start")

    driver = None
    try:
        options = webdriver.ChromeOptions()
        capabilities = {"browserName": "wry"}

        driver = webdriver.Remote(
            command_executor="http://127.0.0.1:4444",
            options=options,
        )
        driver.capabilities.update(capabilities)

        # Wait for body to load
        body = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Get the background color
        bg_color = body.value_of_css_property("background-color")

        # Check that it's a dark color
        if bg_color and bg_color.startswith("rgb"):
            rgb_match = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", bg_color)
            if rgb_match:
                r, g, b = map(int, rgb_match.groups())
                # Calculate luminance
                luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
                assert luma < 100, f"Background is too bright for dark theme (luma: {luma})"

    except WebDriverException as e:
        pytest.fail(f"Failed to test dark theme: {e}")

    finally:
        if driver:
            with contextlib.suppress(WebDriverException):
                driver.quit()
