clean_mp3:
	./clean.sh
get-saved:
	python3 findMusic.py
get-links:
	python3 findMusic.py --links
download:
	python3 findMusic.py --download
get-lyrics:
	python3 findMusic.py --lyrics
get-suggest:
	python3 findMusic.py --suggest
add-suggest:
	python3 findMusic.py --add
