#!/usr/bin/env python3
"""Maze Donate — the official, PGP-verified Maze Linux donation addresses."""
import sys

if __name__ == "__main__":
    from mazedonate.gui.app import run
    sys.exit(run())
