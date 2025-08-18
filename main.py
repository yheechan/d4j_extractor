import argparse
import logging
import os
from dotenv import load_dotenv

from lib.extractor_engine import ExtractorEngine
from lib.mutation_testing_engine import MutationTestingEngine
from lib.saver_engine import SaverEngine
from lib.constructor_engine import ConstructorEngine
from lib.postprocessor_engine import PostProcessorEngine
from lib.slack import Slack

def make_parser():
    parser = argparse.ArgumentParser(description="Extract dynamic data from defects4j")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output")

    # General arguments
    parser.add_argument("-pid", "--project-id", type=str, help="Project ID to extract data from")
    parser.add_argument("-el", "--experiment-label", type=str, required=True, help="Label for the experiment")

    # Arguments for ExtractorEngine
    parser.add_argument("-e", "--extractor", action="store_true", help="Run the extractor engine")
    parser.add_argument("-p", "--parallel", type=int, default=10, help="Number of parallel processes to run")
    parser.add_argument("-wmc", "--with-mutation-coverage", action="store_true", help="Enable mutation coverage")
    parser.add_argument("-tm", "--time-measurement", action="store_true", help="Enable time measurement")

    # Arguments for MutationTestingEngine
    parser.add_argument("-mt", "--mutation-testing", action="store_true", help="Run the mutation testing engine")

    # Arguments for SaverEngine
    parser.add_argument("-sr", "--save-results", action="store_true", help="Save the extracted data to db")
    parser.add_argument("-bid", "--bug-id", type=str, required=False, help="Bug ID to save data for")

    # Arguments for ConstructorEngine
    parser.add_argument("-c", "--constructor", action="store_true", help="Run the constructor engine")

    # Arguments for PostProcessorEngine
    parser.add_argument("-pp", "--postprocessor", action="store_true", help="Run the postprocessor engine")
    parser.add_argument("-sb", "--subjects", type=str, nargs='+', default=["Lang"], help="List of subjects to process")

    return parser

def set_logger(verbose=False, debug=False):
    if verbose:
        logging.basicConfig(level=logging.INFO, format='[%(levelname)s - %(asctime)s] %(filename)s::%(funcName)s - %(message)s')
    elif debug:
        logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s - %(asctime)s] %(filename)s::%(funcName)s - %(message)s')
    else:
        logging.basicConfig(level=logging.WARNING, format='[%(levelname)s - %(asctime)s] %(filename)s::%(funcName)s - %(message)s')

def main():
    parser = make_parser()
    args = parser.parse_args()

    set_logger(verbose=args.verbose, debug=args.debug)
    load_dotenv()

    slack = Slack(
        slack_channel=os.getenv("SLACK_CHANNEL"),
        slack_token=os.getenv("SLACK_TOKEN"),
        bot_name="D4J Extractor Bot"
    )
    function_name = "main"

    logging.info("Starting the script with arguments: %s", args)

    if args.extractor:
        if not args.project_id:
            logging.error("Project ID is required when running the extractor.")
            return
        extractor_engine = ExtractorEngine(args.project_id, args.parallel, args.experiment_label, args.with_mutation_coverage, args.time_measurement)
        function_name = "ExtractorEngine"
        slack.send_message(f"Starting {function_name} for project {args.project_id} with parallel={args.parallel} with_mutation_coverage={args.with_mutation_coverage}.")
        extractor_engine.run()
    elif args.mutation_testing:
        if not args.project_id:
            logging.error("Project ID is required when running the mutation testing.")
            return
        mutation_testing_engine = MutationTestingEngine(args.project_id, args.bug_id, args.experiment_label, args.parallel, args.time_measurement)
        function_name = "MutationTestingEngine"
        slack.send_message(f"Starting {function_name} for project {args.project_id} and bug {args.bug_id} with parallel={args.parallel}.")
        mutation_testing_engine.run()
    elif args.save_results:
        if not args.project_id:
            logging.error("Project ID is required when saving results.")
            return
        if not args.bug_id:
            logging.error("Bug ID is required when saving results.")
            return
        saver_engine = SaverEngine(args.project_id, args.bug_id, args.experiment_label, args.time_measurement)
        function_name = "SaverEngine"
        slack.send_message(f"Starting {function_name} for project {args.project_id} and bug {args.bug_id}.")
        saver_engine.run()
    elif args.constructor:
        if not args.project_id:
            logging.error("Project ID is required when running the constructor.")
            return
        constructor_engine = ConstructorEngine(args.project_id, args.experiment_label)
        function_name = "ConstructorEngine"
        slack.send_message(f"Starting {function_name} for project {args.project_id}.")
        constructor_engine.run()
    elif args.postprocessor:
        if not args.experiment_label:
            logging.error("Experiment label is required when running the postprocessor.")
            return
        post_processor_engine = PostProcessorEngine(args.experiment_label, args.subjects)
        function_name = "PostProcessorEngine"
        slack.send_message(f"Starting {function_name} for experiment {args.experiment_label}.")
        post_processor_engine.run()
    
    slack.send_message(f"{function_name} completed successfully.")


if __name__ == "__main__":
    main()