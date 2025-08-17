clean:
	./clean.sh
get-saved:
	python3 findMusic.py
get-links:
	python3 findMusic.py --links
download:
	python3 findMusic.py --download
meta:
	python3 findMusic.py --meta
get-lyrics:
	python3 findMusic.py --lyrics
get-suggest:
	python3 findMusic.py --suggest
add-suggest: get-suggest
	python3 findMusic.py --add
get-recent:
	python3 findMusic.py --recent
