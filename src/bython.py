#! /usr/bin/python3
import parser
import argparse
import os
import sys
from logger import Logger

"""
Bython is Python with braces.

This is a command-line utility to translate and run bython files.

Flags:
    -V, --version:      Print version number
    -v, --verbose:      Print progress
    -c, --compile:      Translate to python file and store; do not run
    -t, --lower_true:   Adds support for lower case true/false
    -2, --python2:      Use python2 instead of python3
    input,              Bython files to process
    args,               Arguments to script
"""

VERSION_NUMBER = "0.5.2"
HOME = os.path.expanduser("~")

def main():
    # Setup argument parser
    argparser = argparse.ArgumentParser("bython", 
        description="Bython is a python preprosessor that translates braces into indentation", 
        formatter_class=argparse.RawTextHelpFormatter)
    argparser.add_argument("-V", "--version", 
        action="version", 
        version="Bython v%s\nMathias Lohne and Tristan Pepin 2017" % VERSION_NUMBER)
    argparser.add_argument("-v", "--verbose", 
        help="print progress",
        action="store_true") 
    argparser.add_argument("-c", "--compile", 
        help="translate to python only (don't run files)",
        action="store_true")
    argparser.add_argument("-k", "--keep",
        help="keep generated python files",
        action="store_true")
    argparser.add_argument("-t", "--lower_true",
        help="adds support for lower case true/false",
        action="store_true")
    argparser.add_argument("-2", "--python2",
        help="use python2 instead of python3 (default)",
        action="store_true")
    argparser.add_argument("-o", "--output",
        type=str, 
        help="specify name of output file (if -c is present)",
        nargs=1)
    argparser.add_argument("input",
        type=str, 
        help="bython files to process",
        nargs=1)
    argparser.add_argument("args",
        type=str,
        help="arguments to script",
        nargs=argparse.REMAINDER)

    # Parse arguments
    cmd_args = argparser.parse_args()

    # Create logger
    logger = Logger(cmd_args.verbose)

    # Check for invalid combination of flags
    if cmd_args.output is not None and cmd_args.compile is False:
        logger.log_error("Cannot specify output when bython is not in compile mode")
        sys.exit(1)

    # Where to output files
    if cmd_args.compile or cmd_args.keep:
        # Place in same folder, no path prefix
        placement_path = ""
        logger.log_info("Placing files in this directory")

    else:
        # Place in subfolder of home dir
        placement_path = HOME + "/.bythontemp/"
        logger.log_info("Placing files in %s" % placement_path)


    # List of all files to translate from bython to python
    parse_que = []

    # Add all files from cmd line
    parse_que.append(cmd_args.input[0])
    if cmd_args.compile:
        for arg in cmd_args.args:
            parse_que.append(arg)

    # Add all files from imports, and recursivelly (ish) add all imports from
    # the imports (and so on..)
    logger.log_info("jScanning for imports")
    i = 0
    while i < len(parse_que):
        try:
            import_files = parser.parse_imports(parse_que[i])

        except FileNotFoundError:
            logger.log_error("No file named '%s'" % parse_que[i])
            sys.exit(1)

        for import_file in import_files:
            if os.path.isfile(import_file) and not import_file in parse_que:
                logger.log_info("Adding '%s' to parse que" % import_file)
                parse_que.append(import_file)

        i += 1

    # Parsing
    try:
        for file in parse_que:
            current_file_name = file
            logger.log_info("Parsing '%s'" % file)
            outputname = cmd_args.output[0] if cmd_args.output is not None else None
            parser.parse_file(file, cmd_args.lower_true, placement_path, outputname)

    except (TypeError, FileNotFoundError) as e:
        logger.log_error("Error while parsing '%s'.\n%s" % (current_file_name, str(e)))
        # Cleanup
        try:
            for file in parse_que:
                os.remove(placement_path + parser._change_file_name(file, None))
        except:
            pass

        sys.exit(1)

    # Stop if we were only asked to translate
    if cmd_args.compile:
        return

    # Run file
    if cmd_args.python2:
        python_command = "python"

    else:
        python_command = "python3"

    filename = os.path.basename(cmd_args.input[0])

    try:
        logger.log_info("Running")
        logger.program_header()
        os.system("%s %s %s" % (
            python_command,
            placement_path + parser._change_file_name(filename, None),
            " ".join(arg for arg in cmd_args.args))
        )
        logger.program_footer()

    except Exception as e:
        logger.log_error("Unexpected error while running Python")
        logger.log_info("Reported error message: %s" % str(e))

    # Delete file if requested
    try:
        if not cmd_args.keep:
            logger.log_info("Deleting files")
            for file in parse_que:
                filename = os.path.basename(file)
                os.remove(placement_path + parser._change_file_name(filename, None))

    except:
        logger.log_error("Could not delete created python files.\nSome garbage may remain in ~/.bythontemp/")

if __name__ == '__main__':
    main()



