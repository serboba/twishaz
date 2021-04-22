import spotipy
import api as ap
from spotipy.oauth2 import SpotifyClientCredentials

client_credentials_manager = SpotifyClientCredentials(ap.SPOTIPY_CLIENT_ID,ap.SPOTIPY_CLIENT_SECRET)

sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


def find_song(search_link):
    separate = search_link.split(',')
    #print(separate[1], separate[0])
    response = sp.search(q="artist:" + separate[1] + " track:"+ separate[0], type="track", limit=3)
    res = response['tracks']['items'][0]['external_urls']['spotify']
    return res

def main():
    find_song()

if __name__ == "__main__":
    main()