"""End-to-end intent routing tests for ovos-skill-news."""
from unittest import TestCase

from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovoscope import End2EndTest, get_minicroft


class TestNewsSkillLoads(TestCase):
    """Verify the skill plugin loads and reaches READY state."""

    @classmethod
    def setUpClass(cls):
        cls.skill_id = "ovos-skill-news.openvoiceos"
        cls.minicroft = get_minicroft([cls.skill_id])

    @classmethod
    def tearDownClass(cls):
        if cls.minicroft:
            cls.minicroft.stop()

    def test_skill_loaded(self):
        """Skill must appear in the loaded plugin skills."""
        self.assertIn(self.skill_id, self.minicroft.plugin_skills)

    def test_play_news_padatious(self):
        session = Session("test-news-01")
        session.pipeline = ["ovos-padatious-pipeline-plugin-high"]
        message = Message(
            "recognizer_loop:utterance",
            {"utterances": ["play the news"], "lang": "en-US"},
            {"session": session.serialize(), "source": "A", "destination": "B"},
        )

        test = End2EndTest(
            minicroft=self.minicroft,
            skill_ids=[self.skill_id],
            source_message=message,
            expected_messages=[
                message,
                Message(f"{self.skill_id}.activate", {}, {"skill_id": self.skill_id}),
            ],
        )
        test.execute(timeout=15)
