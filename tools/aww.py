#!/usr/bin/env python

import argh

from ec2 import describe_images, describe


def main():
    parser = argh.ArghParser()
    parser.add_commands([describe_images, describe])
    parser.dispatch()


if __name__ == '__main__':
    main()
