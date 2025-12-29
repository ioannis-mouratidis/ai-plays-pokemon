"""
HTTP client for mGBA-http API v0.8.1
Provides wrapper functions for emulator control
"""

import requests
import base64
import time
import os
import tempfile
from typing import Optional, Dict, Any, List
from io import BytesIO
from PIL import Image


class MGBAClient:
    """Client for communicating with mGBA-http REST API v0.8.1"""

    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()

    def is_connected(self) -> bool:
        """Check if mGBA-http is running and connected"""
        try:
            # Try to get current frame - simple test
            response = self.session.get(f"{self.base_url}/Core/CurrentFrame", timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def get_game_info(self) -> Dict[str, Any]:
        """Get current game information"""
        response = self.session.get(f"{self.base_url}/Core/GetGameCode")
        response.raise_for_status()
        return {"game_code": response.text}

    def press_button(self, button: str, frames: int = 1) -> bool:
        """
        Press a button (tap it briefly)

        Args:
            button: Button name (A, B, Start, Select, L, R, Up, Down, Left, Right)
            frames: Number of frames to hold (default 1)

        Returns:
            True if successful
        """
        # Use the tap endpoint for brief presses
        response = self.session.post(
            f"{self.base_url}/Mgba-Http/Button/Tap",
            params={"button": button.capitalize()}
        )
        response.raise_for_status()

        # If need to hold longer
        if frames > 1:
            time.sleep(frames * 0.0167)  # ~60 FPS = 16.7ms per frame

        return True

    def press_buttons_sequence(self, buttons: List[str], delay_frames: int = 5) -> bool:
        """
        Press a sequence of buttons with delays

        Args:
            buttons: List of button names
            delay_frames: Frames to wait between presses

        Returns:
            True if successful
        """
        for button in buttons:
            self.press_button(button, frames=1)
            time.sleep(delay_frames * 0.0167)
        return True

    def read_memory(self, address: int, size: int) -> bytes:
        """
        Read memory from emulator

        Args:
            address: Memory address (integer, e.g., 0x02024284)
            size: Number of bytes to read

        Returns:
            Bytes object containing memory data
        """
        # Use readrange endpoint to read multiple bytes
        result = []

        # Read byte by byte (v0.8.1 API)
        for offset in range(size):
            addr = address + offset
            response = self.session.get(
                f"{self.base_url}/Core/Read8",
                params={"address": addr}
            )
            response.raise_for_status()

            # Response is plain text number
            byte_value = int(response.text.strip())
            result.append(byte_value)

        return bytes(result)

    def get_screenshot(self) -> Image.Image:
        """
        Capture current screen as PIL Image

        Uses mGBA screenshot API with path parameter to save screenshot,
        then reads it back from disk.

        Returns:
            PIL Image object (240x160 for GBA)
        """
        from urllib.parse import quote

        # Determine screenshot save directory (main project directory)
        mcp_server_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(mcp_server_dir)
        screenshot_dir = os.path.join(project_root, "screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)

        # Create unique filename with timestamp
        import time as time_module
        timestamp = int(time_module.time() * 1000)
        screenshot_filename = f"mgba_screenshot_{timestamp}.png"
        screenshot_path = os.path.join(screenshot_dir, screenshot_filename)

        # URL encode the path for the API call
        # mGBA screenshot API expects: POST /core/screenshot?path=<url_encoded_path>
        encoded_path = quote(screenshot_path, safe='')

        # Call mGBA screenshot endpoint with path parameter
        response = self.session.post(
            f"{self.base_url}/core/screenshot",
            params={"path": screenshot_path}  # requests will URL encode this
        )
        response.raise_for_status()

        # Wait a moment for file to be written
        time.sleep(0.3)

        # Check if file was created
        if not os.path.exists(screenshot_path):
            raise RuntimeError(
                f"Screenshot file was not created at: {screenshot_path}\n"
                f"mGBA screenshot endpoint returned: {response.text}"
            )

        # Read and return the image
        try:
            img = Image.open(screenshot_path)
            return img
        except Exception as e:
            raise RuntimeError(f"Failed to read screenshot file: {e}")


    def read_byte(self, address: int) -> int:
        """Read single byte from memory"""
        response = self.session.get(
            f"{self.base_url}/Core/Read8",
            params={"address": address}
        )
        response.raise_for_status()
        return int(response.text.strip())

    def read_word(self, address: int) -> int:
        """Read 2-byte word from memory (little-endian)"""
        data = self.read_memory(address, 2)
        return int.from_bytes(data, byteorder='little')

    def read_dword(self, address: int) -> int:
        """Read 4-byte double word from memory (little-endian)"""
        data = self.read_memory(address, 4)
        return int.from_bytes(data, byteorder='little')


# Convenience function for creating client
def create_client(base_url: str = "http://localhost:5000") -> MGBAClient:
    """
    Create and test mGBA client connection

    Args:
        base_url: URL to mGBA-http server

    Returns:
        MGBAClient instance

    Raises:
        ConnectionError: If unable to connect to mGBA-http
    """
    client = MGBAClient(base_url)

    if not client.is_connected():
        raise ConnectionError(
            f"Unable to connect to mGBA-http at {base_url}. "
            "Ensure mGBA is running with Lua script loaded and mGBA-http is started."
        )

    return client
