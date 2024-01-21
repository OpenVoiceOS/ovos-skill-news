from os.path import join, dirname

from json_database import JsonStorage
from ovos_utils import classproperty
from ovos_utils.ocp import MediaType, PlaybackType
from ovos_utils.parse import match_one, MatchStrategy
from ovos_utils.process_utils import RuntimeRequirements
from ovos_workshop.decorators import ocp_search, ocp_featured_media
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill


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

    def __init__(self, *args, **kwargs):
        self.supported_media = [MediaType.NEWS]
        self.skill_icon = join(dirname(__file__), "ui", "news.png")
        self.default_bg = join(dirname(__file__), "ui", "bg.jpg")
        self.archive = JsonStorage(f"{dirname(__file__)}/News.json")
        super().__init__(*args, **kwargs)

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
        self.export_ocp_keywords_csv("news.csv")

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
        entities = self.ocp_voc_match(phrase)
        base_score += 50 * len(entities)
        if media_type == MediaType.NEWS or self.voc_match(phrase, "news"):
            base_score += 30
            if not phrase.strip():
                base_score += 20  # "play the news", no query

        pl = self.news_playlist()

        # score individual results
        langs = self.match_lang(phrase) or [self.lang, self.lang.split("-")[0]]
        phrase = self.clean_phrase(phrase)
        results = []

        if entities or media_type == MediaType.NEWS:
            for v in pl:
                v["match_confidence"] = self._score(phrase, v, langs=langs, base_score=base_score)
                results.append(v)

        # playlist result
        if pl and base_score >= 50:
            results.append({
                "match_confidence": base_score,
                "media_type": MediaType.NEWS,
                "playlist": pl,
                "playback": PlaybackType.AUDIO,
                "image": self.skill_icon,
                "bg_image": self.skill_icon,
                "skill_icon": self.skill_icon,
                "title": "Latest News (Station Playlist)",
                "skill_id": self.skill_id
            })

        return sorted(results, key=lambda k: k["match_confidence"], reverse=True)


if __name__ == "__main__":
    from ovos_utils.messagebus import FakeBus

    s = NewsSkill(bus=FakeBus(), skill_id="t.fake")

    for r in s.search_news("portuguese", MediaType.NEWS):
        print(r)
        # {'aliases': ['TSF', 'TSF Rádio Notícias', 'TSF Notícias'], 'uri': 'news//https://www.tsf.pt/stream', 'image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/images/tsf.png', 'secondary_langs': ['pt'], 'is_default': True, 'lang': 'pt-pt', 'title': 'TSF', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 100.0}
        # {'aliases': ['RTP', 'Antena 1', 'Noticiario Nacional'], 'uri': 'rss//http://www.rtp.pt/play/itunes/7496', 'image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/images/RTP_1.png', 'secondary_langs': ['pt'], 'lang': 'pt-pt', 'title': 'RTP', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 70.0}
        # {'aliases': ['RDP', 'RDP Africa'], 'uri': 'rss//http://www.rtp.pt/play/itunes/5442', 'image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/images/RDP.png', 'secondary_langs': ['pt'], 'lang': 'pt-pt', 'title': 'RDP', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 70.0}
        # {'aliases': ['NPR News', 'NPR', 'National Public Radio', 'National Public Radio News', 'NPR News Now'], 'uri': 'news//https://www.npr.org/podcasts/500005/npr-news-now', 'image': 'https://media.npr.org/assets/img/2018/08/06/nprnewsnow_podcasttile_sq.webp', 'secondary_langs': ['en'], 'is_default': True, 'lang': 'en-us', 'title': 'NPR', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 60.0}
        # {'aliases': ['British Broadcasting Corporation', 'BBC', 'BBC News'], 'uri': 'rss//https://podcasts.files.bbci.co.uk/p02nq0gn.rss', 'image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/images/BBC.png', 'secondary_langs': ['en'], 'is_default': True, 'lang': 'en-gb', 'title': 'BBC', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-ovos-news/ui/bg.jpg', 'skill_logo': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'playback': <PlaybackType.AUDIO: 2>, 'media_type': <MediaType.NEWS: 8>, 'match_confidence': 60.0}
        # ...
