#!/usr/bin/env python

import sys
import argparse
import cmd

def die(message):
    sys.stderr.write(message + '\n')
    sys.exit(1)

def main(argv):
    parser = argparse.ArgumentParser(prog='spackdev')
    subparsers = parser.add_subparsers(metavar='SUBCOMMAND', dest="command")

    print 'spackdev commands:', cmd.commands

    for cm in cmd.commands:
        module = cmd.get_module(cm)
        subparser = subparsers.add_parser(cm, help=module.description)
        module.setup_parser(subparser)

    args = parser.parse_args(argv[1:])

    command = cmd.get_command(args.command)
    try:
        return_val = command(parser, args)
    # except SpackError, e:
    #     e.die()
    except KeyboardInterrupt:
        sys.stderr.write('\n')
        die("Keyboard interrupt.")

    # Allow commands to return values if they want to exit with some other code.
    if return_val is None:
        sys.exit(0)
    elif isinstance(return_val, int):
        sys.exit(return_val)
    else:
        die("Bad return value from command %s: %s" % (args.command, return_val))
