build: build_www

install: install_www

.PHONY: build_www install_www \
	$(BUILD_DIR)/www/index.html \
	$(INSTALL_DIR)/index.html

build_www: $(BUILD_DIR)/www/index.html

install_www: $(INSTALL_DIR)/index.html

$(BUILD_DIR)/www/index.html:
	mkdir -p $(@D)
	python -m transit_www get-html > "$@"

$(INSTALL_DIR)/index.html:
	mkdir -p $(@D)
	cp "$(BUILD_DIR)/www/index.html" "$@"
