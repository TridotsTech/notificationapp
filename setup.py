# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
try: # for pip >= 10
	from pip._internal.req import parse_requirements
except ImportError: # for pip <= 9.0.3
	from pip.req import parse_requirements
import re, ast

# get version from __version__ variable in notification/__init__.py
_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('notification/__init__.py', 'rb') as f:
	version = str(ast.literal_eval(_version_re.search(
		f.read().decode('utf-8')).group(1)))

#requirements = parse_requirements("requirements.txt", session="")
with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

setup(
	name='notification',
	version=version,
	description='for sms, email and mobile notification',
	author='Tridots Tech Private Ltd.',
	author_email='info@valiantsystems.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
	# install_requires=[str(ir.req) for ir in requirements],
	# dependency_links=[str(ir._link) for ir in requirements if ir._link]
)
