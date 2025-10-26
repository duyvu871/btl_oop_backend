#!/usr/bin/env python3
"""
Script to compress a file to gzip format.
Usage: python compress_resources_file.py <input_path> [--output <output_path>]
"""

import argparse
import gzip
import shutil
from pathlib import Path


def compress_file(input_path: str, output_path: str = None):
    """
    Compress a file to gzip format.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file {input_path} does not exist.")

    if output_path is None:
        output_path = str(input_file) + '.gz'
    else:
        output_path = output_path

    print(f"Compressing {input_path} to {output_path}...")
    with open(input_file, 'rb') as f_in:
        with gzip.open(output_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    print(f"Compression complete: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Compress a file to gzip format.')
    parser.add_argument('input_path', help='Path to the input file')
    parser.add_argument('--output', '-o', help='Path to the output file (default: input_path.gz)')

    args = parser.parse_args()
    compress_file(args.input_path, args.output)
