"""
Setup script for Django Boilerplate CLI.
"""
from setuptools import setup, find_packages
import os

# Read README file
current_dir = os.path.dirname(os.path.abspath(__file__))
readme_path = os.path.join(current_dir, 'README.md')

with open(readme_path, 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='django-boilerplate-cli',
    version='1.0.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='CLI tool to create Django projects from a modern boilerplate',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/camcoder337/django-boilerplate',
    packages=find_packages(),
    py_modules=['create_django_project'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Code Generators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Framework :: Django',
        'Framework :: Django :: 5.0',
    ],
    python_requires='>=3.9',
    install_requires=[
        # No additional requirements - uses only stdlib
    ],
    entry_points={
        'console_scripts': [
            'create-django-project=create_django_project:main',
            'django-boilerplate=create_django_project:main',
        ],
    },
    keywords='django, boilerplate, cli, project-generator, web-development',
    project_urls={
        'Bug Reports': 'https://github.com/camcoder337/django-boilerplate/issues',
        'Source': 'https://github.com/camcoder337/django-boilerplate',
        'Documentation': 'https://github.com/camcoder337/django-boilerplate#readme',
    },
)