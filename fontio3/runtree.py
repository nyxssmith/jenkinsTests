#
# runtree.py
#
# Copyright (c) 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Run doctests on entire fontio2 library by executing every .py file in a tree,
specified by user-supplied root or default 'fontio2' directory. Configurable to
start at specified root as well as to skip directories/filenames containing
supplied strings (defaults supplied).
"""

from __future__ import print_function

import argparse
import os
import shutil
import subprocess

# Edit default configuration here, not in main().
DFLT_ROOT_DIR = 'fontio3'
DFLT_SKIP_DIRS = ['.coverage', '.idea', 'build', 'hintsexperimental',
                  'test', 'unittest_scripts']
DFLT_SKIP_FILES = ['_generateUnicodeRanges_']
DFLT_RESULT_DIR = 'qe/testing/'


def main():
    """Main loop: gather args, iterate over files and run."""
    parser = argparse.ArgumentParser(
        description='Run doctests')

    thispath = os.path.dirname(os.path.realpath(__file__))
    rundflt = os.path.join(thispath, DFLT_ROOT_DIR)
    resultdflt = os.path.join(thispath,DFLT_RESULT_DIR)
    if(os.path.exists(rundflt)==False):
        os.mkdir(rundflt)
    if(os.path.exists(resultdflt)==False):
        os.mkdir(resultdflt)

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
            '-rd',
            '--resultsdirectory',
            nargs="*",
            default=resultdflt,
            help="Save log file in teh results directory for each subprocess call.")
    
    parser.add_argument(
        '-sf',
        '--skipfiles',
        nargs="*",
        default=DFLT_SKIP_FILES,
        help='File names to skip (partial OK; simple matching)')

    parser.add_argument(
        '-p',
        '--printfilename',
        action='store_true',
        help="Print the name of each file before running it.")


    args = parser.parse_args()

    numModulesTested = 0
    moduleWithError = []
    #print ("\n Results dir = "+args.resultsdirectory[0]+"\n")
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
                            logfilename=''
                            if(os.path.exists(args.resultsdirectory[0])):
                                #print('\n filename = '+os.path.splitext(filename)[0]+'_log.txt')
                                logfilename = os.path.join(args.resultsdirectory[0],os.path.splitext(filename)[0]+'_log.txt')
                            if args.printfilename:
                                print('\n' + fullfile + ':')
                            if len(logfilename)>2 and len(args.resultsdirectory[0])>2:
                                numModulesTested+=1
                                f = open(logfilename,'w')
                                r_stdout = subprocess.call(['python', fullfile],stdout = f)
                                f.close()
                                if(os.path.getsize(logfilename)==0):
                                    os.remove(logfilename)
                                else:
                                    moduleWithError.append(' Error for '+filename+' in '+logfilename)

                            else:
                                numModulesTested+=1
                                subprocess.call(['python', fullfile])

    print ('\n ********************************************\n Test Summary:\n #. of test cases = '+str(numModulesTested))

    if(len(moduleWithError)>0):
        print ('\n #. of log files with information on test failures = '+str(len(moduleWithError)))
        print('\n Details on logs with errors \n')
        for moduleError in moduleWithError:
            print('\n'+moduleError)
        else:
            print ('\n All tests passed! ')
    print ('\n ********************************************\n')

    if(args.resultsdirectory and os.path.exists(args.resultsdirectory[0])):
        logfilename = os.path.join(args.resultsdirectory[0],'TestSummary.txt')
        f = open(logfilename,'w')
        f.write('\n ********************************************\n Test Summary:\n #. of test cases = '+str(numModulesTested))
        if(len(moduleWithError)>0):
            f.write('\n #. of log files with error information = '+str(len(moduleWithError)))
            f.write('\n Details on logs with errors \n')
            for moduleError in moduleWithError:
                f.write('\n'+moduleError)
        else:
            f.write ('\n All tests passed! ')
        f.write('\n ********************************************\n')
        f.close()
    

if __name__ == '__main__':
    main()
