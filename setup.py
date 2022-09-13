#!/usr/bin/env python3
import os
from setuptools import setup

BASEDIR = os.path.abspath(os.path.dirname(__file__))

# skill_id=package_name:SkillClass
PLUGIN_ENTRY_POINT = 'skill-news.jarbasai=skill_news:NewsSkill'


def required(requirements_file):
    """ Read requirements file and remove comments and empty lines. """
    with open(os.path.join(BASEDIR, requirements_file), 'r') as f:
        requirements = f.read().splitlines()
        if 'MYCROFT_LOOSE_REQUIREMENTS' in os.environ:
            print('USING LOOSE REQUIREMENTS!')
            requirements = [r.replace('==', '>=').replace('~=', '>=') for r in requirements]
        return [pkg for pkg in requirements
                if pkg.strip() and not pkg.startswith("#")]


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
    install_requires=required("requirements.txt"),
    keywords='ovos skill plugin',
    entry_points={'ovos.plugin.skill': PLUGIN_ENTRY_POINT}
)
