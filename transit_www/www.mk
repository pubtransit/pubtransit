build: build_www

install: install_www

.PHONY: build_www install_www

WWW_SRC_DIR = transit_www
WWW_SOURCES = $(shell find $(WWW_SRC_DIR)/ -type f -iregex ".*\.(py|html|js)")

build_www: $(BUILD_DIR)/www/index.html

install_www: $(INSTALL_DIR)/index.html

$(BUILD_DIR)/www/index.html: $(WWW_SOURCES)
	mkdir -p $(@D)
	python -m transit_www get-html > "$@"

$(INSTALL_DIR)/index.html: $(BUILD_DIR)/www/index.html
	mkdir -p $(@D)
	cp "$<" "$@"
