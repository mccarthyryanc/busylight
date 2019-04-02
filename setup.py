from setuptools import setup, find_packages

print('PACKAGES: ',find_packages())

# Parse the version from the module.
with open('busylight/__init__.py') as f:
    for line in f:
        if line.find("__version__") >= 0:
            version = line.split("=")[1].strip()
            version = version.strip('"')
            version = version.strip("'")
            continue

setup(name='busylight',
      version=version,
      description='Package to interact with a Busylight',
      classifiers=[
        'Programming Language :: Python :: 3.6',
      ],
      keywords='busylight hid',
      author='Ryan McCarthy',
      author_email='ryan@mcginger.net',
      license='MIT License',
      install_requires=[
        'click',
        'numpy',
        'hidapi',
      ],
      setup_requires=['pytest-runner'],
      tests_require=['pytest'],
      package_dir={'': '.'},
      packages=find_packages(),
      entry_points='''
        [console_scripts]
        busylight=busylight.scripts.busycli:cli
      ''',
      include_package_data=True,
      zip_safe=False)
