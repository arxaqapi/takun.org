
build:
	zola $@

serve:
	zola $@

compress:
	tar -zcvf blog.tar.gz public

clean:
	rm -rf public