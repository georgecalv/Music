from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import argparse
import requests
import music_tag
from bs4 import BeautifulSoup
from youtubesearchpython import VideosSearch
from pprint import pprint
from pytubefix import YouTube
from openai import OpenAI
from tqdm import tqdm
from datetime import datetime


load_dotenv()

class FindMusic:
    def __init__(self):
        os.environ["SPOTIPY_CLIENT_ID"] = os.getenv("SPOTIPY_CLIENT_ID")
        os.environ["SPOTIPY_CLIENT_SECRET"] = os.getenv("SPOTIPY_CLIENT_SECRET")
        os.environ["SPOTIPY_REDIRECT_URI"] = os.getenv("SPOTIPY_REDIRECT_URI")
        ai_key = os.getenv("OPEN_AI")
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="user-library-read playlist-modify-public playlist-modify-private user-read-currently-playing user-read-recently-played", open_browser=False))
        self.ai_client = client = OpenAI(api_key=ai_key, base_url="https://api.deepseek.com")
        self.saved_ids = []

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
                    self.saved_ids.append(item["track"]['uri'])
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
                    yt = YouTube(link)
                    thumbnail_url = yt.thumbnail_url
                    song = {
                        "name": name,
                        "artist": artist,
                        "link": link,
                        "thumbnail_url": thumbnail_url
                    }
                    result['songs'].append(song)
            print("Finished finding links")
            with open("saved_tracks_with_links.json", "w") as f:
                f.write(json.dumps(result, indent=4))
        except KeyboardInterrupt:
            with open("saved_tracks_with_links.json", "w") as f:
                f.write(json.dumps(result, indent=4))
    
    def download_music(self):
        print("Start Downloading...")
        with open("saved_tracks_with_links.json", "r") as f:
            data = json.load(f)
            num_songs = len(data['songs'])
            for index in tqdm(range(num_songs), desc="Downloading Songs"):
                song = data['songs'][index]
                link = song['link']
                if link:
                    try:
                        yt = YouTube(link)
                        audio = yt.streams.filter(only_audio=True).first()
                        if audio:
                            audio.download(output_path="./mp3s", filename=f'{song['name']}-{song['artist']}.mp3')
                    except Exception as e:
                        print("Error: ", e)
    def set_meta(self):
        print("Starting Meta Data Generation...")
        with open("saved_tracks_with_links.json", "r") as f:
            data = json.load(f)
            num = len(data['songs'])
            for index in tqdm(range(num), desc="Writing Meta Data"):
                song = data['songs'][index]
                mt_file = music_tag.load_file(f"./mp3s/{song['name']}-{song['artist']}")
                mt_file['artist'] = song['artist']
                mt_file['album'] = song['album']
                img_data = requests.get(song["thumbnail_url"]).content
                mt_file['artwork'] = img_data
                mt_file.save()
                

                

    def load_lyrics(self):
        with open("saved_tracks_with_links.json", "r") as f:
            data = json.load(f)
            num_songs = len(data["songs"])
            for index in tqdm(range(num_songs), desc="Downloading Lyrics"):
                song = data["songs"][index] 
                link = song["link"]
                try:
                    yt = YouTube(link)
                    caption = yt.captions['a.en']
                    if caption:
                        with open(f"./words/{song["name"]}-captions.txt", "w") as f:
                            f.write(caption)
                except:
                    print(f"Unable to get captions for {song['name']} by {song['artist']}")
                    continue


    def get_suggestions(self):
        print("Getting Suggestions...")
        with open("prompt.txt", 'r') as prompt:
            with open("saved_tracks.json", 'r') as songs:
                response = self.ai_client.chat.completions.create(
                    model="deepseek-reasoner",
                    messages=[
                        {"role": "system", "content": prompt.read().replace("\n", "")},
                        {"role": "user", "content": str(json.load(songs))},
                    ],
                    temperature=1.5,
                    stream=False
                )
            unclean_suggest = response.choices[0].message.content
            clean_str = unclean_suggest.strip('`').strip('json').strip()
            json_data = json.loads(clean_str)
            with open("music_suggestions.json", "w") as f:
                f.write(json.dumps(json_data, indent=4))
    
    def add_playlist(self):
        print("Adding to playlist...")
        self.load_user_saved()
        # get all tracks in playlist
        try:
            playlist_id = "0aO783eGEA5sKxpQlfxln6"
            results = self.sp.playlist_items(playlist_id, limit=100)
            added_tracks = []
            for item in results["items"]:
                added_tracks.append(item["track"]['uri'])
            with open("music_suggestions.json", "r") as f:
                data = json.load(f)
                tracks = []
                for song in data["songs"]:
                    q = f"artist:{song["artist"]}, track:{song["name"]}"
                    result = self.sp.search(q=q, limit=1)
                    try:
                        if result["tracks"]['items'][0]['uri'] not in added_tracks and result["tracks"]['items'][0]['uri'] not in self.saved_ids:
                            tracks.append(result["tracks"]['items'][0]['uri'])
                        else: 
                            print(f"Did not add {song["name"]} by {song["artist"]}")
                    except:
                        print(f"Unable to add {song['name']} by {song['artist']}")
                
                    # spotify:playlist:0aO783eGEA5sKxpQlfxln6
                self.sp.user_playlist_add_tracks(user="georgecal-us", playlist_id=playlist_id, tracks=tracks)
        except Exception as e:
            print(f"Exception: {e}")
    
    def get_recent(self):
        try:
            recent = self.sp.current_user_recently_played(limit=50)
            result = {'songs': []}
            with open("recently_played.json", 'w') as f:
                for song in recent['items']:
                    result['song'].append(
                        {
                            'played_at': song['played_at'],
                            'artist': song['track']['album']['artists'][0]['name'],
                            'track': song['track']['album']['name']
                        }
                    )
                f.write(json.dumps(result, indent=4))
                
        except Exception as e:
            print(f"Unable to get recents: {e}")





if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find and save Spotify music.")
    parser.add_argument("--links", action="store_true", help="Finds linked of saved tracks from Spotify")
    parser.add_argument("--download", action="store_true", help="Download music from saved tracks with links")
    parser.add_argument("--lyrics", action="store_true", help="Load lyrics from saved tracks with links")
    parser.add_argument("--suggestions", action="store_true", help="Get Ai suggesstions for new music")
    parser.add_argument("--add", action="store_true", help="Add AI suggestions to playlist")
    parser.add_argument("--recent", action="store_true", help="Get recently played")
    parser.add_argument("--meta", action="store_true", help="Load Metadata")
    args = parser.parse_args()

    find_music = FindMusic()
    if args.links:
        find_music.find_links()
    elif args.download:
        find_music.download_music()
    elif args.lyrics:
        find_music.load_lyrics()
    elif args.suggestions:
        find_music.get_suggestions()
        find_music.add_playlist()
    elif args.add:
        find_music.add_playlist()
    elif args.recent:
        find_music.get_recent()
    elif args.meta:
        find_music.set_meta()
    else:
       find_music.load_user_saved()
