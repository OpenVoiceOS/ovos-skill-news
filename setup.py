#!/usr/bin/env python3
from setuptools import setup

# skill_id=package_name:SkillClass
PLUGIN_ENTRY_POINT = 'skill-news.jarbasai=skill_news:NewsSkill'

setup(
    # this is the package name that goes on pip
    name='ovos-skill-news',
    version='0.0.1',
    description='ovos news skill plugin',
    url='https://github.com/JarbasSkills/skill-news',
    author='JarbasAi',
    author_email='jarbasai@mailfence.com',
    license='Apache-2.0',
    package_dir={"skill_news": ""},
    package_data={'skill_news': ['locale/*', 'ui/*', 'res/*']},
    packages=['skill_news'],
    include_package_data=True,
    install_requires=["ovos_workshop~=0.0.5a7", "pytz", "beautifulsoup4"],
    keywords='ovos skill plugin',
    entry_points={'ovos.plugin.skill': PLUGIN_ENTRY_POINT}
)
