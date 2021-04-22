import logging

import requests

import tweepy
import api as ap
import time
import os
import moviepy.editor as mp
import spotify as spo

from ShazamAPI import Shazam

auth = tweepy.OAuthHandler(ap.CONSUMER_KEY, ap.CONSUMER_SECRET_KEY)
auth.set_access_token(ap.ACCESS_TOKEN,ap.ACCESS_TOKEN_SECRET)

temp_name = "temp.mp4"
searchfile = "searchfile.mp3"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def check_id_replied(m_id):
    with open('mentdb.txt',"r") as f:
        mentid = m_id
        for id in f:
            if mentid == int(id):
                return True

    f = open('mentdb.txt',"a")
    f.write("\n" + str(m_id))
    f.close()
    return False

def download_vid(link):
    with requests.get(link, stream=True) as r:
        r.raise_for_status()
        with open(temp_name,'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print("downloaded vid")
    return True

def convert_to_mp3():
    temp_vid = mp.VideoFileClip(temp_name)
    audio_ext = temp_vid.audio
    audio_ext.write_audiofile(searchfile)
    temp_vid.close()
    audio_ext.close()
    os.remove(temp_name)
    print("ended convert")

def shazamsearch():

    detect_music = open(searchfile,'rb').read()
    shazam = Shazam(detect_music)
    recognize_generator = shazam.recognizeSong()
    sample = ""
    sampl = ""
    while True:
        print("alo girdik?")
        sample = next(recognize_generator)
        #sampl = sample[1]['track']['hub']['providers'][0]['actions'][0]
        if(sample !=""):
            artist = sample[1]['track']['subtitle']
            print(sample[1])
            song = sample[1]['track']['title']
            sampl = song + "," + artist
        if sampl != "":
            break
        print(sampl)
        os.remove(searchfile)

    return sampl

def handle_req(api,since_id):
    logger.info("loading ments")
    new_id = since_id

    for mention in api.mentions_timeline(since_id=since_id):
        flag = check_id_replied(mention.id)
        if flag:  # mention already replied
            continue
        new_id = max(mention.id, new_id)
        get_ment_expanded = api.get_status(mention.in_reply_to_status_id, tweet_mode='extended', included_ext_alt_text=True, trim_user=True)._json
        aq = get_ment_expanded['extended_entities']['media'][0]['video_info']['variants'][0]['url']
        print(mention.text)
        download_vid(aq)
        convert_to_mp3()
        found_song = shazamsearch()
        if found_song == "":
            print("no result ")
            logger.info(f"NO MUSIC FOUND")
            continue
        sp = spo.find_song(found_song)
        print(sp)
        api.update_status(status = ("Here is the track you looking for: "+sp), in_reply_to_status_id = mention.id, auto_populate_reply_metadata=True)
        time.sleep(50)
    return new_id






def main():
    since_id = 1
    api = tweepy.API(auth,wait_on_rate_limit=True,wait_on_rate_limit_notify=True)
    while True:
        logger.info("waitin on next timeline")
        since_id = handle_req(api,since_id)
        time.sleep(50)

if __name__ == "__main__":
    main()
