import os
from setuptools import setup
os.makedirs("output", exist_ok=True)
setup(
    name = 'mindstudio-kl',
    version = '26.0.0',
    author =' mskl',
    author_email = 'mskl',
    description = 'mskl',
    long_description = open('README.md', encoding='utf-8').read(),
    long_description_content_type = 'text/markdown',
    url = 'https://gitcode.com/Ascend/mskl',
    packages = ['mskl'],
    include_package_data = True,
    classifiers = [
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    options={
        'bdist_wheel': {
            'dist_dir': 'output',
        }
    },
    python_requires = '>=3.6'
)