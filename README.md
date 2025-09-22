# TACC Tools

This repository contains convenience tools for using and automating the usage of HPC systems.
Currently, it only support TACC, but may be extended in the future for other clusters.

## Installation

To use this tool from the command line, run the following to clone and install it to your
python environment.
```bash
git clone git@github.com:artzha/tacc_infra.git
cd tacc_infra
pip install -e .
```

## Usage 

### Build/push a pre-written Dockerfile

This commands builds the default Ubuntu 20.04 image with ROS and cuda 11.8 installed. It will
publish the docker image to docker hub after building.
```bash
export DOCKER_IMAGE_NAME=$DOCKER_USER/tacc_infra_ros
taccenv build_image $DOCKER_IMAGE_NAME
```

### Queue a job on TACC

Set the following environment variables to enable slack notifications for when your job is queued 
or ready.
```bash
export SLACK_WEBHOOK_URL=
export SLACK_MENTION_ID=
```

Here is an example command submtting a job to TACC. For more options, run `taccenv submit_job`
```bash
taccenv submit_job --time 00:60:00 --partition vm-small --allocation IRI23005
```

To see other commands, type `taccenv` and press enter to view the available commands (example below).

```
Usage:
  taccenv <scriptname> [args...]

Runs scripts from: /work/09156/arthurz/ls6/AMRL/tacc_infra/src/tacc_infra

Examples:
  taccenv build_image --tag dev
  taccenv submit_job --time 02:00:00

Available scripts:
  - __init__
  - build_image
  - submit_job
```