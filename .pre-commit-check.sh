#!/bin/bash

# make doesn't really do command line arguments so this wrapper script passes arguments as 
# an environment variable to check only changed files (supplied by the pre-commit hook)  
export files=$*
make check