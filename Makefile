BUILD_DIR = build

include $(shell \
    python -m departures_feed.make --target makefile --debug --build-dir $(BUILD_DIR))


HTML_DIR = $(BUILD_DIR)/html
HTML_SRC_DIR = departures_web
HTML_SOURCES = $(shell find $(HTML_SRC_DIR)/ -type f -iregex ".*\.(py|html|js)")
HTML_PRODUCTS = $(HTML_DIR)/index.html


all: html feed


clean:
	rm -fR $(BUILD_DIR)


html: $(HTML_DIR)/index.html


$(HTML_PRODUCTS): $(HTML_SOURCES)
	mkdir -p $(HTML_DIR)
	python -m departures_web get-html > "$(HTML_DIR)/index.html"
