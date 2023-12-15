from setuptools import find_packages
from setuptools import setup

import os


version = '1.0a1'

setup(
    name='collective.sitter',
    version=version,
    description='Sitter agency',
    long_description=open('README.md').read()
    + '\n'
    + open(os.path.join('docs', 'HISTORY.txt')).read(),
    # Get more strings from
    # https://pypi.org/pypi?%3Aaction=list_classifiers
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
        'beautifulsoup4',
        'collective.taxonomy',
        'eea.facetednavigation',
        'plone.app.z3cform',
        'plone.autoform',
        'plone.dexterity',
        'plone.namedfile',
        'plone.supermodel',
        'plone.z3cform',
        'setuptools',
        'z3c.form',
        'z3c.jbot',
        'z3c.relationfield',
        'zope.formlib',
        'collective.z3cform.datagridfield',
    ],
    extras_require={
        'test': [
            'Products.Sessions[tests]',
            'plone.app.contenttypes[test]',
            'plone.app.testing',
            'plone.testing',
        ],
    },
    entry_points={
        'z3c.autoinclude.plugin': 'target = plone',
    },
)
