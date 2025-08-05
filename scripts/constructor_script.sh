cd ..

# echo "Running Lang constructor script..."
# time python3 main.py -pid Lang -el attempt_1 -c > ./log/Lang/Lang_constructor_attempt_1.log 2>&1

# echo "Running Lang constructor script..."
# time python3 main.py -pid Mockito -el attempt_1 -c > ./log/Mockito/Mockito_constructor_attempt_1.log 2>&1

# echo "Running Math constructor script..."
# time python3 main.py -pid Math -el attempt_1 -c > ./log/Math/Math_constructor_attempt_1.log 2>&1

echo "Running Time constructor script..."
time python3 main.py -pid Time -el attempt_1 -c > ./log/Time/Time_constructor_attempt_1.log 2>&1

echo "Running Chart constructor script..."
time python3 main.py -pid Chart -el attempt_1 -c > ./log/Chart/Chart_constructor_attempt_1.log 2>&1

# echo "Running Closure constructor script..."
# time python3 main.py -pid Closure -el attempt_1 -c > ./log/Closure/Closure_constructor_attempt_1.log 2>&1
