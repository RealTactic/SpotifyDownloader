import requests
import time
import os
from os import path
import shutil
import threading
import sys

from mutagen.mp3 import MP3, EasyMP3
from mutagen.id3 import ID3, APIC, error

import colorama
from colorama import Fore
colorama.init(autoreset=True)

# CLI params
if "help" in sys.argv:
    y = Fore.YELLOW
    m = Fore.MAGENTA
    c = Fore.CYAN
    g = Fore.GREEN
    print(f"""{m}Welcome | Help Menu
{y}Description:
This program was made to download spotify music (from youtube) given a spotify link.
It will automatically fetch cover art and metadata (ID3 tags) and add them to 
downloaded files. This is a one man project which I made to be open source for others to use. :)

{g}Input any spotify 'track', 'album' or 'playlist' url as a parameter to start.
If no urls are supplied, program will run normally with any specified flags.
When inputting parameters, you may input multiple links at a time.

{y}help {c}| Shows this help menu.

{y}-y   {c}| Force program to continue without asking user for confirmation.
{y}-T   {c}| Set custom amount of MAX download threads.
""")
    quit()

links = []
for Links in sys.argv:
    if Links.startswith("https://open.spotify.com/"):
        links.append(Links)
Force_Continue = True if "-y" in sys.argv else False
Arguments_supplied = True if links else False


spotify_dl_api = "https://api.spotify-downloader.com/"
MAX_THREADS = 5  # default amount threads
# custom max thread by given params
if "-T" in sys.argv:
    mt_num = sys.argv.index("-T") + 1
    if len(sys.argv) != mt_num:
        mt_num = sys.argv[mt_num]
        if str(mt_num).isdigit():
            if int(mt_num) > 20:
                mt_num = MAX_THREADS
                print(f"{Fore.YELLOW}Too Many Threads, Reduced to 5")
            MAX_THREADS = mt_num

# Check if 2 dir exists or make them
DIRS = ("buffer", "Audio")
for d in DIRS:
    if not path.exists(path.abspath(d)):
        os.mkdir(path.abspath(d))


def getSpotify_urlInfo(_url):
    tries = 0
    max_tries = 5
    while tries != max_tries:
        try:
            result = requests.post(spotify_dl_api, data={"link": _url})
            if result.status_code == 200:
                return result.json()
        except:
            pass
        tries += 1
        time.sleep(1)
        print(f"{Fore.RED}Failed to get url info, {tries} of {max_tries} remaining.")
    print(f"{Fore.YELLOW}Could not fetch url info, exceeded max tries.")


def getUrlInput():
    while True:
        print(f"{Fore.GREEN}Input Spotify URL:", end="")
        _input = input()
        if _input.startswith("https://open.spotify.com/"):
            return _input
        print(f"{Fore.BLUE}Must be a spotify url.")


def getCoverart(_url, _track_name):
    while True:
        try:
            result = requests.get(_url)
            if result.status_code == 200:
                return result.content
        except:
            pass
        print(f"{Fore.RED}Failed to get cover art for {Fore.YELLOW}{_track_name}.")
        time.sleep(1)


def getAudioMP3(_url, _track_name):
    while True:
        try:
            result = requests.get(_url)
            if result.status_code == 200:
                return result.content
        except:
            pass
        print(f"{Fore.RED}Failed to get mp3 file for {Fore.YELLOW}{_track_name}.")
        time.sleep(1)

# save a file into buffer folder
def addBufferFile(_name, _contents):
    _path = path.abspath("buffer\\" + _name)
    _file = open(_path, "wb")
    _file.write(_contents)
    _file.close()
    return _path

# move file from buffer to Audio folder
def movefrombuffer(_new_dir=None):
    old_path = path.abspath("buffer") + "\\"
    new_path = path.abspath("Audio") + "\\"
    if _new_dir:
        _dir = new_path + _new_dir + "\\"
        if not path.exists(_dir):
            os.mkdir(_dir)
        new_path = _dir

    Files = os.listdir(path.abspath("buffer"))
    for f in Files:
        if f.endswith(".mp3"):
            shutil.move(old_path + f, new_path + f)

# Download mp3 file and cover art
def DownloadMP3(_audio_url, _cover_url, _track_name):
    _Cover_art = None
    if _cover_url:
        print(f"{Fore.YELLOW}{_track_name}{Fore.GREEN} |{Fore.BLUE} Getting cover art.")
        _Cover_art = getCoverart(_cover_url, _track_name)
    print(f"{Fore.YELLOW}{_track_name}{Fore.GREEN} |{Fore.BLUE} Dowloading audio file.")
    _Audio_file = getAudioMP3(_audio_url, _track_name)

    _file_name = f"{_track_name}.mp3"
    _path_to_audio = addBufferFile(_file_name, _Audio_file)
    if _cover_url:
        return _Cover_art, _path_to_audio
    return _path_to_audio


def AddID3Tags(_cover_art, _track_name, _path_to_audio, _ID3: dict):
    # Add cover art to file
    audio = MP3(_path_to_audio, ID3=ID3)
    try:
        audio.add_tags()
    except error:
        pass
    audio.tags.add(APIC(mime="image/jpeg", type=3, desc=u"Cover", data=_cover_art))
    audio.save()

    # Add ID3 tags to file
    audio = EasyMP3(_path_to_audio)
    audio["title"] = _ID3["title"]  # title
    audio["artist"] = _ID3["artists"]  # artists
    audio["album"] = _ID3["albumname"]  # album name
    audio["date"] = _ID3["albumreleasedate"]  # year date
    audio.save()
    print(f"{Fore.YELLOW}{_track_name}{Fore.GREEN} |{Fore.BLUE} Added ID3 tags.")


def print_musicInfo(_MI):
    _music_type = _MI["type"]

    def p_track(name, artists: list, size):
        artists_str = ""
        for artist in artists:
            artists_str += artist + " "
        size = f"{size / 1000000}Mb"
        print(f"{Fore.MAGENTA}Song: {Fore.BLUE}{name} {Fore.MAGENTA}by {Fore.BLUE}{artists_str}{Fore.LIGHTYELLOW_EX}{size}")

    if _music_type == "track":
        """ I need 
        album name
        albumreleasedate
        name
        artist
        size
        """
        #print(_MI)
        _album_info = _MI["album"]

        _Album_name = _album_info["name"]
        _Album_releaseDate = _album_info["releaseDate"][:4]
        _Album_cover_url = _album_info["cover"]

        _Track_audio_url = _MI["audio"]["url"]
        _Track_audio_size = _MI['audio']['size']

        _track_name = _MI["name"]
        _track_artists = _MI["artists"]
        p_track(_track_name, _track_artists, _Track_audio_size)
        _ID3TrackInfo = {
            "title": _track_name,
            "artists": _track_artists,
            "albumname": _Album_name,
            "albumreleasedate": _Album_releaseDate
        }
        return _ID3TrackInfo, _Album_cover_url, _Track_audio_url
    elif _music_type == "album":
        _album_info = _MI["album"]
        _Album_name = _album_info["name"]
        _Album_releaseDate = _album_info["releaseDate"][:4]
        _Album_cover_url = _album_info["cover"]
        _Track_list = _MI["tracks"]

        _parsed_tracks = []

        _total_T_size = 0
        print(f"{Fore.CYAN}Album: {Fore.LIGHTMAGENTA_EX}{_Album_name} - {_Album_releaseDate}")
        for _track in _Track_list:
            # print track
            _Track_audio_size = _track['audio']['size']
            _total_T_size += _Track_audio_size
            p_track(_track["name"], _track["artists"], _Track_audio_size)

            # parse track
            _ID3TrackInfo = {
                "title": _track["name"],
                "artists": _track["artists"],
                "albumname": _Album_name,
                "albumreleasedate": _Album_releaseDate
            }
            _Track_audio_url = _track["audio"]["url"]
            _parsed_tracks.append({"ID3": _ID3TrackInfo, "url": _Track_audio_url})
        print(f"{Fore.CYAN}Total: {Fore.LIGHTYELLOW_EX}{_total_T_size / 1000000}Mb")
        return _parsed_tracks, _Album_cover_url
    elif _music_type == "playlist":
        _playlist_name = _MI["name"]
        _Tracks = _MI["tracks"]

        _parsed_tracks = []

        _total_T_size = 0
        print(f"{Fore.YELLOW}Playlist: {Fore.MAGENTA}{_playlist_name}")
        for _track in _Tracks:
            # Print Track
            _Track_audio_size = _track['audio']['size']
            _total_T_size += _Track_audio_size
            p_track(_track["name"], _track["artists"], _Track_audio_size)

            # Parse Track
            _ID3TrackInfo = {
                "title": _track["name"],
                "artists": _track["artists"],
                "albumname": _track["album"]["name"],
                "albumreleasedate": _track["album"]["releaseDate"][:4]
            }
            _Track_audio_url = _track["audio"]["url"]
            _Track_cover_url = _track["album"]["cover"]
            _parsed_tracks.append({"ID3": _ID3TrackInfo, "audioUrl": _Track_audio_url, "coverUrl": _Track_cover_url})
        print(f"{Fore.CYAN}Total: {Fore.LIGHTYELLOW_EX}{_total_T_size / 1000000}Mb")
        return _parsed_tracks


def downloadTrack_thread(_audio_url, _cover_or_Coverurl, _ID3):
    global thread_num
    downloadTrack(_audio_url, _cover_or_Coverurl, _ID3)
    thread_num -= 1


def downloadTrack(_audio_url, _cover_or_Coverurl, _ID3):
    _track_name = _ID3["title"]
    # get audio
    if type(_cover_or_Coverurl) == str:
        _cover_or_Coverurl, _audioPath = DownloadMP3(_audio_url, _cover_or_Coverurl, _track_name)
    else:
        _audioPath = DownloadMP3(_audio_url, None, _track_name)

    # add id3 tags
    AddID3Tags(_cover_or_Coverurl, _track_name, _audioPath, _ID3)


running = True
while running:
    if Arguments_supplied:
        if links:
            url = links[0]
            links.pop(0)
        else:
            break
    else:
        url = getUrlInput()
    print(f"{Fore.CYAN}Getting url information.")
    music_info = getSpotify_urlInfo(url)
    if not music_info:
        continue
    Track_information = print_musicInfo(music_info)
    # confirm continuation
    if not Force_Continue:
        print(f"{Fore.GREEN}Proceed? {Fore.BLUE}\"y\" ", end="")
        if input() != "y":
            continue

    music_type = music_info["type"]
    if music_type == "track":
        # Track data
        ID3TrackInfo = Track_information[0]
        Album_cover_url = Track_information[1]
        Track_audio_url = Track_information[2]

        # Download Track, Add ID3 Tags, Add Cover
        downloadTrack(Track_audio_url, Album_cover_url, ID3TrackInfo)

        # Move Files | buffer -> Audio | dir
        movefrombuffer()
    elif music_type == "album":
        Album_name = music_info["album"]["name"]
        Album_cover_url = Track_information[1]
        Track_list = list(Track_information[0])

        # get cover art for album
        print(f"{Fore.BLUE}Album: {Fore.YELLOW}{Album_name}{Fore.GREEN} |{Fore.BLUE} Getting cover art.")
        Album_Cover_art = getCoverart(Album_cover_url, Album_name)
        thread_num = 0
        for track in Track_list:
            ID3TrackInfo = track["ID3"]
            Track_audio_url = track["url"]

            thread = threading.Thread(target=downloadTrack_thread, args=(Track_audio_url, Album_Cover_art, ID3TrackInfo))
            thread.daemon = True
            thread.start()

            thread_num += 1
            while thread_num == MAX_THREADS: time.sleep(0.1)
        while thread_num != 0: time.sleep(0.1)

        movefrombuffer(Album_name)
        print(f"{Fore.BLUE}{music_type}: {Fore.YELLOW}{Album_name}{Fore.GREEN} |{Fore.BLUE} Finished.")
    elif music_type == "playlist":
        playlist_name = music_info["name"]
        Tracks = Track_information

        thread_num = 0
        for track in Tracks:
            ID3TrackInfo = track["ID3"]
            Track_audio_url = track["audioUrl"]
            Track_cover_url = track["coverUrl"]

            #downloadTrack(Track_audio_url, Track_cover_url, ID3TrackInfo)
            thread = threading.Thread(target=downloadTrack_thread, args=(Track_audio_url, Track_cover_url, ID3TrackInfo))
            thread.daemon = True
            thread.start()

            thread_num += 1
            while thread_num == MAX_THREADS: time.sleep(0.1)
        while thread_num != 0: time.sleep(0.1)
        movefrombuffer(playlist_name)
        print(f"{Fore.BLUE}{music_type}: {Fore.MAGENTA}{playlist_name}{Fore.GREEN} |{Fore.BLUE} Finished.")
    print()

