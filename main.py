import argparse
import logging

from lib.extractor_engine import ExtractorEngine
from lib.saver_engine import SaverEngine

def make_parser():
    parser = argparse.ArgumentParser(description="Extract dynamic data from defects4j")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output")
    parser.add_argument("-pid", "--project-id", type=str, required=True, help="Project ID to extract data from")

    parser.add_argument("-e", "--extractor", action="store_true", help="Run the extractor engine")
    parser.add_argument("-p", "--parallel", type=int, default=10, help="Number of parallel processes to run")
    parser.add_argument("-el", "--experiment-label", type=str, required=True, help="Label for the experiment")

    parser.add_argument("-sr", "--save-results", action="store_true", help="Save the extracted data to db")
    parser.add_argument("-bid", "--bug-id", type=str, required=False, help="Bug ID to save data for")
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

    logging.info("Starting the script with arguments: %s", args)

    if args.extractor:
        extractor_engine = ExtractorEngine(args.project_id, args.parallel, args.experiment_label)
        extractor_engine.run()
    elif args.save_results:
        if not args.bug_id:
            logging.error("Bug ID is required when saving results.")
            return
        saver_engine = SaverEngine(args.project_id, args.bug_id, args.experiment_label)
        saver_engine.run()


if __name__ == "__main__":
    main()