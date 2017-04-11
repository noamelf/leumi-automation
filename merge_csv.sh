#!/usr/bin/env bash
cd $1
files_to_merge="6841.csv 6940.csv"
for file in ${files_to_merge}; do
    tail --lines=+2 ${file} >> 83240883626.csv
    rm ${file}
done
