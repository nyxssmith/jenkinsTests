#
# rundoctestcoverage.py
#
# Copyright (c) 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Run doctests and measure their code coverage on entire fontio2 library by
executing every .py file in a tree specified by user-supplied root or default
'fontio2' directory. Code coverage is measured using Ned Batchelder's
coverage.py which is availble through pip ($ pip install coverage) or at
http://nedbatchelder.com/code/coverage/install.html#install

Run this file with the -h option for help.
"""

from __future__ import print_function

import argparse
import os
import subprocess

# Edit default configuration here, not in main().
DFLT_ROOT_DIR = 'fontio3'
DFLT_SKIP_DIRS = ['.coverage', '.idea', 'build', 'hintsexperimental',
                  'test', 'unittest_scripts']
DFLT_SKIP_FILES = ['_generateUnicodeRanges_']


def main():
    """Main loop: gather args, iterate over files and run."""
    parser = argparse.ArgumentParser(
        description='Run doctests')

    thispath = os.path.dirname(os.path.realpath(__file__))
    rundflt = os.path.join(thispath, DFLT_ROOT_DIR)

    parser.add_argument(
        '-root',
        default=rundflt,
        help='Root of tree.')

    parser.add_argument(
        '-sd',
        '--skipdirs',
        nargs="*",
        default=DFLT_SKIP_DIRS,
        help='Directory names to skip')

    parser.add_argument(
        '-sf',
        '--skipfiles',
        nargs="*",
        default=DFLT_SKIP_FILES,
        help='File names to skip (partial OK; simple matching)')

    parser.add_argument(
        '-html',
        action='store_true',
        help="Generate HTML package.")
        
    parser.add_argument(
        '-m',
        '--report_missing',
        action='store_true',
        help="Show missing in text report.")

    args = parser.parse_args()

    subprocess.call(["coverage", "erase"])

    for dirname, dirnames, filenames in os.walk(args.root):
        if dirname not in args.skipdirs:
            for skd in args.skipdirs:
                if skd in dirnames:
                    dirnames.remove(skd)

            for filename in filenames:
                for skf in args.skipfiles:
                    if skf not in filename:
                        fullfile = os.path.join(dirname, filename)
                        if os.path.splitext(fullfile)[1] == '.py':
                            subprocess.call(["coverage", "run", "-p", fullfile])

    subprocess.call(["coverage", "combine"])

    params = ["coverage", "report"]
    if args.report_missing:
        params.append("-m")
    subprocess.call(params)

    if args.html:
        subprocess.call(["coverage", "html", "-d", "fontio2_coverage_report"])
        print("HTML report in 'fontio2_coverage_report' folder.")

if __name__ == '__main__':
    main()
