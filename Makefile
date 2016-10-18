all: html feed

BUILD_DIR = build

include $(shell \
    python -m transit_feed --target makefile --debug --build-dir $(BUILD_DIR))


HTML_DIR = $(BUILD_DIR)/html
HTML_SRC_DIR = transit_www
HTML_SOURCES = $(shell find $(HTML_SRC_DIR)/ -type f -iregex ".*\.(py|html|js)")
HTML_PRODUCTS = $(HTML_DIR)/index.html


clean:
	rm -fR $(BUILD_DIR)


html: $(HTML_DIR)/index.html


$(HTML_PRODUCTS): $(HTML_SOURCES)
	mkdir -p $(HTML_DIR)
	python -m transit_www get-html > "$(HTML_DIR)/index.html"
