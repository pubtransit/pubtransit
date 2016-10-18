all: www

.PHONY: www

WWW_DIR = $(BUILD_DIR)/www
WWW_SRC_DIR = transit_www
WWW_SOURCES = $(shell find $(WWW_SRC_DIR)/ -type f -iregex ".*\.(py|html|js)")
WWW_PRODUCTS = $(WWW_DIR)/index.html

www: $(WWW_PRODUCTS)

$(WWW_PRODUCTS): $(WWW_SOURCES)
	mkdir -p $(WWW_DIR)
	python -m transit_www get-html > "$(WWW_DIR)/index.html"
