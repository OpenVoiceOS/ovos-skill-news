from datetime import timedelta
import feedparser
import re
from os.path import join, dirname
from pytz import timezone
from mycroft.util.time import now_local
from mycroft.util.parse import match_one
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill
from ovos_workshop.frameworks.playback import CPSMatchType, CPSPlayback, \
    CPSMatchConfidence
import requests
from youtube_searcher import extract_videos


# news uri extractors
def tsf():
    """Custom inews fetcher for TSF news."""
    feed = ('https://www.tsf.pt/stream/audio/{year}/{month:02d}/'
            'noticias/{day:02d}/not{hour:02d}.mp3')
    uri = None
    i = 0
    status = 404
    date = now_local(timezone('Portugal'))
    while status != 200 and i < 6:
        uri = feed.format(hour=date.hour, year=date.year,
                          month=date.month, day=date.day)
        status = requests.get(uri).status_code
        date -= timedelta(hours=1)
        i += 1
    if status != 200:
        return None
    return uri


def gpb():
    """Custom news fetcher for GBP news."""
    feed = 'http://feeds.feedburner.com/gpbnews/GeorgiaRSS?format=xml'
    data = feedparser.parse(feed)
    next_link = None
    for entry in data['entries']:
        # Find the first mp3 link with "GPB {time} Headlines" in title
        if 'GPB' in entry['title'] and 'Headlines' in entry['title']:
            next_link = entry['links'][0]['href']
            break
    html = requests.get(next_link)
    # Find the first mp3 link
    # Note that the latest mp3 may not be news,
    # but could be an interview, etc.
    mp3_find = re.search(r'href="(?P<mp3>.+\.mp3)"'.encode(), html.content)
    if mp3_find is None:
        return None
    url = mp3_find.group('mp3').decode('utf-8')
    return url


def abc():
    """Custom news fetcher for ABC News Australia briefing"""
    date = now_local(timezone('Australia/Sydney'))
    hour = date.strftime('%H')
    day = date.strftime('%d')
    month = date.strftime('%m')
    year = date.strftime('%Y')
    url = f"https://abcmedia.akamaized.net/news/audio/news-briefings/top" \
          f"-stories/{year}{month}/NAUs_{hour}00flash_{day}{month}_nola.mp3"
    # If this hours news is unavailable try the hour before
    response = requests.get(url)
    if response.status_code != 200:
        hour = str(int(hour) - 1)
        url = f"https://abcmedia.akamaized.net/news/audio/news-briefings/top" \
              f"-stories/{year}{month}/NAUs_{hour}00flash_{day}{month}_nola.mp3"

    return url


def npr():
    url = "https://www.npr.org/rss/podcast.php?id=500005"
    feed = extract_rss(url)
    if feed:
        return feed.split("?")[0]


def extract_rss(feed_url):
    try:
        # parse RSS or XML feed
        data = feedparser.parse(feed_url.strip())
        # After the intro, find and start the news uri
        # select the first link to an audio file

        for link in data['entries'][0]['links']:
            if 'audio' in link['type']:
                # TODO return duration for proper display in UI
                duration = link.get('length')
                return link['href']
    except Exception as e:
        pass


def extract_yt_channel(url):
    try:
        for e in extract_videos(url):
            if not e["is_live"]:
                continue
            return e["url"]
    except:
        pass


# Unified News Skill
class NewsSkill(OVOSCommonPlaybackSkill):
    # default feeds per language (optional)
    langdefaults = {
        "pt-pt": "TSF",
        "ca": "CCMA",
        "es": "RNE",
        "en-gb": "BBC",
        "en-us": "NPR",
        "fr": "France24",
        "de": "Deutsche Welle"
    }
    # all news streams for better-cps
    lang2news = {
        "en": {
            "France24 EN": {
                "aliases": ["france 24"],
                "youtube_channel": "https://www.youtube.com/channel/UCQfwfsi5VrQ8yKZ-UWmAEFg",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.VIDEO,
                                CPSMatchType.TV, CPSMatchType.NEWS],
                "playback": CPSPlayback.GUI,
                "secondary_langs": ["fr"],
                "image": join(dirname(__file__), "ui", "images", "FR24_EN.jpg")
            },
            "France24 EN (audio)": {
                "aliases": ["france 24"],
                "youtube_channel": "https://www.youtube.com/channel/UCQfwfsi5VrQ8yKZ-UWmAEFg",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS],
                "playback": CPSPlayback.AUDIO,
                "secondary_langs": ["fr"],
                "image": join(dirname(__file__), "ui", "images", "FR24_EN.jpg")
            },
            "Deutsche Welle EN": {
                "aliases": ["DW", "Deutsche Welle"],
                "youtube_channel": "https://www.youtube.com/channel/UCknLrEdhRCp1aegoMqRaCZg",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.VIDEO,
                                CPSMatchType.TV, CPSMatchType.NEWS],
                "playback": CPSPlayback.GUI,
                "image": join(dirname(__file__), "ui", "images", "DW.jpg")
            },
            "Deutsche Welle EN (audio)": {
                "aliases": ["DW", "Deutsche Welle"],
                "youtube_channel": "https://www.youtube.com/channel/UCknLrEdhRCp1aegoMqRaCZg",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS],
                "playback": CPSPlayback.AUDIO,
                "image": join(dirname(__file__), "ui", "images", "DW.jpg")
            },
            "Russia Today": {
                "aliases": ["RT", "Russia Today"],
                "youtube_channel": "https://www.youtube.com/user/RussiaToday",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.VIDEO,
                                CPSMatchType.TV, CPSMatchType.NEWS],
                "playback": CPSPlayback.GUI,
                "secondary_langs": ["ru"],
                "image": join(dirname(__file__), "ui", "images", "RT.jpg")
            },
            "Russia Today (audio)": {
                "aliases": ["RT", "Russia Today"],
                "youtube_channel": "https://www.youtube.com/user/RussiaToday",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS],
                "playback": CPSPlayback.AUDIO,
                "secondary_langs": ["ru"],
                "image": join(dirname(__file__), "ui", "images", "RT.jpg")
            }
        },
        "en-us": {
            "SkyStream": {
                "aliases": ["skyuri", "sky uri", "sky news", "skynews"],
                "uri": "https://skynews2-plutolive-vo.akamaized.net/cdhlsskynewsamericas/1013/latest.m3u8?serverSideAds=true",
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.VIDEO,
                                CPSMatchType.TV, CPSMatchType.NEWS],
                "playback": CPSPlayback.GUI,
                "media_type": CPSMatchType.NEWS,
                "image": join(dirname(__file__), "ui", "images", "skystream.png"),
                "secondary_langs": ["en"]
            },
            "SkyStream (audio)": {
                # names used for matching
                "aliases": ["skyuri", "sky uri", "sky news", "skynews"],
                # uri_extractor method or text if static
                "uri": "https://skynews2-plutolive-vo.akamaized.net/cdhlsskynewsamericas/1013/latest.m3u8?serverSideAds=true",
                # media types
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS],
                # playback types
                "playback": CPSPlayback.AUDIO,
                "media_type": CPSMatchType.NEWS,
                "image": join(dirname(__file__), "ui", "images", "skystream.png"),
                "secondary_langs": ["en"]
            },
            "TWC": {
                "aliases": ["twc", "weather channel", "the weather channel"],
                "uri": "https://weather-lh.akamaihd.net/i/twc_1@92006/master.m3u8",
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.VIDEO,
                                CPSMatchType.TV, CPSMatchType.NEWS],
                "playback": CPSPlayback.GUI,
                "media_type": CPSMatchType.NEWS,
                "image": join(dirname(__file__), "ui", "images", "twc.png"),
                "secondary_langs": ["en"]
            },
            "TWC (audio)": {
                "aliases": ["twc", "weather channel", "the weather channel"],
                "uri": "https://weather-lh.akamaihd.net/i/twc_1@92006/master.m3u8",
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS],
                "playback": CPSPlayback.AUDIO,
                "media_type": CPSMatchType.NEWS,
                "image": join(dirname(__file__), "ui", "images", "twc.png"),
                "secondary_langs": ["en"]
            },
            "GPB": {
                "aliases": ["Georgia Public Broadcasting", "GPB",
                            "Georgia Public Radio"],
                "uri": gpb,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS, CPSMatchType.RADIO],
                "playback": CPSPlayback.AUDIO,
                "media_type": CPSMatchType.NEWS,
                "image": join(dirname(__file__), "ui", "images", "gpb.png"),
                "secondary_langs": ["en"]
            },
            "AP": {
                "aliases": ["AP Hourly Radio News", "Associated Press",
                            "Associated Press News",
                            "Associated Press Radio News",
                            "Associated Press Hourly Radio News"],
                "rss_feed": "https://www.spreaker.com/show/1401466/episodes/feed",
                "uri": extract_rss,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS, CPSMatchType.RADIO],
                "image": join(dirname(__file__), "ui", "images", "AP.png"),
                "playback": CPSPlayback.AUDIO,
                "media_type": CPSMatchType.NEWS,
                "secondary_langs": ["en"]
            },
            "FOX": {
                "aliases": ["FOX News", "FOX", "Fox News Channel"],
                "rss_feed": "http://feeds.foxnewsradio.com/FoxNewsRadio",
                "uri": extract_rss,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS, CPSMatchType.RADIO],
                "playback": CPSPlayback.AUDIO,
                "media_type": CPSMatchType.NEWS,
                "image": join(dirname(__file__), "ui", "images", "FOX.png"),
                "secondary_langs": ["en"]
            },
            "NPR": {
                "aliases": ["NPR News", "NPR", "National Public Radio",
                            "National Public Radio News", "NPR News Now"],
                "uri": npr,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS, CPSMatchType.RADIO],
                "image": join(dirname(__file__), "ui", "images", "NPR.png"),
                "playback": CPSPlayback.AUDIO,
                "media_type": CPSMatchType.NEWS,
                "secondary_langs": ["en"]
            },
            "PBS": {
                "aliases": ["PBS News", "PBS", "PBS NewsHour", "PBS News Hour",
                            "National Public Broadcasting Service",
                            "Public Broadcasting Service News"],
                "rss_feed": "https://www.pbs.org/newshour/feeds/rss/podcasts/show",
                "uri": extract_rss,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS, CPSMatchType.RADIO],
                "playback": CPSPlayback.AUDIO,
                "media_type": CPSMatchType.NEWS,
                "image": join(dirname(__file__), "ui", "images", "PBS.png"),
                "secondary_langs": ["en"]
            },
            "Russia Today America": {
                "aliases": ["RT", "Russia Today", "RT America",
                            "Russia Today America"],
                "youtube_channel": "https://www.youtube.com/channel/UCczrL-2b-gYK3l4yDld4XlQ",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.VIDEO,
                                CPSMatchType.TV, CPSMatchType.NEWS],
                "playback": CPSPlayback.GUI,
                "secondary_langs": ["en", "ru"],
                "image": join(dirname(__file__), "ui", "images", "RT_US.jpg")
            },
            "Russia Today America (audio)": {
                "aliases": ["RT", "Russia Today", "RT America",
                            "Russia Today America"],
                "youtube_channel": "https://www.youtube.com/channel/UCczrL-2b-gYK3l4yDld4XlQ",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS],
                "playback": CPSPlayback.AUDIO,
                "secondary_langs": ["en", "ru"],
                "image": join(dirname(__file__), "ui", "images", "RT_US.jpg")
            }
        },
        "en-gb": {
            "BBC": {
                "aliases": ["British Broadcasting Corporation", "BBC",
                            "BBC News"],
                "rss_feed": "https://podcasts.files.bbci.co.uk/p02nq0gn.rss",
                "uri": extract_rss,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS, CPSMatchType.RADIO],
                "playback": CPSPlayback.AUDIO,
                "media_type": CPSMatchType.NEWS,
                "image": join(dirname(__file__), "ui", "images", "BBC.png"),
                "secondary_langs": ["en"]
            },
            "EuroNews": {
                "aliases": ["euro", "euronews", "Euro News", "european",
                            "european news"],
                "youtube_channel": "https://www.youtube.com/user/Euronews",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.VIDEO,
                                CPSMatchType.TV, CPSMatchType.NEWS],
                "playback": CPSPlayback.GUI,
                "image": join(dirname(__file__), "ui", "images", "euronews.png"),
                "secondary_langs": ["en"]
            },
            "EuroNews (audio)": {
                "aliases": ["euro", "euronews", "Euro News", "european",
                            "european news"],
                "youtube_channel": "https://www.youtube.com/user/euronews",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS],
                "playback": CPSPlayback.AUDIO,
                "secondary_langs": ["en"],
                "image": join(dirname(__file__), "ui", "images", "euronews.png")
            },
            "Russia Today UK": {
                "aliases": ["RT", "Russia Today", "RT UK", "Russia Today UK"],
                "youtube_channel": "https://www.youtube.com/channel/UC_ab7FFA2ACk2yTHgNan8lQ",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.VIDEO,
                                CPSMatchType.TV, CPSMatchType.NEWS],
                "playback": CPSPlayback.GUI,
                "secondary_langs": ["en", "ru"],
                "image": join(dirname(__file__), "ui", "images", "RT_UK.jpg")
            },
            "Russia Today UK (audio)": {
                "aliases": ["RT", "Russia Today", "RT UK", "Russia Today UK"],
                "youtube_channel": "https://www.youtube.com/channel/UC_ab7FFA2ACk2yTHgNan8lQ",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS],
                "playback": CPSPlayback.AUDIO,
                "secondary_langs": ["en", "ru"],
                "image": join(dirname(__file__), "ui", "images", "RT_UK.jpg")
            }
        },
        "en-au": {
            "ABC": {
                "aliases": ["ABC News Australia", "ABC News", "ABC"],
                "uri": abc,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS, CPSMatchType.RADIO],
                "playback": CPSPlayback.AUDIO,
                "media_type": CPSMatchType.NEWS,
                "image": join(dirname(__file__), "ui", "images", "ABC.png"),
                "secondary_langs": ["en"]
            }
        },
        "en-ca": {
            "CBC": {
                "aliases": ["Canadian Broadcasting Corporation", "CBC",
                            "CBC News"],
                "uri": extract_rss,
                "rss_feed": "https://www.cbc.ca/podcasting/includes/hourlynews.xml",
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS, CPSMatchType.RADIO],
                "playback": CPSPlayback.AUDIO,
                "media_type": CPSMatchType.NEWS,
                "image": join(dirname(__file__), "ui", "images", "CBC.png"),
                "secondary_langs": ["en"]
            }
        },
        "pt-pt": {
            "TSF": {
                "aliases": ["TSF", "TSF Rádio Notícias", "TSF Notícias"],
                "uri": tsf,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS, CPSMatchType.RADIO],
                "playback": CPSPlayback.AUDIO,
                "image": join(dirname(__file__), "ui", "images", "tsf.png"),
                "secondary_langs": ["pt"]
            },
            "RDP-AFRICA": {
                "aliases": ["RDP", "RDP Africa", "Noticiários RDP África"],
                "uri": "http://www.rtp.pt//play/itunes/5442",
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS, CPSMatchType.RADIO],
                "playback": CPSPlayback.AUDIO,
                "image": join(dirname(__file__), "ui", "images", "rdp_africa.png"),
                "secondary_langs": ["pt"]
            },
            "EuroNews PT": {
                "aliases": ["euro", "euronews", "Euro News", "european",
                            "european news"],
                "youtube_channel": "https://www.youtube.com/user/euronewspt",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.VIDEO,
                                CPSMatchType.TV, CPSMatchType.NEWS],
                "playback": CPSPlayback.GUI,
                "image": join(dirname(__file__), "ui", "images", "euronews.png"),
                "secondary_langs": ["pt"]
            },
            "EuroNews PT (audio)": {
                "aliases": ["euro", "euronews", "Euro News", "european",
                            "european news"],
                "youtube_channel": "https://www.youtube.com/user/euronewspt",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS],
                "playback": CPSPlayback.AUDIO,
                "secondary_langs": ["pt"],
                "image": join(dirname(__file__), "ui", "images", "euronews.png")
            }
        },
        "de": {
            "Deutsche Welle": {
                "aliases": ["DW", "Deutsche Welle"],
                "youtube_channel": "https://www.youtube.com/c/dwdeutsch",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.VIDEO,
                                CPSMatchType.TV, CPSMatchType.NEWS],
                "playback": CPSPlayback.GUI,
                "image": join(dirname(__file__), "ui", "images", "DW.jpg")
            },
            "Deutsche Welle (audio)": {
                "aliases": ["DW", "Deutsche Welle"],
                "youtube_channel": "https://www.youtube.com/c/dwdeutsch",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS],
                "playback": CPSPlayback.AUDIO,
                "image": join(dirname(__file__), "ui", "images", "DW.jpg")
            },
            "OE3": {
                "aliases": ["OE3", "Ö3 Nachrichten"],
                "uri": "https://oe3meta.orf.at/oe3mdata/StaticAudio/Nachrichten.mp3",
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS, CPSMatchType.RADIO],
                "image": join(dirname(__file__), "ui", "images", "oe3.jpeg"),
                 "playback": CPSPlayback.AUDIO
            },
            "DLF": {
                "aliases": ["DLF", "deutschlandfunk"],
                "rss_feed": "https://www.deutschlandfunk.de/podcast-nachrichten.1257.de.podcast.xml",
                "uri": extract_rss,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS, CPSMatchType.RADIO],
                "image": join(dirname(__file__), "ui", "images", "DLF.png"),
                 "playback": CPSPlayback.AUDIO
            },
            "WDR": {
                "aliases": ["WDR"],
                "uri": "https://www1.wdr.de/mediathek/audio/wdr-aktuell-news/wdr-aktuell-152.podcast",
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS, CPSMatchType.RADIO],
                "image": join(dirname(__file__), "ui", "images", "WDR.png"),
                 "playback": CPSPlayback.AUDIO
            },
            "EuroNews DE": {
                "aliases": ["euro", "euronews", "Euro News", "european",
                            "european news"],
                "youtube_channel": "https://www.youtube.com/user/euronewsde",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.VIDEO,
                                CPSMatchType.TV, CPSMatchType.NEWS],
                "playback": CPSPlayback.GUI,
                "image": join(dirname(__file__), "ui", "images", "euronews.png")
            },
            "EuroNews DE (audio)": {
                "aliases": ["euro", "euronews", "Euro News", "european",
                            "european news"],
                "youtube_channel": "https://www.youtube.com/user/euronewsde",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS],
                "playback": CPSPlayback.AUDIO,
                "image": join(dirname(__file__), "ui", "images", "euronews.png")
            }
        },
        "nl": {
            "VRT": {
                "aliases": ["VRT Nieuws", "VRT"],
                "uri": "https://progressive-audio.lwc.vrtcdn.be/content/fixed/11_11niws-snip_hi.mp3",
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS, CPSMatchType.RADIO],
                "image": join(dirname(__file__), "ui", "images", "vrt.png"),
                 "playback": CPSPlayback.AUDIO
            }
        },
        "sv": {
            "Ekot": {
                "aliases": ["Ekot"],
                "rss_feed": "https://api.sr.se/api/rss/pod/3795",
                "uri": extract_rss,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS, CPSMatchType.RADIO],
                "image": join(dirname(__file__), "ui", "images", "Ekot.png"),
                 "playback": CPSPlayback.AUDIO
            }
        },
        "es": {
            "RNE": {
                "aliases": ["RNE", "National Spanish Radio",
                            "Radio Nacional de España"],
                "uri": extract_rss,
                "media_type": CPSMatchType.NEWS,
                "rss_feed": "http://api.rtve.es/api/programas/36019/audios.rs",
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS, CPSMatchType.RADIO],
                "image": join(dirname(__file__), "ui", "images", "rne.png"),
                "playback": CPSPlayback.AUDIO
            },
            "France24 ES": {
                "aliases": ["france 24"],
                "youtube_channel": "https://www.youtube.com/channel/UCUdOoVWuWmgo1wByzcsyKDQ",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.VIDEO,
                                CPSMatchType.TV, CPSMatchType.NEWS],
                "playback": CPSPlayback.GUI,
                "secondary_langs": ["fr"],
                "image": join(dirname(__file__), "ui", "images", "FR24_ES.jpg")
            },
            "France24 ES (audio)": {
                "aliases": ["france 24"],
                "youtube_channel": "https://www.youtube.com/channel/UCUdOoVWuWmgo1wByzcsyKDQ",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS],
                "playback": CPSPlayback.AUDIO,
                "secondary_langs": ["fr"],
                "image": join(dirname(__file__), "ui", "images", "FR24_ES.jpg")
            },
            "EuroNews ES": {
                "aliases": ["euro", "euronews", "Euro News", "european",
                            "european news"],
                "youtube_channel": "https://www.youtube.com/user/euronewses",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.VIDEO,
                                CPSMatchType.TV, CPSMatchType.NEWS],
                "playback": CPSPlayback.GUI,
                "image": join(dirname(__file__), "ui", "images", "euronews.png")
            },
            "EuroNews ES (audio)": {
                "aliases": ["euro", "euronews", "Euro News", "european",
                            "european news"],
                "youtube_channel": "https://www.youtube.com/user/euronewses",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS],
                "playback": CPSPlayback.AUDIO,
                "image": join(dirname(__file__), "ui", "images", "euronews.png")
            },
            "Deutsche Welle ES": {
                "aliases": ["DW", "Deutsche Welle"],
                "youtube_channel": "https://www.youtube.com/channel/UCT4Jg8h03dD0iN3Pb5L0PMA",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.VIDEO,
                                CPSMatchType.TV, CPSMatchType.NEWS],
                "playback": CPSPlayback.GUI,
                "image": join(dirname(__file__), "ui", "images", "DW.jpg")
            },
            "Deutsche Welle ES (audio)": {
                "aliases": ["DW", "Deutsche Welle"],
                "youtube_channel": "https://www.youtube.com/channel/UCT4Jg8h03dD0iN3Pb5L0PMA",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS],
                "playback": CPSPlayback.AUDIO,
                "image": join(dirname(__file__), "ui", "images", "DW.jpg")
            }
        },
        "ca": {
            "CCMA": {
                "aliases": ["CCMA", "Catalunya Informació"],
                "uri": "https://de1.api.radio-browser.info/pls/url/69bc7084-523c-11ea-be63-52543be04c81",
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS, CPSMatchType.RADIO],
                "playback": CPSPlayback.AUDIO,
                "image": join(dirname(__file__), "ui", "images", "CCMA.png"),
                "secondary_langs": ["es"]
            }
        },
        "fi": {
            "YLE": {
                "aliases": ["YLE", "YLE News Radio"],
                "rss_feed": "https://feeds.yle.fi/areena/v1/series/1-1440981.rss",
                "uri": extract_rss,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS, CPSMatchType.RADIO],
                "image": join(dirname(__file__), "ui", "images", "Yle.png"),
                "playback": CPSPlayback.AUDIO
            }
        },
        "ru": {
            "EuroNews RU": {
                "aliases": ["euro", "euronews", "Euro News", "european",
                            "european news"],
                "youtube_channel": "https://www.youtube.com/user/euronewsru",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.VIDEO,
                                CPSMatchType.TV, CPSMatchType.NEWS],
                "playback": CPSPlayback.GUI,
                "image": join(dirname(__file__), "ui", "images", "euronews.png")
            },
            "EuroNews RU (audio)": {
                "aliases": ["euro", "euronews", "Euro News", "european",
                            "european news"],
                "youtube_channel": "https://www.youtube.com/user/euronewsru",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS],
                "playback": CPSPlayback.AUDIO,
                "image": join(dirname(__file__), "ui", "images", "euronews.png")
            }
        },
        "it": {
            "EuroNews IT": {
                "aliases": ["euro", "euronews", "Euro News", "european",
                            "european news"],
                "youtube_channel": "https://www.youtube.com/user/euronewsit",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.VIDEO,
                                CPSMatchType.TV, CPSMatchType.NEWS],
                "playback": CPSPlayback.GUI,
                "image": join(dirname(__file__), "ui", "images", "euronews.png")
            },
            "EuroNews IT (audio)": {
                "aliases": ["euro", "euronews", "Euro News", "european",
                            "european news"],
                "youtube_channel": "https://www.youtube.com/user/euronewsit",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS],
                "playback": CPSPlayback.AUDIO,
                "image": join(dirname(__file__), "ui", "images", "euronews.png")
            }
        },
        "fr": {
            "France24": {
                "aliases": ["france 24"],
                "youtube_channel": "https://www.youtube.com/channel/UCCCPCZNChQdGa9EkATeye4g",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.VIDEO,
                                CPSMatchType.TV, CPSMatchType.NEWS],
                "playback": CPSPlayback.GUI,
                "image": join(dirname(__file__), "ui", "images", "FR24.jpg")
            },
            "France24 (audio)": {
                "aliases": ["france 24"],
                "youtube_channel": "https://www.youtube.com/channel/UCCCPCZNChQdGa9EkATeye4g",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS],
                "playback": CPSPlayback.AUDIO,
                "image": join(dirname(__file__), "ui", "images", "FR24.jpg")
            },
            "EuroNews FR": {
                "aliases": ["euro", "euronews", "Euro News", "european",
                            "european news"],
                "youtube_channel": "https://www.youtube.com/user/euronewsft",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.VIDEO,
                                CPSMatchType.TV, CPSMatchType.NEWS],
                "playback": CPSPlayback.GUI,
                "image": join(dirname(__file__), "ui", "images", "euronews.png")
            },
            "EuroNews FR (audio)": {
                "aliases": ["euro", "euronews", "Euro News", "european",
                            "european news"],
                "youtube_channel": "https://www.youtube.com/user/euronewsft",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS],
                "playback": CPSPlayback.AUDIO,
                "image": join(dirname(__file__), "ui", "images", "euronews.png")
            },
            "Russia Today France": {
                "aliases": ["RT", "Russia Today"],
                "youtube_channel": "https://www.youtube.com/channel/UCqEVwTnDzlzKOGYNFemqnYA",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.VIDEO,
                                CPSMatchType.TV, CPSMatchType.NEWS],
                "playback": CPSPlayback.GUI,
                "secondary_langs": ["ru"],
                "image": join(dirname(__file__), "ui", "images", "RT_FR.jpg")
            },
            "Russia Today France (audio)": {
                "aliases": ["RT", "Russia Today"],
                "youtube_channel": "https://www.youtube.com/channel/UCqEVwTnDzlzKOGYNFemqnYA",
                "uri": extract_yt_channel,
                "media_type": CPSMatchType.NEWS,
                "match_types": [CPSMatchType.GENERIC, CPSMatchType.AUDIO,
                                CPSMatchType.NEWS],
                "playback": CPSPlayback.AUDIO,
                "secondary_langs": ["ru"],
                "image": join(dirname(__file__), "ui", "images", "RT_FR.jpg")
            }
        }
    }

    def __init__(self):
        super().__init__("News")
        self.supported_media = [CPSMatchType.GENERIC,
                                CPSMatchType.AUDIO,
                                CPSMatchType.VIDEO,
                                CPSMatchType.TV,
                                CPSMatchType.RADIO,
                                CPSMatchType.NEWS]
        self.skill_icon = join(dirname(__file__), "ui", "news.png")
        self.default_bg = join(dirname(__file__), "ui", "bg.jpg")

    def get_intro_message(self):
        self.speak_dialog("intro")

    # common play
    def clean_phrase(self, phrase):
        phrase = self.remove_voc(phrase, "news")

        # special handling for channel name
        # these channels include language .voc in their names, do not
        # cleanup the phrase to improve matching
        if not self.voc_match(phrase, "fr24") \
            and not self.voc_match(phrase, "rt"):

            phrase = self.remove_voc(phrase, "pt-pt")
            phrase = self.remove_voc(phrase, "en-au")
            phrase = self.remove_voc(phrase, "en-us")
            phrase = self.remove_voc(phrase, "en-ca")
            phrase = self.remove_voc(phrase, "en-gb")
            phrase = self.remove_voc(phrase, "es")
            phrase = self.remove_voc(phrase, "it")
            phrase = self.remove_voc(phrase, "fi")
            phrase = self.remove_voc(phrase, "de")
            phrase = self.remove_voc(phrase, "sv")
            phrase = self.remove_voc(phrase, "nl")
            phrase = self.remove_voc(phrase, "en")
            phrase = self.remove_voc(phrase, "ca")

        return phrase.strip()

    def match_lang(self, phrase):
        langs = []
        if self.voc_match(phrase, "pt-pt"):
            langs.append("pt-pt")
        if self.voc_match(phrase, "en-au"):
            langs.append("en-au")
        if self.voc_match(phrase, "en-us"):
            langs.append("en-us")
        if self.voc_match(phrase, "en-gb"):
            langs.append("en-gb")
        if self.voc_match(phrase, "en-ca"):
            langs.append("en-ca")
        if self.voc_match(phrase, "en"):
            langs.append("en")
        if self.voc_match(phrase, "es"):
            langs.append("es")
        if self.voc_match(phrase, "ca"):
            langs.append("ca")
        if self.voc_match(phrase, "de"):
            langs.append("de")
        if self.voc_match(phrase, "nl"):
            langs.append("nl")
        if self.voc_match(phrase, "fi"):
            langs.append("fi")
        if self.voc_match(phrase, "sv"):
            langs.append("sv")
        if self.voc_match(phrase, "it"):
            langs.append("it")

        # special handling for channel name
        # these channels include streams for other languages which should
        # be selected according to the mycroft.conf instead
        if self.voc_match(phrase, "fr") and \
                not self.voc_match(phrase, "fr24"):
            langs.append("fr")
        if self.voc_match(phrase, "ru") and \
                not self.voc_match(phrase, "rt"):
            langs.append("ru")

        langs += [l.split("-")[0] for l in langs]
        return langs

    def CPS_search(self, phrase, media_type):
        """Analyze phrase to see if it is a play-able phrase with this skill.

        Arguments:
            phrase (str): User phrase uttered after "Play", e.g. "some music"
            media_type (CPSMatchType): requested CPSMatchType to search for

        Returns:
            search_results (list): list of dictionaries with result entries
            {
                "match_confidence": CPSMatchConfidence.HIGH,
                "media_type":  CPSMatchType.MUSIC,
                "uri": "https://audioservice.or.gui.will.play.this",
                "playback": CPSPlayback.GUI,
                "image": "http://optional.audioservice.jpg",
                "bg_image": "http://optional.audioservice.background.jpg"
            }
        """
        # requested language
        langs = self.match_lang(phrase) or []

        # base score
        score = 0
        if media_type == CPSMatchType.NEWS or self.voc_match(phrase, "news")  \
                or self.voc_match(phrase, "euronews"):
            score = 50
            # youtube matches take a little longer to extract the streams
            self.CPS_extend_timeout(1)
        # score penalty if media_type is vague
        elif media_type == CPSMatchType.GENERIC or \
                media_type == CPSMatchType.VIDEO:
            score -= 30
        elif media_type == CPSMatchType.RADIO:
            score -= 20

        phrase = self.clean_phrase(phrase)

        # default feed (gets score bonus)
        default_feeds = []

        if not phrase:
            # "play {lang} news"
            for lang in langs:
                # choose default feed for requested language
                if lang in self.langdefaults:
                    feed = self.langdefaults[lang]
                    if feed:
                        default_feeds.append(feed)
            if not langs:
                # "play the news" -> no feed requested
                # play user preference if set in skill settings
                feed = self.settings.get("default_feed")
                if feed:
                    default_feeds.append(feed)

        # score individual results
        candidates = []
        langs = langs or [self.lang, self.lang.split("-")[0]]
        for l in self.lang2news:
            for k, v in self.lang2news[l].items():
                # match name
                _, alias_score = match_one(phrase, v["aliases"])
                v["match_confidence"] = score + alias_score * 60

                # match languages
                if l in langs:
                    v["match_confidence"] += 20  # lang bonus
                elif any([lang in v.get("secondary_langs", [])
                          for lang in langs]):
                    v["match_confidence"] += 10  # smaller lang bonus
                else:
                    v["match_confidence"] -= 20  # wrong language penalty

                # match media type
                if media_type not in v["match_types"]:
                    # filter audio / video if explicitly asked one or the other
                    v["match_confidence"] = 0

                # favour GUI results over audio only
                # meant to influence only matches that provide both options
                if v["playback"] == CPSPlayback.GUI and\
                        media_type not in [CPSMatchType.AUDIO, CPSMatchType.RADIO]:
                    v["match_confidence"] += 5

                # default news feed gets a nice bonus
                # only happens if phrase doesnt really contain a query
                if k in default_feeds:
                    v["match_confidence"] += 30

                # final score
                v["match_confidence"] = min([v["match_confidence"], 100])

                if v["match_confidence"] >= CPSMatchConfidence.AVERAGE:
                    if callable(v["uri"]):
                        if v.get("rss_feed"):
                            v["uri"] = v["uri"](v["rss_feed"])
                        elif v.get("youtube_channel"):
                            v["uri"] = v["uri"](v["youtube_channel"])
                        else:
                            v["uri"] = v["uri"]()

                    if v["uri"]:
                        v["title"] = v.get("title") or k
                        v["bg_image"] = v.get("bg_image") or self.default_bg
                        v["skill_logo"] = self.skill_icon
                        candidates.append(v)

        return candidates


def create_skill():
    return NewsSkill()
