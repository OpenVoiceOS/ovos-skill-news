import unittest
from os.path import dirname

from ovos_plugin_manager.skills import find_skill_plugins
from ovos_utils.fakebus import FakeBus
from ovos_workshop.skill_launcher import PluginSkillLoader
from ovos_skill_news import NewsSkill


class TestSkillLoading(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill_id = "ovos-skill-news.openvoiceos"

    def test_from_class(self):
        bus = FakeBus()
        skill = NewsSkill()
        skill._startup(bus, self.skill_id)
        self.assertEqual(skill.bus, bus)
        self.assertEqual(skill.skill_id, self.skill_id)

    def test_from_plugin(self):
        bus = FakeBus()
        for skill_id, plug in find_skill_plugins().items():
            if skill_id == self.skill_id:
                skill = plug()
                skill._startup(bus, self.skill_id)
                self.assertEqual(skill.bus, bus)
                self.assertEqual(skill.skill_id, self.skill_id)
                break
        else:
            raise RuntimeError("plugin not found")

    def test_from_plugin_loader(self):
        bus = FakeBus()
        loader = PluginSkillLoader(bus, self.skill_id)
        for skill_id, plug in find_skill_plugins().items():
            if skill_id == self.skill_id:
                loader.load(plug)
                break
        else:
            raise RuntimeError("plugin not found")

        self.assertEqual(loader.skill_id, self.skill_id)
        self.assertEqual(loader.instance.bus, bus)
        self.assertEqual(loader.instance.skill_id, self.skill_id)
