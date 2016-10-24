build: build_feed

install: install_feed

.PHONY: build_feed install_feed

build_feed:
	python -m transit_feed --target index --debug --build-dir $(BUILD_DIR)/feed

include $(shell python -m transit_feed --target makefile --debug \
    --build-dir $(BUILD_DIR)/feed)

install_feed:
	rm -fR $(INSTALL_DIR)/feed
	mkdir -p $(INSTALL_DIR)/feed
	cp -fR $(BUILD_DIR)/feed $(INSTALL_DIR)
