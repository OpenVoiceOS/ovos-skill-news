from os.path import join, dirname
from typing import Iterable, Union, List

from langcodes import closest_match
from json_database import JsonStorage
from ovos_utils import classproperty
from ovos_utils.lang import standardize_lang_tag
from ovos_utils.ocp import MediaType, PlaybackType, Playlist, PluginStream, dict2entry, MediaEntry
from ovos_utils.parse import match_one, MatchStrategy
from ovos_utils.process_utils import RuntimeRequirements
from ovos_workshop.decorators import ocp_search, ocp_featured_media, intent_handler
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill


# Unified News Skill
class NewsSkill(OVOSCommonPlaybackSkill):
    # default feeds per language (optional)
    langdefaults = {
        "pt-PT": "RTP",
        "es-ES": "RNE",
        "ca-ES": "CCMA",
        "en-GB": "BBC",
        "en-US": "NPR",
        "en-AU": "ABC",
        "en-CA": "CBC",
        "it-IT": "GR1",
        "fr-FR": "EuroNews",
        "de-DE": "DLF - Die Nachrichten"
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

    def clean_phrase(self, phrase: str) -> str:
        phrase = self.remove_voc(phrase, "world_news")
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

    def match_lang(self, phrase: str) -> List[str]:
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
        langs = [standardize_lang_tag(l, macro=True) for l in langs]
        return list(set(langs))

    def _score(self, phrase, entry, langs=None, base_score=0):
        # self.log.debug(f"### {entry}")
        score = base_score
        langs = langs or self.native_langs
        # self.log.debug(f"\t- base score: {score}")

        # match name
        _, alias_score = match_one(phrase, entry["aliases"],
                                   strategy=MatchStrategy.TOKEN_SORT_RATIO)
        match_confidence = score + alias_score * 60
        # self.log.debug(f"\t- fuzzy score: {match_confidence}")

        # match languages
        elang = standardize_lang_tag(entry["lang"])
        elangs = set(standardize_lang_tag(l) for l in entry.get("secondary_langs", []))
        elangs.add(elang)
        if elang in langs:
            match_confidence += 25  # lang bonus
        elif any([lang in elangs for lang in langs]):
            match_confidence += 10  # smaller lang bonus
        else:
            match_confidence -= 20  # wrong language penalty
        # self.log.debug(f"\t- lang score: {match_confidence}")

        # match country code
        country = self.location["city"]["state"]["country"]["code"]
        if any((l.endswith(f"-{country}") for l in elangs)):
            match_confidence += 20  # bonus for news stations from user location
            # self.log.debug(f"\t- location score: {match_confidence}")

        # default news feed gets a nice bonus
        if entry.get("is_default"):
            match_confidence += 10
            # self.log.debug(f"\t- default station score: {match_confidence}")

        return min([match_confidence, 100])

    def read_db(self, world_only=False, local_only=False, langs=None) -> List[dict]:
        langs = langs or self.native_langs
        entries = []
        for lang in self.archive:
            std_lang = standardize_lang_tag(lang)
            lang_score = closest_match(std_lang, langs)[-1]
            if lang_score > 10:
                self.log.debug(f"Ignoring news streams from foreign language: {std_lang}")
                continue
            default_feed = self.langdefaults.get(lang)
            if std_lang == self.lang:
                default_feed = self.settings.get("default_feed") or default_feed
            for feed, config in self.archive[lang].items():
                if world_only and not config.get("world_news", False):
                    continue
                if local_only and config.get("world_news"):
                    continue
                if feed == default_feed:
                    config["is_default"] = True
                config["lang"] = std_lang
                config["title"] = config.get("title") or feed
                config["image"] = config.get("image", "").replace("./res/images/",
                                                                  f"{dirname(__file__)}/res/images/")
                config["bg_image"] = config.get("bg_image") or self.default_bg
                config["skill_logo"] = self.skill_icon
                config["playback"] = PlaybackType.AUDIO
                config["media_type"] = MediaType.NEWS

                if config["uri"]:
                    if config["uri"].startswith("news//"):
                        config["extractor_id"] = "news"
                        config["stream"] = config["uri"].split("news//")[-1]
                    elif config["uri"].startswith("rss//"):
                        config["extractor_id"] = "rss"
                        config["stream"] = config["uri"].split("rss//")[-1]
                    elif config["uri"].startswith("youtube.channel.live//"):
                        config["extractor_id"] = "youtube.channel.live"
                        config["stream"] = config["uri"].split("youtube.channel.live//")[-1]
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
        world_news = self.voc_match(phrase, "world_news")
        base_score = 50 if world_news else 0

        entities = self.ocp_voc_match(phrase)

        base_score += 20 * len(entities)
        if media_type == MediaType.NEWS or self.voc_match(phrase, "news"):
            base_score += 30
            if not phrase.strip():
                base_score += 20  # "play the news", no query

        # score individual results
        langs = self.match_lang(phrase) or self.native_langs
        if entities:
            phrase = entities["news_provider"]
        else:
            phrase = self.clean_phrase(phrase)

        results = []

        if entities or media_type == MediaType.NEWS or world_news:
            for v in self.read_db(world_only=world_news, langs=langs):
                s = self._score(phrase, v, langs=langs, base_score=base_score)
                if s <= 50:
                    continue
                v = dict2entry(v)
                v.match_confidence = min(100, s)
                results.append(v)

        # playlist result
        if not world_news and (media_type == MediaType.NEWS or base_score >= 60):
            pl = self.news_playlist()
            if pl:
                results.append(pl)
        return sorted(results, key=lambda k: k.match_confidence, reverse=True)

    @intent_handler("news.intent")
    def handle_play_the_news(self, message):
        utterance = message.data["utterance"]
        self.acknowledge()  # short sound to know we are searching news
        # create a playlist with results sorted by relevance
        # create a playlist with results sorted by relevance
        results = []
        for v in self.read_db(local_only=True):
            s = self._score(utterance, v, base_score=30)
            if s <= 50:
                continue
            v = dict2entry(v)
            v.match_confidence = min(100, s)
            results.append(v)

        if not results:
            self.speak_dialog("news.error")
        else:
            self.play_media(media=results[0],
                            disambiguation=results,
                            playlist=results)

    @intent_handler("global_news.intent")
    def handle_global_news(self, message):
        utterance = message.data["utterance"]
        self.acknowledge()  # short sound to know we are searching news
        # create a playlist with results sorted by relevance
        results = []
        for v in self.read_db(world_only=True):
            s = self._score(utterance, v, base_score=30)
            if s <= 50:
                continue
            v = dict2entry(v)
            v.match_confidence = min(100, s)
            results.append(v)

        if not results:
            self.speak_dialog("news.error")
        else:
            self.play_media(media=results[0],
                            disambiguation=results,
                            playlist=results)


if __name__ == "__main__":
    from ovos_utils.messagebus import FakeBus

    s = NewsSkill(bus=FakeBus(), skill_id="t.fake")

    for r in s.search_news("portuguese world news", MediaType.GENERIC):
        print(r)
        # PluginStream(stream='https://www.youtube.com/@euronewspt/live', extractor_id='youtube.channel.live', title='EuroNews', artist='', match_confidence=100, skill_id='ovos.common_play', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.NEWS: 8>, length=0, image='/home/miro/PycharmProjects/OVOS-dev/ovos-skill-news/res/images/EuroNews.png', skill_icon='')

    for r in s.search_news("portuguese news", MediaType.GENERIC):
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
