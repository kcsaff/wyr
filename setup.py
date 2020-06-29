import os
from setuptools import setup, find_packages

version = '0.0.1'

def read(f):
    return open(os.path.join(os.path.dirname(__file__), f)).read().strip()

try:
   import pypandoc
   description = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError):
   description = read('README.md')

setup(name='wyr',
      version=version,
      description='A script that asks Would You Rather questions',
      long_description=description,
      classifiers=[
          'License :: OSI Approved :: MIT License',
          'Intended Audience :: Other Audience',
          'Programming Language :: Python :: 3'],
      author='K.C.Saff',
      author_email='kc@saff.net',
      url='https://github.com/kcsaff/wyr',
      license='MIT',
      packages=find_packages(),
      install_requires=[
          'requests>=2.24.0',
      ],
      entry_points={
          'console_scripts': ['wyr = wyr:main']
      },
      include_package_data=False,
)
