from setuptools import find_packages
from setuptools import setup

import os


version = '1.0alpha1'

setup(
    name='collective.sitter',
    version=version,
    description='Sitter agency',
    long_description=open('README.md').read()
    + '\n'
    + open(os.path.join('docs', 'HISTORY.txt')).read(),
    # Get more strings from
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Framework :: Plone',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='parents children kinder baby babysitter sitter agency pfleger nurse carer',
    author='Thomas Lotze (for starzel.de)',
    author_email='team@starzel.de',
    url='https://github.com/collective/collective.sitter',
    license='GPL version 2',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    namespace_packages=['collective'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'plone.app.dexterity',
        'plone.app.portlets',
        'plone.app.relationfield',
        'plone.autoform',
        'plone.formwidget.contenttree',
        'plone.namedfile',
        'plone.supermodel',
        'setuptools',
        'zope.formlib',
        'collective.taxonomy',
    ],
    extras_require={
        'test': [
            'plone.app.contenttypes[test]',
            'plone.app.testing',
            'plone.api',
        ],
    },
    entry_points={
        'z3c.autoinclude.plugin': 'target = plone',
    },
)
