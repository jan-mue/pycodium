"""Integration tests for the PyCodium Tauri application using Selenium WebDriver."""

from __future__ import annotations

import contextlib
import logging
import platform
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
def tauri_driver_process() -> Generator[subprocess.Popen[bytes], None, None]:
    """Start tauri-driver process for WebDriver tests."""
    if platform.system() == "Darwin":
        pytest.skip("tauri-driver is not supported on macOS")

    logger.info("Starting tauri-driver...")
    process = subprocess.Popen(["tauri-driver"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)

    if process.poll() is not None:
        stderr = process.stderr.read().decode() if process.stderr else ""
        pytest.fail(f"tauri-driver failed to start. stderr: {stderr}")

    yield process

    logger.info("Stopping tauri-driver...")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


@pytest.fixture(scope="module")
def app_process() -> Generator[subprocess.Popen[bytes], None, None]:
    """Start the PyCodium application."""
    logger.info("Starting PyCodium application...")
    process = subprocess.Popen(["uv", "run", "pycodium"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(10)

    if process.poll() is not None:
        stderr = process.stderr.read().decode() if process.stderr else ""
        stdout = process.stdout.read().decode() if process.stdout else ""
        pytest.fail(f"PyCodium application failed to start.\nstdout: {stdout}\nstderr: {stderr}")

    yield process

    logger.info("Stopping PyCodium application...")
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def test_webdriver_connection(tauri_driver_process: subprocess.Popen[bytes]) -> None:
    """Test that tauri-driver is running and accessible."""
    response = urllib.request.urlopen("http://127.0.0.1:4444/status", timeout=5)
    assert response.status == 200


def test_app_starts_and_frontend_loads(
    tauri_driver_process: subprocess.Popen[bytes],
    app_process: subprocess.Popen[bytes],
) -> None:
    """Test that the application starts and the frontend loads."""
    driver = None
    try:
        options = webdriver.ChromeOptions()
        capabilities = {"browserName": "wry"}

        driver = webdriver.Remote(command_executor="http://127.0.0.1:4444", options=options)
        driver.capabilities.update(capabilities)

        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        body = driver.find_element(By.TAG_NAME, "body")
        assert body is not None

        divs = driver.find_elements(By.TAG_NAME, "div")
        assert len(divs) > 0, "No div elements found - UI may not have loaded"
    finally:
        if driver:
            with contextlib.suppress(WebDriverException):
                driver.quit()


def test_dark_theme_applied(
    tauri_driver_process: subprocess.Popen[bytes], app_process: subprocess.Popen[bytes]
) -> None:
    """Test that the dark theme is applied."""
    driver = None
    try:
        options = webdriver.ChromeOptions()
        capabilities = {"browserName": "wry"}

        driver = webdriver.Remote(command_executor="http://127.0.0.1:4444", options=options)
        driver.capabilities.update(capabilities)

        body = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        bg_color = body.value_of_css_property("background-color")

        if bg_color and bg_color.startswith("rgb"):
            rgb_match = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", bg_color)
            if rgb_match:
                r, g, b = map(int, rgb_match.groups())
                luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
                assert luma < 100, f"Background is too bright for dark theme (luma: {luma})"

    finally:
        if driver:
            with contextlib.suppress(WebDriverException):
                driver.quit()
