from setuptools import setup, find_packages

setup(
    name='reddit-scraper',
    version='2.01',
    packages=find_packages(),
    install_requires=['pillow>=1.7.8',
                      'lxml>=3.0.2',
                      'sqlalchemy>=0.8.0b2',
                      'requests>=2.0.0'
    ],
    url='https://github.com/oscillot/reddit-scraper',
    license='GPL2',
    author='Oscillot',
    author_email='oscillot@trioptimum.com',
    description='Automatically download upvoted wallpapers using cron or '
                'jenkins easily extended with plugins you can write yourself. '
                'Requires SQLite be already installed. See the README to get '
                'started with plugins or just dive into the code.'
)
