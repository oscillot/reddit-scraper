import os
from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(HERE, 'VERSION')) as f:
    VERSION = f.read()

setup(
    name='reddit_scraper',
    version=VERSION,
    package_dir={'':'src'},
    packages=find_packages(where='src'),
    install_requires=['pillow>=1.7.8',
                      'lxml>=3.0.2',
                      'sqlalchemy>=0.8.0b2',
                      'requests>=2.0.0',
                      'BeautifulSoup4'
    ],
    url='https://github.com/oscillot/reddit-scraper',
    license='GPL2',
    author='Oscillot',
    author_email='oscillot@trioptimum.com',
    test_suite='tests',
    description='Automatically download upvoted wallpapers using cron or '
                'jenkins easily extended with plugins you can write yourself. '
                'Requires SQLite be already installed. See the README to get '
                'started with plugins or just dive into the code.'
)