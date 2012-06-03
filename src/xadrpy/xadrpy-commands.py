#!/usr/bin/env python
"""
Console commands for xadrpy
"""
import os
import argparse
import xadrpy.conf
from xadrpy.cli.create import CreateHandler

CURRENT_PATH = os.getcwd()  
XADRPY_PATH = os.path.realpath(os.path.dirname(__file__))

def _copy_file(source, dest):
    pass

if __name__== "__main__":

    parser = argparse.ArgumentParser(description='xadrpy console tools')
    subparsers = parser.add_subparsers(help='commands help')
    
    setup_parser = subparsers.add_parser('create', help='create django-xadrpy project')
    setup_parser.set_defaults(handler=CreateHandler(setup_parser))    

    args = parser.parse_args()
    
    args.handler(args)
    