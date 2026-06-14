"""
NeevDB - A lightweight file-based database engine.
Built with pure Python, zero dependencies.

v3.0.3 — Clean release with optional server support.

Usage:
    from neevdb import NeevDB
    db = NeevDB("mydata.json")

Server (optional):
    pip install neevdb[server]
    from neevdb.server import start
    start()
"""

from .core import NeevDB

__version__ = "3.0.3"
__author__  = "Manish Dange"
__all__     = ["NeevDB"]