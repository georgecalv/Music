from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import argparse
import requests
from bs4 import BeautifulSoup
from youtubesearchpython import VideosSearch
from pprint import pprint
from pytubefix import YouTube


load_dotenv()

class FindMusic:
    def __init__(self):
        os.environ["SPOTIPY_CLIENT_ID"] = os.getenv("SPOTIPY_CLIENT_ID")
        os.environ["SPOTIPY_CLIENT_SECRET"] = os.getenv("SPOTIPY_CLIENT_SECRET")
        os.environ["SPOTIPY_REDIRECT_URI"] = os.getenv("SPOTIPY_REDIRECT_URI")
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="user-library-read", open_browser=False))

    def load_user_saved(self):
        print("Starting to get saved tracks...")
        offset = 0
        limit = 50
        result = {'songs': []}
        try:
            for i in range(26):
                results = self.sp.current_user_saved_tracks(limit=limit, offset=offset)
                for item in results['items']:
                    track = item['track']
                    song = {
                        "name": track['name'],
                        "artist": track['artists'][0]['name'],
                        "album": track['album']['name'],
                    }
                    result['songs'].append(song)
                offset += limit
                i += 1
            with open("saved_tracks.json", "w") as f:
                f.write(json.dumps(result, indent=4))
            print("Saved tracks written to saved_tracks.json")
        except Exception as e:
            print("Error: ", e)
    
    def find_links(self):
        print("Starting to find links...")
        result = {'songs': []}
        try:
            with open("saved_tracks.json", "r") as f:
                data = json.load(f)
                num_songs = len(data['songs'])
                for index in range(num_songs):
                    print(f"({index}/{num_songs}): Finding link for song: ", data['songs'][index])
                    song = data['songs'][index]
                    name = song['name']
                    artist = song['artist']
                    search_query = f"{name} {artist}"
                    search = VideosSearch(search_query, limit=1)
                    link = search.result()['result'][0]['link']
                    song = {
                        "name": name,
                        "artist": artist,
                        "link": link
                    }
                    result['songs'].append(song)
            print("Finished finding links")
            with open("saved_tracks_with_links.json", "w") as f:
                f.write(json.dumps(result, indent=4))
        except KeyboardInterrupt:
            with open("saved_tracks_with_links.json", "w") as f:
                f.write(json.dumps(result, indent=4))
    
    def download_music(self):
        print("Start Downlaoding...")
        with open("saved_tracks_with_links.json", "r") as f:
            data = json.load(f)
            num_songs = len(data['songs'])
            for index in range(num_songs):
                print(f"({index}/{num_songs}): Downloading song: ", data['songs'][index], "...")
                song = data['songs'][index]
                link = song['link']
                if link:
                    try:
                        yt = YouTube(link)
                        audio = yt.streams.filter(only_audio=True).first()
                        if audio:
                            print('Downloading Audio...')
                            audio.download(output_path="./mp3s", filename=f'{song['name']}-{song['artist']}.mp3')
                    except Exception as e:
                        print("Error: ", e)
    def load_lyrics(self):
        with open("saved_tracks_with_links.json", "r") as f:
            data = json.load(f)
            num_songs = len(data["songs"])
            for index in range(num_songs):
                print(f" ({index}/{num_songs}): Getting lyrics for song: ", data["songs"][index])
                song = data["songs"][index] 
                link = song["link"]
                try:
                    yt = YouTube(link)
                    caption = yt.captions['a.en']
                    caption.save_captions("captions.txt")
                    if caption:
                        with open(f"./words/{song["name"]}-captions.txt", "w") as f:
                            f.write(caption)
                    else:
                        print("Unable to retrieve lyrics")
                except Exception as e:
                    print("Error: ", e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find and save Spotify music.")
    parser.add_argument("--links", action="store_true", help="Finds linked of saved tracks from Spotify")
    parser.add_argument("--download", action="store_true", help="Download music from saved tracks with links")
    parser.add_argument("--lyrics", action="store_true", help="Load lyrics from saved tracks with links")
    args = parser.parse_args()

    find_music = FindMusic()
    if args.links:
        find_music.find_links()
    elif args.download:
        find_music.download_music()
    elif args.lyrics:
        find_music.load_lyrics()
    else:
       find_music.load_user_saved()
