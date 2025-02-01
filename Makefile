SUBDIRS ?= debian

# Output docker image
PROJECT_NAME ?= educinfo
AUTHOR ?= doalou
REGISTRY ?= docker.io
BASE_IMAGE_REGISTRY ?= docker.io
WEB_SITE ?= doalou.org

IMAGE_VERSION ?= 1.0.0
IMAGE_NAME ?= $(PROJECT_NAME)

# Max CPU and memory
CPUS ?= 8.0
CPU_SHARES ?= 1024
MEMORY ?= 16GB
MEMORY_RESERVATION ?= 2GB
TMPFS_SIZE ?= 4GB
BUILD_CPU_SHARES ?= 1024
BUILD_MEMORY ?= 16GB

TEST_CMD ?= ./test/test.sh
RUN_CMD ?=

include DockerImages.mk
