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
auth.set_access_token(ap.ACCESS_TOKEN, ap.ACCESS_TOKEN_SECRET)

temp_name = "temp.mp4"
searchfile = "searchfile.mp3"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def check_id_replied(m_id):
    with open('mentdb.txt', "r") as f:
        mentid = m_id
        for id in f:
            if mentid == int(id):
                logger.info(f"mention already answered.")
                return True

    f = open('mentdb.txt', "a")
    f.write("\n" + str(m_id))
    f.close()
    logger.info(f"mention id added to txt.")
    return False


def download_vid(link):
    with requests.get(link, stream=True) as r:
        r.raise_for_status()
        with open(temp_name, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    logger.info(f"downloaded MP4 twitter video")
    return True


def convert_to_mp3():
    temp_vid = mp.VideoFileClip(temp_name)
    audio_ext = temp_vid.audio
    audio_ext.write_audiofile(searchfile)

    temp_vid.close()
    audio_ext.close()

    os.remove(temp_name)

    logger.info(f"MP4 file converted to MP3")

def loop_over(recognize_generator):
    while True:
        logger.info(f"loopin through audio intervals")
        try:
            yield next(recognize_generator)
        except StopIteration:
            return recognize_generator

def shazamsearch():
    logger.info(f"entered shazam search lessgo")
    detect_music = open(searchfile, 'rb').read()
    shazam = Shazam(detect_music)
    recognize_generator = shazam.recognizeSong()

    sample = tuple(loop_over(recognize_generator))

    sampl = ""

    if len(sample[0][1]['matches'])!=0:
        print("yeter amk")
        if len(sample[0][1]['track']['sections'][0]['metapages']) >=2:
            artist = sample[0][1]['track']['sections'][0]['metapages'][0]['caption']
            song = sample[0][1]['track']['sections'][0]['metapages'][1]['caption']
            sampl = song + "," + artist
        else:
            artist = sample[0][1]['track']['subtitle']
            song = sample[0][1]['track']['title']
            sampl = song + "," + artist

    if sampl == "":
        return "unknown"
    os.remove(searchfile)
    return sampl


def handle_req(api, since_id):
    logger.info("loading ments")
    new_id = since_id

    for mention in api.mentions_timeline(since_id=since_id):
        flag = check_id_replied(mention.id)
        if flag:  # mention already replied
            continue
        new_id = max(mention.id, new_id)

        get_ment_expanded = api.get_status(mention.in_reply_to_status_id, tweet_mode='extended', included_ext_alt_text=True, trim_user=True)._json
        aq = ""

        for j in get_ment_expanded['extended_entities']['media'][0]['video_info']['variants']:
            if ".mp4" in j['url']:
                aq = j['url']
                break
        if aq == "":
            logger.info(f"NO MP4 FOUND? OR VALID FORMAT")
            continue

        download_vid(aq)
        convert_to_mp3()

        found_song = shazamsearch()
        logger.info(f"left shazam search?")
        if found_song == "unknown":
            logger.info(f"NO MUSIC FOUND")
            continue

        sp = spo.find_song(found_song)
        api.update_status(status = ("Here is the track you looking for: "+sp), in_reply_to_status_id = mention.id, auto_populate_reply_metadata=True)
        time.sleep(30)
    return new_id


def main():
    since_id = 1
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    while True:
        logger.info("waitin on next timeline")
        since_id = handle_req(api, since_id)
        time.sleep(300)


if __name__ == "__main__":
    main()
