cd ../


# echo "Running Lang with coverage..."
# mkdir -p ./log/Lang
# time python3 main.py -pid Lang -el withCoverage_1 --parallel 8 --extractor --with-mutation-coverage -d > ./log/Lang/Lang_withCoverage_1.log 2>&1

echo "Running Mockito with coverage..."
mkdir -p ./log/Mockito
time python3 main.py -pid Mockito -el withCoverage_1 --parallel 8 --extractor --with-mutation-coverage -d > ./log/Mockito/Mockito_withCoverage_1.log 2>&1

# echo "Running Math with coverage..."
# mkdir -p ./log/Math
# time python3 main.py -pid Math -el withCoverage_1 --parallel 8 --extractor --with-mutation-coverage -d > ./log/Math/Math_withCoverage_1.log 2>&1

# echo "Running Time with coverage..."
# mkdir -p ./log/Time
# time python3 main.py -pid Time -el withCoverage_1 --parallel 8 --extractor --with-mutation-coverage -d > ./log/Time/Time_withCoverage_1.log 2>&1

# echo "Running Chart with coverage..."
# mkdir -p ./log/Chart
# time python3 main.py -pid Chart -el withCoverage_1 --parallel 8 --extractor --with-mutation-coverage -d > ./log/Chart/Chart_withCoverage_1.log 2>&1

# echo "Running Closure with coverage..."
# mkdir -p ./log/Closure
# time python3 main.py -pid Closure -el withCoverage_1 --parallel 8 --extractor --with-mutation-coverage -d > ./log/Closure/Closure_withCoverage_1.log 2>&1

