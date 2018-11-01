#!/usr/bin/env python

import csv

def write_csv_list(the_file, the_list):
    wr = csv.writer(the_file, quoting=csv.QUOTE_ALL)
    wr.writerow(the_list)

def read_all_csv_lists(filename):
    with open(filename, 'r') as the_file:
        reader = csv.reader(the_file)
        retval = []
        for line in reader:
            retval.append(line)
    return retval
