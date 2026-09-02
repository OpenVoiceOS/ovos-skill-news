import unittest
from unittest.mock import patch, MagicMock

from ovos_utils.fakebus import FakeBus
from ovos_bus_client.message import Message

from ovos_skill_news import NewsSkill


class TestNewsDispatch(unittest.TestCase):
    """The single ``news.intent`` handler dispatches between global and
    local news based on ``global.voc`` matching the utterance, rather than
    relying on two separate Padatious intents."""

    @classmethod
    def setUpClass(cls):
        cls.skill_id = "ovos-skill-news.openvoiceos"

    def _make_skill(self):
        bus = FakeBus()
        skill = NewsSkill()
        skill._startup(bus, self.skill_id)
        return skill

    def _fake_read_db(self, world_only=False, local_only=False, langs=None):
        # one distinguishable entry per feed scope so the test can assert
        # which scope the handler actually searched
        title = "GlobalFeed" if world_only else "LocalFeed"
        return [{"title": title, "uri": f"http://example.com/{title}",
                 "media_type": "news"}]

    def test_world_news_utterance_takes_global_path(self):
        skill = self._make_skill()
        with patch.object(skill, "read_db", side_effect=self._fake_read_db), \
             patch.object(skill, "_score", return_value=100), \
             patch.object(skill, "play_media") as play_media, \
             patch.object(skill, "acknowledge"):
            skill.handle_play_the_news(
                Message("intent", {"utterance": "play world news"})
            )
        self.assertTrue(play_media.called)
        media = play_media.call_args.kwargs["media"]
        self.assertEqual(media.title, "GlobalFeed")

    def test_default_news_utterance_takes_local_path(self):
        skill = self._make_skill()
        with patch.object(skill, "read_db", side_effect=self._fake_read_db), \
             patch.object(skill, "_score", return_value=100), \
             patch.object(skill, "play_media") as play_media, \
             patch.object(skill, "acknowledge"):
            skill.handle_play_the_news(
                Message("intent", {"utterance": "play the news"})
            )
        self.assertTrue(play_media.called)
        media = play_media.call_args.kwargs["media"]
        self.assertEqual(media.title, "LocalFeed")


if __name__ == "__main__":
    unittest.main()
