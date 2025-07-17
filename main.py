import argparse
import logging

from lib.extractor_engine import ExtractorEngine

def make_parser():
    parser = argparse.ArgumentParser(description="Extract dynamic data from defects4j")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output")
    return parser

def set_logger(verbose=False, debug=False):
    if verbose:
        logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(filename)s::%(funcName)s - %(message)s')
    elif debug:
        logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(filename)s::%(funcName)s - %(message)s')
    else:
        logging.basicConfig(level=logging.WARNING, format='[%(levelname)s] %(filename)s::%(funcName)s - %(message)s')

def main():
    parser = make_parser()
    args = parser.parse_args()
    set_logger(verbose=args.verbose, debug=args.debug)

    logging.info("Starting the script with arguments: %s", args)

    extractor_engine = ExtractorEngine()
    extractor_engine.run()

if __name__ == "__main__":
    main()