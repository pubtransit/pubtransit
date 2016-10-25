all: build

.PHONY: all build install clean

BUILD_DIR = build
INSTALL_DIR = /var/www/html

include transit_www/www.mk
include transit_feed/feed.mk

deploy:
	ansible-playbook provision.yaml

clean:
	rm -fR $(BUILD_DIR)
