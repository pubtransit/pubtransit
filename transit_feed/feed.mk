all: feed

.PHONY: feed {{ target }}.zip {{ target }}.mk

feed: {{ target }}/index.gz

{{ target }}.zip:
	wget -c "{{ url }}" -O "{{ target }}.zip"

{{ target }}/index.gz: {{ target }}.zip
	rm -fR $(@D)
	python -m {{ script_name }} --target datastore {{ make_flags }} $< --dest $(@D)

"{{ target }}.mk":
	{{ make_me }}
