#!/bin/bash


# echo "Starting Compilation..."
# echo "./0_compile2prepare.sh Lang 32 attempt_2"
# ./0_compile2prepare.sh Lang 32 attempt_2


# echo "Starting mutant generation"
# echo "./run_pit.sh Lang 32 attempt_2 8"
# ./run_pit.sh Lang 32 attempt_2 8


cd ../

# echo "Starting mutation testing..."
# echo "time python3 main.py -pid Lang -bid 32 -el attempt_2 -p 8 --mutation-testing --time-measurement -d > mutation_testing.log 2>&1"
# time python3 main.py -pid Lang -bid 32 -el attempt_2 -p 8 --mutation-testing --time-measurement -d > time-mutation_testing.log 2>&1

echo "Starting saving..."
echo "python3 main.py -pid Lang -bid 32 -el attempt_2 --save-results --time-measurement -d > time-saving.log 2>&1"
python3 main.py -pid Lang -bid 32 -el attempt_2 --save-results --time-measurement -d > time-saving.log 2>&1

