feed: {{ target }}/index.gz

.PHONY: feed {{ target }}.zip {{ target }}.mk

{{ target }}.zip:
	wget -c "{{ url }}" -O "{{ target }}.zip"

{{ target }}/index.gz: {{ target }}.zip
	rm -fR $(@D)
	python -m departures_feed.make --target datastore {{ make_flags }} $< --dest $(@D)

"{{ target }}.mk":
	{{ make_me }}
