#! /usr/bin/env python

import subprocess
import os

from setuptools import setup
from setuptools.command.sdist import sdist


class eo_sdist(sdist):
    def run(self):
        print "creating VERSION file"
        if os.path.exists('VERSION'):
            os.remove('VERSION')
        version = get_version()
        version_file = open('VERSION', 'w')
        version_file.write(version)
        version_file.close()
        sdist.run(self)
        print "removing VERSION file"
        if os.path.exists('VERSION'):
            os.remove('VERSION')


def get_version():
    '''Use the VERSION, if absent generates a version with git describe, if not
       tag exists, take 0.0.0- and add the length of the commit log.
    '''
    if os.path.exists('VERSION'):
        with open('VERSION', 'r') as v:
            return v.read()
    if os.path.exists('.git'):
        p = subprocess.Popen(['git', 'describe', '--dirty', '--match=v*'], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        result = p.communicate()[0]
        if p.returncode == 0:
            result = result.split()[0][1:]
        else:
            result = '0.0.0-%s' % len(subprocess.check_output(
                ['git', 'rev-list', 'HEAD']).splitlines())
        return result.replace('-', '.').replace('.g', '+g')
    return '0.0.0'


setup(name="poormanschema",
      version=get_version(),
      license="MIT",
      description="Very simple and effective schema checker",
      long_description=open('README.rst').read(),
      author="Benjamin Dauvergne",
      author_email="bdauvergne@entrouvert.com",
      py_modules=['poormanschema'],
      install_requires=['setuptools'],
      zip_safe=True,
      cmdclass={'sdist': eo_sdist})
