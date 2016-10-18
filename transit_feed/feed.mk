feed: {{ target }}/index.gz

.PHONY: feed {{ target }}.zip {{ target }}.mk

{{ target }}.zip:
	wget -c "{{ url }}" -O "{{ target }}.zip"

{{ target }}/index.gz: {{ target }}.zip
	rm -fR $(@D)
	python -m {{ script_name }} --target datastore {{ make_flags }} $< --dest $(@D)
	rm -fR $(HTML_DIR)/feeds/$(notdir {{ target }})
	mkdir -p $(HTML_DIR)/feeds/$(notdir {{ target }})
	cp {{ target }}/*.gz $(HTML_DIR)/feeds/$(notdir {{ target }})

"{{ target }}.mk":
	{{ make_me }}
