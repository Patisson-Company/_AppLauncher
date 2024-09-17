from setuptools import setup, find_packages

setup(
    name='patisson_appLauncher',
    version='0.3.0',
    packages=find_packages(),
    author='EliseyGodX',
    description='tools for connecting and managing Consul',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Patisson-Company/_AppLauncher',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.11',
)