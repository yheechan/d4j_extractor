cd ../


mkdir -p ./log/Lang
time python3 main.py -pid Lang -el timeMeasurement_1 --parallel 8 --extractor --with-mutation-coverage --time-measurement -d > ./log/Lang/Lang_timeMeasurement_1.log 2>&1


# mkdir -p ./log/Mockito
# time python3 main.py -pid Mockito -el timeMeasurement_1 --parallel 8 --extractor --with-mutation-coverage --time-measurement -d > ./log/Mockito/Mockito_timeMeasurement_1.log 2>&1

# mkdir -p ./log/Math
# time python3 main.py -pid Math -el timeMeasurement_1 --parallel 8 --extractor --with-mutation-coverage --time-measurement -d > ./log/Math/Math_timeMeasurement_1.log 2>&1

# mkdir -p ./log/Time
# time python3 main.py -pid Time -el timeMeasurement_1 --parallel 8 --extractor --with-mutation-coverage --time-measurement -d > ./log/Time/Time_timeMeasurement_1.log 2>&1

# mkdir -p ./log/Chart
# time python3 main.py -pid Chart -el timeMeasurement_1 --parallel 8 --extractor --with-mutation-coverage --time-measurement -d > ./log/Chart/Chart_timeMeasurement_1.log 2>&1

# mkdir -p ./log/Closure
# time python3 main.py -pid Closure -el timeMeasurement_1 --parallel 16 --extractor --with-mutation-coverage --time-measurement -d > ./log/Closure/Closure_timeMeasurement_1.log 2>&1

