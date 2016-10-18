build: build_feed

install: install_feed

.PHONY: build_feed install_feed {{ build_dir }}/{{ target }}.mk

install_feed: {{ install_dir }}/{{ target }}/index.gz

build_feed: {{ build_dir }}/{{ target }}/index.gz

{{ build_dir }}/{{ target }}.mk:
	{{ make_me }}

{{ build_dir }}/{{ target }}.zip:
	mkdir -p $(@D)
	wget -c "{{ url }}" -O "$@"

{{ build_dir }}/{{ target }}/index.gz: {{ build_dir }}/{{ target }}.zip
	rm -fR $(@D)
	python -m {{ script_name }} --target datastore {{ make_flags }} $< --dest $(@D)
	touch $@

{{ install_dir }}/{{ target }}/index.gz: {{ build_dir }}/{{ target }}/index.gz
	rm -fR {{ install_dir }}/{{ target }}
	mkdir -p {{ install_dir }}/{{ target }}
	cp {{ build_dir }}/{{ target }}/*.gz $(@D)
