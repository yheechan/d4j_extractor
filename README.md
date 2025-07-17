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