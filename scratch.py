import argparse
#argparse setup for commandline args
parser= argparse.ArgumentParser()
parser.add_argument("-l", "--loglevel",
                    help= "Choose logging level: DEBUG INFO WARNING ERROR CRITICAL",
                    default="DEBUG",
                    choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                    )
args = parser.parse_args()
print(args.loglevel)
