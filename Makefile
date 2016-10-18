all: build

.PHONY: all build install clean

BUILD_DIR = build
INSTALL_DIR = /var/www/html

include transit_www/www.mk

include $(shell python -m transit_feed --target makefile --debug \
    --build-dir $(BUILD_DIR)/feed)

clean:
	rm -fR $(BUILD_DIR)
