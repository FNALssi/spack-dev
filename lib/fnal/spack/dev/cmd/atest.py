from llnl.util import tty

description = 'Simple subcommand test.'


def setup_parser(subparser):
    tty.debug('atest parser setup OK')


def atest(parser, args):
    tty.debug('atest command execution OK')
