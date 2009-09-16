#!/bin/bash

for i in $( ls *test.py ); do
  echo "Running $i"
  ./$i
  echo
  echo
done

