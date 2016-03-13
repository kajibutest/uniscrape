#!/bin/bash

set -x

SCRIPT_DIR=/Users/kajibu/lab/uniscrape
DATA_DIR=/Users/kajibu/data/lab/uniscrape

$SCRIPT_DIR/process_$1.py\
 --download_dir=$DATA_DIR/$1/download\
 --processed_dir=$DATA_DIR/$1/processed

