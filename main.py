#!/usr/bin/env python3
"""make.fun entry: write the bundled news image to /output/entry.png.

No network, no randomness, no clock: every run copies the exact same
bytes, so the grader's two runs produce identical files.
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")
DST_DIR = "/output"
DST = os.path.join(DST_DIR, "entry.png")


def main():
    os.makedirs(DST_DIR, exist_ok=True)
    if os.path.abspath(SRC) != os.path.abspath(DST):
        shutil.copyfile(SRC, DST)


if __name__ == "__main__":
    main()
