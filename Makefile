all: build

.PHONY: all build install clean deploy test test_python test_deploy

BUILD_DIR = build
INSTALL_DIR = /var/www/html

include transit_www/www.mk
include pubtransit/feed.mk

deploy:
	ansible-playbook deploy.yml

test: test_python test_deploy

test_install: build install
	echo INSTALLED

test_python:
	tox

test_deploy: build
	vagrant up --provision

clean:
	rm -fR $(BUILD_DIR)
