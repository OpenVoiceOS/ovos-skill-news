from os.path import join, dirname
from typing import Iterable, Union, List

from json_database import JsonStorage
from ovos_utils import classproperty
from ovos_utils.ocp import MediaType, PlaybackType, Playlist, PluginStream, dict2entry, MediaEntry
from ovos_utils.parse import match_one, MatchStrategy
from ovos_utils.process_utils import RuntimeRequirements
from ovos_workshop.decorators import ocp_search, ocp_featured_media
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill


# Unified News Skill
class NewsSkill(OVOSCommonPlaybackSkill):
    # default feeds per language (optional)
    langdefaults = {
        "pt-pt": "RTP",
        "es-es": "RNE",
        "ca-es": "CCMA",
        "en-gb": "BBC",
        "en-us": "NPR",
        "en-au": "ABC",
        "en-ca": "CBC",
        "it-it": "GR1",
        "de-de": "DLF - Die Nachrichten"
    }

    def __init__(self, *args, **kwargs):
        self.default_bg = join(dirname(__file__), "res", "bg.jpg")
        self.archive = JsonStorage(f"{dirname(__file__)}/News.json")
        super().__init__(supported_media=[MediaType.NEWS, MediaType.GENERIC], 
                         skill_icon=join(dirname(__file__), "res", "news.png"), 
                         *args, **kwargs)

    @classproperty
    def runtime_requirements(self):
        return RuntimeRequirements(internet_before_load=True,
                                   requires_internet=True)

    def initialize(self):
        news = []
        for a in self.archive.values():
            for k in a:
                news += a[k]["aliases"] + [k]
        self.register_ocp_keyword(MediaType.NEWS, "news_provider", news)
        # self.export_ocp_keywords_csv("news.csv")

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
        match_confidence = score + alias_score * 60

        # match languages
        if entry["lang"] in langs:
            match_confidence += 25  # lang bonus
        elif any([lang in entry.get("secondary_langs", [])
                  for lang in langs]):
            match_confidence += 10  # smaller lang bonus
        else:
            match_confidence -= 20  # wrong language penalty

        # default news feed gets a nice bonus
        if entry.get("is_default"):
            match_confidence += 30

        return min([match_confidence, 100])

    def read_db(self) -> List[dict]:
        entries = []
        for lang in self.archive:
            default_feed = self.langdefaults.get(lang)
            if lang == self.lang:
                default_feed = self.settings.get("default_feed") or default_feed
            for feed, config in self.archive[lang].items():
                if feed == default_feed:
                    config["is_default"] = True
                config["lang"] = lang
                config["title"] = config.get("title") or feed
                config["image"] = config.get("image", "").replace("./res/images/",
                                                                  f"{dirname(__file__)}/res/images/")
                config["bg_image"] = config.get("bg_image") or self.default_bg
                config["skill_logo"] = self.skill_icon
                config["playback"] = PlaybackType.AUDIO
                config["media_type"] = MediaType.NEWS
                if config["uri"]:
                    entries.append(config)
        return entries

    @ocp_featured_media()
    def news_playlist(self) -> Playlist:
        entries = Playlist(title="Latest News (Station Playlist)")
        for config in self.read_db():
            if config["uri"].startswith("rss//"):
                entries.append(PluginStream(
                    extractor_id="rss",
                    stream=config["uri"].split("rss//")[-1],
                    title=config.get("title"),
                    image=config.get("image"),
                    media_type=MediaType.NEWS,
                    playback=PlaybackType.AUDIO,
                    skill_icon=self.skill_icon,
                    skill_id=self.skill_id)
                )
            elif config["uri"].startswith("news//"):
                entries.append(PluginStream(
                    extractor_id="news",
                    stream=config["uri"].split("news//")[-1],
                    title=config.get("title"),
                    image=config.get("image"),
                    media_type=MediaType.NEWS,
                    playback=PlaybackType.AUDIO,
                    skill_icon=self.skill_icon,
                    skill_id=self.skill_id)
                )
            else:
                entries.append(MediaEntry(
                    uri=config["uri"],
                    title=config.get("title"),
                    image=config.get("image"),
                    media_type=MediaType.NEWS,
                    playback=PlaybackType.AUDIO,
                    skill_icon=self.skill_icon,
                    skill_id=self.skill_id)
                )
        return entries

    @ocp_search()
    def search_news(self, phrase, media_type) -> Iterable[Union[Playlist, MediaType, PluginStream]]:
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

        entities = self.ocp_voc_match(phrase)

        base_score += 20 * len(entities)
        if media_type == MediaType.NEWS or self.voc_match(phrase, "news"):
            base_score += 30
            if not phrase.strip():
                base_score += 20  # "play the news", no query

        pl = self.news_playlist()

        # score individual results
        langs = self.match_lang(phrase) or [self.lang, self.lang.split("-")[0]]
        if entities:
            phrase = entities["news_provider"]
        else:
            phrase = self.clean_phrase(phrase)

        results = []
        # playlist result
        if pl and base_score >= 50:
            results.append(pl)

        if entities or media_type == MediaType.NEWS:
            for v in self.read_db():
                s = self._score(phrase, v, langs=langs, base_score=base_score)
                if s <= 50:
                    continue
                if v["uri"].startswith("news//"):
                    v["extractor_id"] = "news"
                    v["stream"] = v["uri"].split("news//")[-1]
                elif v["uri"].startswith("rss//"):
                    v["extractor_id"] = "rss"
                    v["stream"] = v["uri"].split("rss//")[-1]
                v = dict2entry(v)
                v.match_confidence = min(100, s)
                results.append(v)

        return sorted(results, key=lambda k: k.match_confidence, reverse=True)


if __name__ == "__main__":
    from ovos_utils.messagebus import FakeBus

    s = NewsSkill(bus=FakeBus(), skill_id="t.fake")

    for r in s.search_news("portuguese", MediaType.NEWS):
        print(r)
        # {'aliases': ['TSF', 'TSF Rádio Notícias', 'TSF Notícias'], 'uri': 'news//https://www.tsf.pt/stream', 'image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/res/images/tsf.png', 'secondary_langs': ['pt'], 'is_default': True, 'lang': 'pt-pt', 'title': 'TSF', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 80.0}
        # {'aliases': ['RTP', 'Antena 1', 'Noticiario Nacional'], 'uri': 'rss//http://www.rtp.pt/play/itunes/7496', 'image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/res/images/RTP_1.png', 'secondary_langs': ['pt'], 'lang': 'pt-pt', 'title': 'RTP', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 50.0}
        # {'aliases': ['RDP', 'RDP Africa'], 'uri': 'rss//http://www.rtp.pt/play/itunes/5442', 'image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/res/images/RDP.png', 'secondary_langs': ['pt'], 'lang': 'pt-pt', 'title': 'RDP', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 50.0}

    for r in s.search_news("NPR", MediaType.GENERIC):
        print(r)
        # {'aliases': ['NPR News', 'NPR', 'National Public Radio', 'National Public Radio News', 'NPR News Now'], 'uri': 'news//https://www.npr.org/podcasts/500005/npr-news-now', 'image': 'https://media.npr.org/assets/img/2018/08/06/nprnewsnow_podcasttile_sq.webp', 'secondary_langs': ['en'], 'is_default': True, 'lang': 'en-us', 'title': 'NPR', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 100}
        # {'aliases': ['British Broadcasting Corporation', 'BBC', 'BBC News'], 'uri': 'rss//https://podcasts.files.bbci.co.uk/p02nq0gn.rss', 'image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/res/images/BBC.png', 'secondary_langs': ['en'], 'is_default': True, 'lang': 'en-gb', 'title': 'BBC', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 70.9090909090909}
        # {'aliases': ['Canadian Broadcasting Corporation', 'CBC', 'CBC News'], 'uri': 'rss//https://www.cbc.ca/podcasting/includes/hourlynews.xml', 'image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/res/images/CBC.png', 'secondary_langs': ['en'], 'is_default': True, 'lang': 'en-ca', 'title': 'CBC', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 70.9090909090909}
        # {'aliases': ['Australian Broadcasting Corporation', 'ABC', 'ABC News'], 'uri': 'news//https://www.abc.net.au/news', 'image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/res/images/ABC.png', 'secondary_langs': ['en'], 'is_default': True, 'lang': 'en-au', 'title': 'ABC', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 70.9090909090909}
        # {'aliases': ['PBS News', 'PBS', 'PBS NewsHour', 'PBS News Hour', 'National Public Broadcasting Service', 'Public Broadcasting Service News'], 'uri': 'rss//https://www.pbs.org/newshour/feeds/rss/podcasts/show', 'image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/res/images/PBS.png', 'secondary_langs': ['en'], 'lang': 'en-us', 'title': 'PBS', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 66.81818181818181}
        # {'aliases': ['NSPR Headlines', 'North State News', 'North State Public Radio'], 'uri': 'news//https://www.npr.org/podcasts/1074915520/n-s-p-r-headlines', 'image': 'https://media.npr.org/images/podcasts/primary/icon_1074915520-8d70ce2af1d6db7fab8a42a9b4eb55dddb6eb69a.png', 'secondary_langs': ['en'], 'lang': 'en-us', 'title': 'NSPR', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 66.17647058823529}
        # {'aliases': ['SDPB', 'SDPB News'], 'uri': 'news//https://www.npr.org/podcasts/1031233995/s-d-p-b-news', 'image': 'https://media.npr.org/images/podcasts/primary/icon_1031233995-ae5c8fd4e932033b3b8e079cdc133703c2ef427c.jpg', 'secondary_langs': ['en'], 'lang': 'en-us', 'title': 'SDPB', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 65.0}
        # {'aliases': ['First News', 'KRCB', 'Sonoma News'], 'uri': 'news//https://www.npr.org/podcasts/1090302835/first-news', 'image': 'https://media.npr.org/images/podcasts/primary/icon_1090302835-6b593e71a8d60b373ec735479dfbdd9e7f2e8cfe.png', 'secondary_langs': ['en'], 'lang': 'en-us', 'title': 'SFN', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 62.14285714285714}
        # {'aliases': ['Aspen Public Radio Newscast', 'Aspen Public Radio News', 'Aspen Public Radio', 'Aspen News'], 'uri': 'news//https://www.npr.org/podcasts/1100476310/aspen-public-radio-newscast', 'image': 'https://media.npr.org/images/podcasts/primary/icon_1100476310-9b43c8bf959de6d90a5f59c58dc82ebc7b9b9258.png', 'secondary_langs': ['en'], 'lang': 'en-us', 'title': 'ASPEN', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 58.84615384615384}
        # {'aliases': ['N.H. News Recap', 'New Hampshire Public Radio', 'New Hampshire News'], 'uri': 'news//https://www.npr.org/podcasts/1071428476/n-h-news-recap', 'image': 'https://media.npr.org/images/podcasts/primary/icon_1071428476-7bd7627d52d6c3fc7082a1524b1b10a49dde7444.png', 'secondary_langs': ['en'], 'lang': 'en-us', 'title': 'NHNR', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 58.33333333333333}
        # {'aliases': ['AP Hourly Radio News', 'Associated Press', 'Associated Press News', 'Associated Press Radio News', 'Associated Press Hourly Radio News'], 'uri': 'rss//https://www.spreaker.com/show/1401466/episodes/feed', 'image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/res/images/AP.png', 'secondary_langs': ['en'], 'lang': 'en-us', 'title': 'AP', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 57.0}
        # {'aliases': ['WSIU News', 'WSIU Public Radio'], 'uri': 'news//https://www.npr.org/podcasts/1038076755/w-s-i-u-news-updates', 'image': 'https://media.npr.org/images/podcasts/primary/icon_1038076755-aa4101ea9d54395c83b03d7dc7ac823047682192.jpg', 'secondary_langs': ['en'], 'lang': 'en-us', 'title': 'WSIU', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 57.0}
        # {'aliases': ['KGOU PM NewsBrief', 'KGOU Evening News'], 'uri': 'news//https://www.npr.org/podcasts/1111549375/k-g-o-u-p-m-news-brief', 'image': 'https://media.npr.org/images/podcasts/primary/icon_1111549375-c22ef178b4a5db87547aeb4c3c14dc8a8b1bc462.png', 'secondary_langs': ['en'], 'lang': 'en-us', 'title': 'KGOU_PM', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 57.0}
        # {'aliases': ['FOX News', 'FOX', 'Fox News Channel'], 'uri': 'rss//http://feeds.foxnewsradio.com/FoxNewsRadio', 'image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/res/images/FOX.png', 'secondary_langs': ['en'], 'lang': 'en-us', 'title': 'FOX', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 55.90909090909091}
        # {'aliases': ['KHNS-FM Local News', 'KHN News'], 'uri': 'news//https://www.npr.org/podcasts/381444103/k-h-n-s-f-m-local-news', 'image': 'https://media.npr.org/images/podcasts/primary/icon_1111549375-c22ef178b4a5db87547aeb4c3c14dc8a8b1bc462.png', 'secondary_langs': ['en'], 'lang': 'en-us', 'title': 'KHNS', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 55.90909090909091}
        # {'aliases': ['KBBI Newscast', 'KBBI News', 'KBBI'], 'uri': 'news//https://www.npr.org/podcasts/1052142404/k-b-b-i-newscast', 'image': 'https://media.npr.org/images/podcasts/primary/icon_1052142404-2839f62f7db7bf2ec753fca56913bd7a1b52c428.png', 'secondary_langs': ['en'], 'lang': 'en-us', 'title': 'KBBI', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 55.0}
        # {'aliases': ['Midday News', 'KVCR News', 'The Midday News Report'], 'uri': 'news//https://www.npr.org/podcasts/1033362253/the-midday-news-report', 'image': 'https://media.npr.org/images/podcasts/primary/icon_1033362253-566d4a69caee465ebe1adf7d2949ae0c745e97b8.png', 'secondary_langs': ['en'], 'lang': 'en-us', 'title': 'KVCR', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 55.0}
        # {'aliases': ['Alaska Nightly', 'Alaska News Nightly'], 'uri': 'news//https://www.npr.org/podcasts/828054805/alaska-news-nightly', 'image': 'https://media.npr.org/images/podcasts/primary/icon_828054805-1ce50401d43f15660a36275a8bf2ff454de62b2f.png', 'secondary_langs': ['en'], 'lang': 'en-us', 'title': 'AN', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 52.05882352941177}
        # {'aliases': ['Financial Times', 'FT', 'FT News Briefing'], 'uri': 'news//https://www.ft.com', 'image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/res/images/FT.png', 'secondary_langs': ['en'], 'lang': 'en-us', 'title': 'FT', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 51.31578947368421}
        # {'aliases': ['KGOU AM NewsBrief', 'KGOU Morning News'], 'uri': 'news//https://www.npr.org/podcasts/1111549080/k-g-o-u-a-m-news-brief', 'image': 'https://media.npr.org/images/podcasts/primary/icon_1111549080-ebbfb83b98c966f38237d3e6ed729d659d098cb9.png', 'secondary_langs': ['en'], 'lang': 'en-us', 'title': 'KGOU_AM', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 51.0}
