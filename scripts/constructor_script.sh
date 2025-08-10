cd ..

echo "Starting all constructor scripts in parallel..."

# Start all processes in background
echo "Starting Lang constructor script..."
time python3 main.py -pid Lang -el attempt_1 -c > ./log/Lang/Lang_constructor_attempt_1.log 2>&1 &
LANG_PID=$!

echo "Starting Mockito constructor script..."
time python3 main.py -pid Mockito -el attempt_1 -c > ./log/Mockito/Mockito_constructor_attempt_1.log 2>&1 &
MOCKITO_PID=$!

echo "Starting Math constructor script..."
time python3 main.py -pid Math -el attempt_1 -c > ./log/Math/Math_constructor_attempt_1.log 2>&1 &
MATH_PID=$!

echo "Starting Time constructor script..."
time python3 main.py -pid Time -el attempt_1 -c > ./log/Time/Time_constructor_attempt_1.log 2>&1 &
TIME_PID=$!

echo "Starting Chart constructor script..."
time python3 main.py -pid Chart -el attempt_1 -c > ./log/Chart/Chart_constructor_attempt_1.log 2>&1 &
CHART_PID=$!

# echo "Starting Closure constructor script..."
# time python3 main.py -pid Closure -el attempt_1 -c > ./log/Closure/Closure_constructor_attempt_1.log 2>&1 &
# CLOSURE_PID=$!

# Wait for all processes to complete
echo "Waiting for all processes to complete..."
wait $LANG_PID && echo "Lang completed"
wait $MOCKITO_PID && echo "Mockito completed"
wait $MATH_PID && echo "Math completed"
wait $TIME_PID && echo "Time completed"
wait $CHART_PID && echo "Chart completed"
# wait $CLOSURE_PID && echo "Closure completed"

echo "All constructor scripts completed!"
