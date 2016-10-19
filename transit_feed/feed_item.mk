.PHONY: {{ build_dir }}/{{ target }}.mk

install_feed: {{ install_dir }}/{{ target }}/feed.gz

build_feed: {{ build_dir }}/{{ target }}/feed.gz

{{ build_dir }}/{{ target }}.mk:
	{{ make_me }}

{{ build_dir }}/{{ target }}.zip:
	mkdir -p $(@D)
	wget -c "{{ url }}" -O "$@"

{{ build_dir }}/{{ target }}/feed.gz: {{ build_dir }}/{{ target }}.zip
	rm -fR $(@D)
	python -m {{ script_name }} --target datastore {{ make_flags }} $< --dest $(@D)

{{ install_dir }}/{{ target }}/feed.gz: {{ build_dir }}/{{ target }}/feed.gz
	rm -fR {{ install_dir }}/{{ target }}
	mkdir -p {{ install_dir }}/{{ target }}
	cp {{ build_dir }}/{{ target }}/*.gz $(@D)
