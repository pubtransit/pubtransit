build: build_feed

install: install_feed

.PHONY: build_feed install_feed

include $(shell python -m transit_feed --target makefile --debug \
    --build-dir $(BUILD_DIR)/feed)

build_feed:
	@echo Build index file
	python -m transit_feed --target index --debug --build-dir $(BUILD_DIR)/feed

install_feed:
	@echo Install feed files
	rm -fR $(INSTALL_DIR)/tmp
	mkdir -p $(INSTALL_DIR)/tmp
	cp -fR $(BUILD_DIR)/feed $(INSTALL_DIR)/tmp
	rm -fR $(INSTALL_DIR)/feed
	mv $(INSTALL_DIR)/tmp/feed $(INSTALL_DIR)
	rm -fR $(INSTALL_DIR)/tmp
