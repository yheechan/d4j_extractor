import subprocess as sp
import logging

LOGGER = logging.getLogger(__name__)

def list_all_tests(PID, BID, EL, CORE, SCRIPTS_DIR):
        command = f"./1_list_tests.sh {PID} {BID} {EL} {CORE}"
        try:
            sp.check_call(command, shell=True, stderr=sp.DEVNULL, stdout=sp.DEVNULL, cwd=SCRIPTS_DIR)
            LOGGER.info(f"Listing tests for core {CORE} completed successfully.")
        except sp.CalledProcessError as e:
            LOGGER.error(f"Listing tests for core {CORE} failed with error: {e}")

def instrument(PID, BID, EL, CORE, WORK_NAME, SCRIPTS_DIR, srcClassPath=None):
    command = f"./2_instrument.sh {PID} {BID} {EL} {CORE}"
    try:
        sp.check_call(command, shell=True, stderr=sp.DEVNULL, stdout=sp.DEVNULL, cwd=SCRIPTS_DIR)
        LOGGER.info(f"Instrumentation for {PID}-{BID}-{EL}-core{CORE}-{WORK_NAME}-{srcClassPath} completed successfully.")
    except sp.CalledProcessError as e:
        LOGGER.error(f"Instrumentation for {PID}-{BID}-{EL}-core{CORE}-{WORK_NAME} failed with error: {e}")

def execute_with_coverage(PID, BID, EL, CORE, WORK_NAME, TARGET_TESTS, SCRIPTS_DIR, srcClassPath=None, timeout=None):
    command = f"./3_execute_with_coverage.sh {PID} {BID} {EL} {CORE} {TARGET_TESTS}"
    try:
        sp.check_call(command, shell=True, stderr=sp.DEVNULL, stdout=sp.DEVNULL, cwd=SCRIPTS_DIR, timeout=timeout)
        LOGGER.info(f"Execution with coverage for {PID}-{BID}-{EL}-core{CORE}-{WORK_NAME}-{TARGET_TESTS}-{srcClassPath} completed successfully.")
    except sp.TimeoutExpired:
        LOGGER.warning(f"Execution with coverage for {PID}-{BID}-{EL}-core{CORE}-{WORK_NAME}-{TARGET_TESTS} timed out")
    except sp.CalledProcessError as e:
        LOGGER.error(f"Execution with coverage for {PID}-{BID}-{EL}-core{CORE}-{WORK_NAME}-{TARGET_TESTS} failed with error: {e}")

def process_cov(PID, BID, EL, CORE, WORK_NAME, SCRIPTS_DIR, srcClassPath=None):
    command = f"./4_process_cov.sh {PID} {BID} {EL} {CORE} {WORK_NAME}"
    try:
        sp.check_call(command, shell=True, stderr=sp.DEVNULL, stdout=sp.DEVNULL, cwd=SCRIPTS_DIR)
        LOGGER.info(f"Process coverage for {PID}-{BID}-{EL}-core{CORE}-{WORK_NAME}-{srcClassPath} completed successfully.")
    except sp.CalledProcessError as e:
        LOGGER.error(f"Process coverage for {PID}-{BID}-{EL}-core{CORE}-{WORK_NAME} failed with error: {e}")
