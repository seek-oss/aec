#!/usr/bin/env python

import argh

import ec2


def main():
    parser = argh.ArghParser()
    parser.add_commands([ec2.describe_images, ec2.describe, ec2.launch, ec2.start, ec2.stop, ec2.terminate])
    parser.dispatch()


if __name__ == '__main__':
    main()
