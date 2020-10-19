import os

from gdpr.version import get_version
from setuptools import find_packages, setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='django-GDPR',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    version=get_version(),
    description='Library for GDPR implementation',
    author='Druids',
    author_email='matllubos@gmail.com',
    url='https://github.com/druids/django-GDPR',
    license='MIT',
    package_dir={'gdpr': 'gdpr'},
    include_package_data=True,
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=[
        'django>=1.8, <2',
        'django-chamber @ git+ssh://git@github.com/druids/django-chamber.git#egg=django-chamber-0.3.9',
        'enum34>=1.1.10',
        'future-fstrings>=1.2.0',
        'python-dateutil>=2.8.0',
        'tqdm>=4.28.1',
    ],
    zip_safe=False,
)
