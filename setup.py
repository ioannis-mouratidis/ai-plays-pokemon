"""
Setup script for MCP Pokemon FireRed Battle Server
"""

from setuptools import setup, find_packages

setup(
    name="mcp_server",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "mcp>=0.5.0",
        "requests>=2.31.0",
        "anthropic>=0.18.0",
        "pillow>=10.0.0",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "mcp-pokemon-battle=mcp_server.server:main",
        ],
    },
)
