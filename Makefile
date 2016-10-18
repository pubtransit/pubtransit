all:

.PHONY: all clean

BUILD_DIR = build

include transit_www/www.mk

include $(shell \
    python -m transit_feed --target makefile --debug --build-dir $(BUILD_DIR)/feed)


clean:
	rm -fR $(BUILD_DIR)
