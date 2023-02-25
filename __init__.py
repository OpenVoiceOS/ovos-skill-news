from os.path import join, dirname

from ovos_plugin_common_play.ocp import MediaType, PlaybackType, \
    MatchConfidence
from ovos_utils.parse import match_one, MatchStrategy
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill, \
    ocp_search, ocp_featured_media
from ovos_utils.process_utils import RuntimeRequirements
from ovos_utils import classproperty


# Unified News Skill
class NewsSkill(OVOSCommonPlaybackSkill):
    # default feeds per language (optional)
    langdefaults = {
        "pt-pt": "TSF",
        "es-es": "RNE",
        "ca-es": "CCMA",
        "en-gb": "BBC",
        "en-us": "NPR",
        "en-au": "ABC",
        "en-ca": "CBC",
        "it-it": "GR1",
        "de-de": "DLF - Die Nachrichten"
    }
    # all news streams
    lang2news = {
        "en-us": {
            "GT": {
                "aliases": ["Georgia Today"],
                "uri": "news//https://www.gpb.org/radio/programs/georgia-today",
                "match_types": [MediaType.NEWS],
                "playback": PlaybackType.AUDIO,
                "media_type": MediaType.NEWS,
                "image": join(dirname(__file__), "ui", "images", "gpb.png"),
                "secondary_langs": ["en"]
            },
            "AP": {
                "aliases": ["AP Hourly Radio News", "Associated Press",
                            "Associated Press News",
                            "Associated Press Radio News",
                            "Associated Press Hourly Radio News"],
                "uri": "rss//https://www.spreaker.com/show/1401466/episodes/feed",
                "match_types": [MediaType.NEWS],
                "image": join(dirname(__file__), "ui", "images", "AP.png"),
                "playback": PlaybackType.AUDIO,
                "media_type": MediaType.NEWS,
                "secondary_langs": ["en"]
            },
            "FOX": {
                "aliases": ["FOX News", "FOX", "Fox News Channel"],
                "uri": "rss//http://feeds.foxnewsradio.com/FoxNewsRadio",
                "match_types": [MediaType.NEWS],
                "playback": PlaybackType.AUDIO,
                "media_type": MediaType.NEWS,
                "image": join(dirname(__file__), "ui", "images", "FOX.png"),
                "secondary_langs": ["en"]
            },
            "NPR": {
                "aliases": ["NPR News", "NPR", "National Public Radio",
                            "National Public Radio News", "NPR News Now"],
                "uri": "news//https://www.npr.org/podcasts/500005/npr-news-now",
                "match_types": [MediaType.NEWS],
                "image": "https://media.npr.org/assets/img/2018/08/06/nprnewsnow_podcasttile_sq.webp",
                "playback": PlaybackType.AUDIO,
                "media_type": MediaType.NEWS,
                "secondary_langs": ["en"]
            },
            "PBS": {
                "aliases": ["PBS News", "PBS", "PBS NewsHour", "PBS News Hour",
                            "National Public Broadcasting Service",
                            "Public Broadcasting Service News"],
                "uri": "rss//https://www.pbs.org/newshour/feeds/rss/podcasts/show",
                "match_types": [MediaType.NEWS],
                "playback": PlaybackType.AUDIO,
                "media_type": MediaType.NEWS,
                "image": join(dirname(__file__), "ui", "images", "PBS.png"),
                "secondary_langs": ["en"]
            },
            "FT": {
                "aliases": ["Financial Times", "FT", "FT News Briefing"],
                "uri": "news//https://www.ft.com",
                "match_types": [MediaType.NEWS],
                "playback": PlaybackType.AUDIO,
                "media_type": MediaType.NEWS,
                "image": join(dirname(__file__), "ui", "images", "FT.png"),
                "secondary_langs": ["en"]
            },
            "AN": {
                "aliases": ["Alaska Nightly", "Alaska News Nightly"],
                "uri": "news//https://www.npr.org/podcasts/828054805/alaska-news-nightly",
                "match_types": [MediaType.NEWS],
                "playback": PlaybackType.AUDIO,
                "media_type": MediaType.NEWS,
                "image": "https://media.npr.org/images/podcasts/primary/icon_828054805-1ce50401d43f15660a36275a8bf2ff454de62b2f.png",
                "secondary_langs": ["en"]
            },
            "KBBI": {
                "aliases": ["KBBI Newscast", "KBBI News", "KBBI"],
                "uri": "news//https://www.npr.org/podcasts/1052142404/k-b-b-i-newscast",
                "match_types": [MediaType.NEWS],
                "playback": PlaybackType.AUDIO,
                "media_type": MediaType.NEWS,
                "image": "https://media.npr.org/images/podcasts/primary/icon_1052142404-2839f62f7db7bf2ec753fca56913bd7a1b52c428.png",
                "secondary_langs": ["en"]
            },
            "ASPEN": {
                "aliases": ["Aspen Public Radio Newscast",
                            "Aspen Public Radio News",
                            "Aspen Public Radio",
                            "Aspen News"],
                "uri": "news//https://www.npr.org/podcasts/1100476310/aspen-public-radio-newscast",
                "match_types": [MediaType.NEWS],
                "playback": PlaybackType.AUDIO,
                "media_type": MediaType.NEWS,
                "image": "https://media.npr.org/images/podcasts/primary/icon_1100476310-9b43c8bf959de6d90a5f59c58dc82ebc7b9b9258.png",
                "secondary_langs": ["en"]
            },
            "SFN": {
                "aliases": ["First News", "KRCB", "Sonoma News"],
                "uri": "news//https://www.npr.org/podcasts/1090302835/first-news",
                "match_types": [MediaType.NEWS],
                "playback": PlaybackType.AUDIO,
                "media_type": MediaType.NEWS,
                "image": "https://media.npr.org/images/podcasts/primary/icon_1090302835-6b593e71a8d60b373ec735479dfbdd9e7f2e8cfe.png",
                "secondary_langs": ["en"]
            },
            "NHNR": {
                "aliases": ["N.H. News Recap",
                            "New Hampshire Public Radio",
                            "New Hampshire News"],
                "uri": "news//https://www.npr.org/podcasts/1071428476/n-h-news-recap",
                "match_types": [MediaType.NEWS],
                "playback": PlaybackType.AUDIO,
                "media_type": MediaType.NEWS,
                "image": "https://media.npr.org/images/podcasts/primary/icon_1071428476-7bd7627d52d6c3fc7082a1524b1b10a49dde7444.png",
                "secondary_langs": ["en"]
            },
            "NSPR": {
                "aliases": ["NSPR Headlines",
                            "North State News",
                            "North State Public Radio"],
                "uri": "news//https://www.npr.org/podcasts/1074915520/n-s-p-r-headlines",
                "match_types": [MediaType.NEWS],
                "playback": PlaybackType.AUDIO,
                "media_type": MediaType.NEWS,
                "image": "https://media.npr.org/images/podcasts/primary/icon_1074915520-8d70ce2af1d6db7fab8a42a9b4eb55dddb6eb69a.png",
                "secondary_langs": ["en"]
            },
            "WSIU": {
                "aliases": ["WSIU News", "WSIU Public Radio"],
                "uri": "news//https://www.npr.org/podcasts/1038076755/w-s-i-u-news-updates",
                "match_types": [MediaType.NEWS],
                "playback": PlaybackType.AUDIO,
                "media_type": MediaType.NEWS,
                "image": "https://media.npr.org/images/podcasts/primary/icon_1038076755-aa4101ea9d54395c83b03d7dc7ac823047682192.jpg",
                "secondary_langs": ["en"]
            },
            "SDPB": {
                "aliases": ["SDPB", "SDPB News"],
                "uri": "news//https://www.npr.org/podcasts/1031233995/s-d-p-b-news",
                "match_types": [MediaType.NEWS],
                "playback": PlaybackType.AUDIO,
                "media_type": MediaType.NEWS,
                "image": "https://media.npr.org/images/podcasts/primary/icon_1031233995-ae5c8fd4e932033b3b8e079cdc133703c2ef427c.jpg",
                "secondary_langs": ["en"]
            },
            "KVCR": {
                "aliases": ["Midday News", "KVCR News",
                            "The Midday News Report"],
                "uri": "news//https://www.npr.org/podcasts/1033362253/the-midday-news-report",
                "match_types": [MediaType.NEWS],
                "playback": PlaybackType.AUDIO,
                "media_type": MediaType.NEWS,
                "image": "https://media.npr.org/images/podcasts/primary/icon_1033362253-566d4a69caee465ebe1adf7d2949ae0c745e97b8.png",
                "secondary_langs": ["en"]
            },
            "KHNS": {
                "aliases": ["KHNS-FM Local News",
                            "KHN News"],
                "uri": "news//https://www.npr.org/podcasts/381444103/k-h-n-s-f-m-local-news",
                "match_types": [MediaType.NEWS],
                "playback": PlaybackType.AUDIO,
                "media_type": MediaType.NEWS,
                "image": "https://media.npr.org/images/podcasts/primary/icon_1111549375-c22ef178b4a5db87547aeb4c3c14dc8a8b1bc462.png",
                "secondary_langs": ["en"]
            },
            "KGOU_AM": {
                "aliases": ["KGOU AM NewsBrief",
                            "KGOU Morning News"],
                "uri": "news//https://www.npr.org/podcasts/1111549080/k-g-o-u-a-m-news-brief",
                "match_types": [MediaType.NEWS],
                "playback": PlaybackType.AUDIO,
                "media_type": MediaType.NEWS,
                "image": "https://media.npr.org/images/podcasts/primary/icon_1111549080-ebbfb83b98c966f38237d3e6ed729d659d098cb9.png",
                "secondary_langs": ["en"]
            },
            "KGOU_PM": {
                "aliases": ["KGOU PM NewsBrief",
                            "KGOU Evening News"],
                "uri": "news//https://www.npr.org/podcasts/1111549375/k-g-o-u-p-m-news-brief",
                "match_types": [MediaType.NEWS],
                "playback": PlaybackType.AUDIO,
                "media_type": MediaType.NEWS,
                "image": "https://media.npr.org/images/podcasts/primary/icon_1111549375-c22ef178b4a5db87547aeb4c3c14dc8a8b1bc462.png",
                "secondary_langs": ["en"]
            }
        },
        "en-gb": {
            "BBC": {
                "aliases": ["British Broadcasting Corporation", "BBC",
                            "BBC News"],
                "uri": "rss//https://podcasts.files.bbci.co.uk/p02nq0gn.rss",
                "match_types": [MediaType.NEWS],
                "playback": PlaybackType.AUDIO,
                "media_type": MediaType.NEWS,
                "image": join(dirname(__file__), "ui", "images", "BBC.png"),
                "secondary_langs": ["en"]
            },
            "SN": {
                "aliases": ["Sky News"],
                "uri": "http://video.news.sky.com/snr/news/snrnews.mp3",
                "match_types": [MediaType.NEWS],
                "playback": PlaybackType.AUDIO,
                "media_type": MediaType.NEWS,
                "image": join(dirname(__file__), "ui", "images", "sky-news-logo.svg"),
                "secondary_langs": ["en"]
            }
        },
        "en-ca": {
            "CBC": {
                "aliases": ["Canadian Broadcasting Corporation", "CBC",
                            "CBC News"],
                "uri": "rss//https://www.cbc.ca/podcasting/includes/hourlynews.xml",
                "match_types": [MediaType.NEWS],
                "playback": PlaybackType.AUDIO,
                "media_type": MediaType.NEWS,
                "image": join(dirname(__file__), "ui", "images", "CBC.png"),
                "secondary_langs": ["en"]
            }
        },
        "en-au": {
            "ABC": {
                "aliases": ["Australian Broadcasting Corporation", "ABC",
                            "ABC News"],
                "uri": "news//https://www.abc.net.au/news",
                "match_types": [MediaType.NEWS],
                "playback": PlaybackType.AUDIO,
                "media_type": MediaType.NEWS,
                "image": join(dirname(__file__), "ui", "images", "ABC.png"),
                "secondary_langs": ["en"]
            }
        },
        "pt-pt": {
            "TSF": {
                "aliases": ["TSF", "TSF Rádio Notícias", "TSF Notícias"],
                "uri": "news//https://www.tsf.pt/stream",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS],
                "playback": PlaybackType.AUDIO,
                "image": join(dirname(__file__), "ui", "images", "tsf.png"),
                "secondary_langs": ["pt"]
            },
            "RTP": {
                "aliases": ["RTP", "Antena 1", "Noticiario Nacional"],
                "uri": "rss//http://www.rtp.pt/play/itunes/7496",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS],
                "playback": PlaybackType.AUDIO,
                "image": join(dirname(__file__), "ui", "images", "RTP_1.png"),
                "secondary_langs": ["pt"]
            },
            "RDP": {
                "aliases": ["RDP", "RDP Africa"],
                "uri": "rss//http://www.rtp.pt/play/itunes/5442",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS],
                "playback": PlaybackType.AUDIO,
                "image": join(dirname(__file__), "ui", "images", "RDP.png"),
                "secondary_langs": ["pt"]
            }
        },
        "de-de": {
            "DLF - Die Nachrichten": {
                "aliases": ["DLF", "deutschlandfunk"],
                "uri": "rss//https://www.deutschlandfunk.de/podcast-nachrichten.1257.de.podcast.xml",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS],
                "image": join(dirname(__file__), "ui", "images", "DLF.png"),
                "playback": PlaybackType.AUDIO
            },
            "DLF - Der Tag": {
                "aliases": ["DLF der tag", "D L F der tag", "deutschlandfunk der tag"],
                "uri": "rss//https://www.deutschlandfunk.de/podcast-104.xml",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS],
                "image": join(dirname(__file__), "ui", "images", "DLF_DT.png"),
                "playback": PlaybackType.AUDIO
            },
            "DLF - Hintergrund": {
                "aliases": ["DLF hintergrund", "D L F hintergrund", "deutschlandfunk hintergrund"],
                "uri": "rss//https://www.deutschlandfunk.de/hintergrund-102.xml",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS],
                "image": join(dirname(__file__), "ui", "images", "DLF_HG.jpeg"),
                "playback": PlaybackType.AUDIO
            },
            "ARD - Tagesschau": {
                "aliases": ["ARD", "A R D", "tagesschau"],
                "uri": "rss//https://www.tagesschau.de/export/podcast/tagesschau_https/",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS],
                "image": join(dirname(__file__), "ui", "images", "ARD_TS.jpg"),
                "playback": PlaybackType.AUDIO
            },
            "ARD - Tagesschau (Kurzfassung)": {
                "aliases": ["tagesschau kurzfassung"],
                "uri": "rss//https://www.tagesschau.de/export/podcast/hi/tagesschau-in-100-sekunden/",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS],
                "image": join(dirname(__file__), "ui", "images", "ARD_TS.jpg"),
                "playback": PlaybackType.AUDIO
            },
            "ARD - Tagesschau (vor 20 Jahren)": {
                "aliases": ["tagesschau vor 20 jahren", "tagesschau damals", "tagesschau früher", "vor 20 jahren"],
                "uri": "rss//https://www.tagesschau.de/export/podcast/tagesschau-vor-20-jahren_https/",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS],
                "image": join(dirname(__file__), "ui", "images", "ARD_TS20.jpg"),
                "playback": PlaybackType.AUDIO
            },
            "ARD - Tagesthemen": {
                "aliases": ["ARD tagesthemen", "tagesthemen"],
                "uri": "rss//https://www.tagesschau.de/export/podcast/tagesthemen_https/",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS],
                "image": join(dirname(__file__), "ui", "images", "ARD_TT.jpeg"),
                "playback": PlaybackType.AUDIO
            },
            "ARD - Nachtmagazin": {
                "aliases": ["ARD nachtmagazin", "nachtmagazin"],
                "uri": "rss//https://www.tagesschau.de/export/podcast/nachtmagazin_https/",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS],
                "image": join(dirname(__file__), "ui", "images", "ARD_NM.jpg"),
                "playback": PlaybackType.AUDIO
            },
            "HRI": {
                "aliases": ["HRI", "hr Info", "hessenschau", "hessen", "hessische"],
                "uri": "rss//https://podcast.hr.de/der_tag_in_hessen/podcast.xml",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS],
                "image": join(dirname(__file__), "ui", "images", "HRI.png"),
                "playback": PlaybackType.AUDIO
            },
            "NDR": {
                "aliases": ["NDR", "N D R", "ndr info", "norddeutscher rundfunk", "norddeutschland", "norddeutsche"],
                "uri": "rss//https://www.ndr.de/nachrichten/info/podcast4370.xml",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS],
                "image": join(dirname(__file__), "ui", "images", "NDR.png"),
                "playback": PlaybackType.AUDIO
            },
            "FAZ - Frühdenker": {
                "aliases": ["FAZ frühdenker", "frankfurter allgemeine", "frühdenker"],
                "uri": "rss//https://fazfruehdenker.podigee.io/feed/mp3",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS, MediaType.PODCAST],
                "image": join(dirname(__file__), "ui", "images", "FAZ_FD.jpeg"),
                "playback": PlaybackType.AUDIO
            },
            "SZ - Auf den Punkt": {
                "aliases": ["SZ", "S Z", "süddeutsche zeitung", "auf den punkt"],
                "uri": "rss//https://sz-auf-den-punkt.podigee.io/feed/mp3",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS, MediaType.PODCAST],
                "image": join(dirname(__file__), "ui", "images", "SZ.jpeg"),
                "playback": PlaybackType.AUDIO
            },
            "Die Zeit - Was jetzt": {
                "aliases": ["die zeit", "zeit", "zeit online", "was jetzt"],
                "uri": "rss//https://wasjetzt.podigee.io/feed/mp3",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS, MediaType.PODCAST],
                "image": join(dirname(__file__), "ui", "images", "ZEIT.png"),
                "playback": PlaybackType.AUDIO
            },
            "Lage der Nation": {
                "aliases": ["lage der nation", "die lage der nation"],
                "uri": "rss//https://feeds.lagedernation.org/feeds/ldn-mp3.xml",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS, MediaType.PODCAST],
                "image": join(dirname(__file__), "ui", "images", "LDN.jpg"),
                "playback": PlaybackType.AUDIO
            },
            "Apokalypse und Filterkaffee": {
                "aliases": ["Apokalypse und Filterkaffee"],
                "uri": "rss//https://apokalypse-und-filterkaffee.podigee.io/feed/mp3",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS, MediaType.PODCAST],
                "image": join(dirname(__file__), "ui", "images", "AUF.jpg"),
                "playback": PlaybackType.AUDIO
            },
            "The Pioneer Briefing": {
                "aliases": ["Pioneer", "pionier", "Pioneer Briefing"],
                "uri": "rss//https://pcr.apple.com/id1428670057",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS, MediaType.PODCAST],
                "image": join(dirname(__file__), "ui", "images", "TPB.jpg"),
                "playback": PlaybackType.AUDIO
            },
            "OE3": {
                "aliases": ["OE3", "Ö3 Nachrichten", "Österreich", "österreichische"],
                "uri": "https://oe3meta.orf.at/oe3mdata/StaticAudio/Nachrichten.mp3",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS],
                "image": join(dirname(__file__), "ui", "images", "oe3.jpeg"),
                "playback": PlaybackType.AUDIO
            }
        },
        "nl-nl": {
            "VRT": {
                "aliases": ["VRT Nieuws", "VRT"],
                "uri": "http://progressive-audio.vrtcdn.be/content/fixed/11_11niws-snip_hi.mp3",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS],
                "image": join(dirname(__file__), "ui", "images", "vrt.png"),
                "playback": PlaybackType.AUDIO
            }
        },
        "sv-se": {
            "Ekot": {
                "aliases": ["Ekot"],
                "uri": "rss//https://api.sr.se/api/rss/pod/3795",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS],
                "image": join(dirname(__file__), "ui", "images", "Ekot.png"),
                "playback": PlaybackType.AUDIO
            }
        },
        "es-es": {
            "RNE": {
                "aliases": ["RNE", "National Spanish Radio",
                            "Radio Nacional de España"],
                "media_type": MediaType.NEWS,
                "uri": "rss//http://api.rtve.es/api/programas/36019/audios.rs",
                "match_types": [MediaType.NEWS],
                "image": join(dirname(__file__), "ui", "images", "rne.png"),
                "playback": PlaybackType.AUDIO
            }
        },
        "ca-es": {
            "CCMA": {
                "aliases": ["CCMA", "Catalunya Informació"],
                "media_type": MediaType.NEWS,
                "uri": "https://de1.api.radio-browser.info/pls/url/69bc7084-523c-11ea-be63-52543be04c81",
                "match_types": [MediaType.NEWS,
                                MediaType.RADIO],
                "image": join(dirname(__file__), "ui", "images", "CCMA.jpeg"),
                "playback": PlaybackType.AUDIO,
                "secondary_langs": ["es"]
            }
        },
        "fi-fi": {
            "YLE": {
                "aliases": ["YLE", "YLE News Radio"],
                "uri": "rss//https://feeds.yle.fi/areena/v1/series/1-1440981.rss",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS],
                "image": join(dirname(__file__), "ui", "images", "Yle.png"),
                "playback": PlaybackType.AUDIO
            }
        },
        "it-it": {
            "GR1": {
                "aliases": ["GR1", "Rai GR1", "Rai", "Radio Giornale 1"],
                "uri": "news//https://www.raiplaysound.it",
                "media_type": MediaType.NEWS,
                "match_types": [MediaType.NEWS],
                "image": join(dirname(__file__), "ui", "images", "RG1.jpg"),
                "playback": PlaybackType.AUDIO
            }
        }
    }

    def __init__(self):
        super().__init__("News")
        self.supported_media = [MediaType.GENERIC,
                                MediaType.NEWS]
        self.skill_icon = join(dirname(__file__), "ui", "news.png")
        self.default_bg = join(dirname(__file__), "ui", "bg.jpg")

    @classproperty
    def runtime_requirements(self):
        return RuntimeRequirements(internet_before_load=True,
                                   network_before_load=True,
                                   gui_before_load=False,
                                   requires_internet=True,
                                   requires_network=True,
                                   requires_gui=False,
                                   no_internet_fallback=False,
                                   no_network_fallback=False,
                                   no_gui_fallback=True)

    def clean_phrase(self, phrase):
        phrase = self.remove_voc(phrase, "news")

        phrase = self.remove_voc(phrase, "pt-pt")
        phrase = self.remove_voc(phrase, "en-us")
        phrase = self.remove_voc(phrase, "en-ca")
        phrase = self.remove_voc(phrase, "en-gb")
        phrase = self.remove_voc(phrase, "es")
        phrase = self.remove_voc(phrase, "fi")
        phrase = self.remove_voc(phrase, "de")
        phrase = self.remove_voc(phrase, "sv")
        phrase = self.remove_voc(phrase, "nl")
        phrase = self.remove_voc(phrase, "en")

        return phrase.strip()

    def match_lang(self, phrase):
        langs = []
        if self.voc_match(phrase, "pt-pt"):
            langs.append("pt-pt")
        if self.voc_match(phrase, "en-us"):
            langs.append("en-us")
        if self.voc_match(phrase, "en-gb"):
            langs.append("en-gb")
        if self.voc_match(phrase, "en-ca"):
            langs.append("en-ca")
        if self.voc_match(phrase, "en"):
            langs.append("en")
        if self.voc_match(phrase, "es"):
            langs.append("es-es")
        if self.voc_match(phrase, "de"):
            langs.append("de-de")
        if self.voc_match(phrase, "nl"):
            langs.append("nl-nl")
        if self.voc_match(phrase, "fi"):
            langs.append("fi-fi")
        if self.voc_match(phrase, "sv"):
            langs.append("sv-se")

        langs += [l.split("-")[0] for l in langs]
        return list(set(langs))

    def _score(self, phrase, entry, langs=None, base_score=0):
        score = base_score
        langs = langs or [self.lang]

        # match name
        _, alias_score = match_one(phrase, entry["aliases"],
                                   strategy=MatchStrategy.TOKEN_SORT_RATIO)
        entry["match_confidence"] = score + alias_score * 60

        # match languages
        if entry["lang"] in langs:
            entry["match_confidence"] += 20  # lang bonus
        elif any([lang in entry.get("secondary_langs", [])
                  for lang in langs]):
            entry["match_confidence"] += 10  # smaller lang bonus
        else:
            entry["match_confidence"] -= 20  # wrong language penalty

        # default news feed gets a nice bonus
        if entry.get("is_default"):
            entry["match_confidence"] += 30

        return min([entry["match_confidence"], 100])

    @ocp_featured_media()
    def news_playlist(self):
        entries = []
        
        for lang in self.lang2news:
            default_feed = self.langdefaults.get(lang)
            if lang == self.lang:
                default_feed = self.settings.get("default_feed") or default_feed

            for feed, config in self.lang2news[lang].items():
                if feed == default_feed:
                    config["is_default"] = True
                config["lang"] = lang
                config["title"] = config.get("title") or feed
                config["bg_image"] = config.get("bg_image") or self.default_bg
                config["skill_logo"] = self.skill_icon
                if config["uri"]:
                    entries.append(config)
        return entries

    @ocp_search()
    def search_news(self, phrase, media_type):
        """Analyze phrase to see if it is a play-able phrase with this skill.

        Arguments:
            phrase (str): User phrase uttered after "Play", e.g. "some music"
            media_type (MediaType): requested CPSMatchType to media for

        Returns:
            search_results (list): list of dictionaries with result entries
            {
                "match_confidence": MatchConfidence.HIGH,
                "media_type":  CPSMatchType.MUSIC,
                "uri": "https://audioservice.or.gui.will.play.this",
                "playback": PlaybackType.VIDEO,
                "image": "http://optional.audioservice.jpg",
                "bg_image": "http://optional.audioservice.background.jpg"
            }
        """
        base_score = 0
        if media_type == MediaType.NEWS or self.voc_match(phrase, "news"):
            base_score = 50
            if not phrase.strip():
                base_score += 20  # "play the news", no query

        pl = self.news_playlist()
        # playlist result
        yield {
            "match_confidence": base_score,
            "media_type": MediaType.NEWS,
            "playlist": pl,
            "playback": PlaybackType.AUDIO,
            "image": self.skill_icon,
            "bg_image": self.skill_icon,
            "skill_icon": self.skill_icon,
            "title": "Latest News (Station Playlist)",
            "skill_id": self.skill_id
        }

        # score individual results
        langs = self.match_lang(phrase) or [self.lang, self.lang.split("-")[0]]
        phrase = self.clean_phrase(phrase)
        if media_type == MediaType.NEWS or (phrase and base_score > MatchConfidence.AVERAGE_LOW):
            for v in pl:
                v["match_confidence"] = self._score(phrase, v, langs=langs, base_score=base_score)
                yield v


def create_skill():
    return NewsSkill()
