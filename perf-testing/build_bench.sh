#!/bin/bash

g++ -std=c++11 -I/usr/include/hayai -fno-omit-frame-pointer -march=native -mtune=native -O3 -mpopcnt -pthread cbench.cpp -o cbench.bin
./cbench.bin
