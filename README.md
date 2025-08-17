# d4j_extractor


### Test Command
* Run All Tests
```
PYTHONPATH=. pytest -s tests/
```

* Run Single Module Tests
```
PYTHONPATH=. pytest -s tests/test_file_utils.py
```

* Run Single Unit Tests
```
PYTHONPATH=. pytest -s tests/test_file_utils.py::test_receive_directory
```


### Running PIT
```
cd scripts/
./compile2prepare.sh <pid> <bid>
python3 measureExpectedTime.py --pid <pid> --bid <bid> --num-threads <num-threads>
python3 run_pit_all.py --pid <pid> --bid <bid> --num-threads <num-threads>
cd ../
python3 main.py -pid {pid} -bid {bid} -el {el} --save-results -v
```


```
python3 main.py -pid Lang -bid 1 -el attempt_2 -p 8 --mutation-testing -d
```


```
python3 main.py -pid Lang -bid 1 -el attempt_2 --save-results -d
```