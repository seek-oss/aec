#!/usr/bin/env python

import argh

from ec2 import describe_images, describe, launch


def main():
    parser = argh.ArghParser()
    parser.add_commands([describe_images, describe, launch])
    parser.dispatch()


if __name__ == '__main__':
    main()
