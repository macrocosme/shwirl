from distutils.core import setup

setup(
    name='test',
    version='0.1.1',
    packages=['extern', 'extern.vispy', 'extern.vispy.io', 'extern.vispy.io.tests', 'extern.vispy.app',
              'extern.vispy.app.tests', 'extern.vispy.app.backends', 'extern.vispy.app.backends.tests',
              'extern.vispy.app.backends.ipython', 'extern.vispy.ext', 'extern.vispy.ext._bundled',
              'extern.vispy.ext._bundled.cassowary', 'extern.vispy.gloo', 'extern.vispy.gloo.gl',
              'extern.vispy.gloo.gl.tests', 'extern.vispy.gloo.tests', 'extern.vispy.glsl', 'extern.vispy.glsl.math',
              'extern.vispy.glsl.misc', 'extern.vispy.glsl.lines', 'extern.vispy.glsl.arrows',
              'extern.vispy.glsl.markers', 'extern.vispy.glsl.antialias', 'extern.vispy.glsl.colormaps',
              'extern.vispy.glsl.arrowheads', 'extern.vispy.glsl.transforms', 'extern.vispy.glsl.collections',
              'extern.vispy.plot', 'extern.vispy.plot.tests', 'extern.vispy.util', 'extern.vispy.util.dpi',
              'extern.vispy.util.dpi.tests', 'extern.vispy.util.svg', 'extern.vispy.util.fonts',
              'extern.vispy.util.fonts.tests', 'extern.vispy.util.tests', 'extern.vispy.color',
              'extern.vispy.color.tests', 'extern.vispy.scene', 'extern.vispy.scene.tests',
              'extern.vispy.scene.cameras', 'extern.vispy.scene.cameras.tests', 'extern.vispy.scene.widgets',
              'extern.vispy.ipython', 'extern.vispy.testing', 'extern.vispy.testing.tests', 'extern.vispy.visuals',
              'extern.vispy.visuals.glsl', 'extern.vispy.visuals.line', 'extern.vispy.visuals.text',
              'extern.vispy.visuals.tests', 'extern.vispy.visuals.graphs', 'extern.vispy.visuals.graphs.tests',
              'extern.vispy.visuals.graphs.layouts', 'extern.vispy.visuals.filters', 'extern.vispy.visuals.shaders',
              'extern.vispy.visuals.shaders.tests', 'extern.vispy.visuals.transforms',
              'extern.vispy.visuals.transforms.tests', 'extern.vispy.visuals.collections', 'extern.vispy.geometry',
              'extern.vispy.geometry.tests', 'shwirl.shaders'],
    requires=['astropy', 'PyOpenGL'],
    # url='https://github.com/macrocosme/shwirl',
    url='',
    license='(new) BSD license',
    author='Dany Vohl',
    author_email='danyvohl@gmail.com',
    # description='Meaningful colouring of spectral cube data with volume rendering'
    description='packaging test'
)

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()
setup(
    name='shwirl',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.1.1',

    description='Meaningful colouring of spectral cube data with volume rendering',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/macrocosme/shwirl',

    # Author details
    author='Dany Vohl',
    author_email='danyvohl@gmail.com',

    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Scientific/Engineering :: Information Analysis',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: BSD License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    # What does your project relate to?
    keywords='visualisation astronomy spectral cubes',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=['extern', 'extern.vispy', 'extern.vispy.io', 'extern.vispy.io.tests', 'extern.vispy.app',
              'extern.vispy.app.tests', 'extern.vispy.app.backends', 'extern.vispy.app.backends.tests',
              'extern.vispy.app.backends.ipython', 'extern.vispy.ext', 'extern.vispy.ext._bundled',
              'extern.vispy.ext._bundled.cassowary', 'extern.vispy.gloo', 'extern.vispy.gloo.gl',
              'extern.vispy.gloo.gl.tests', 'extern.vispy.gloo.tests', 'extern.vispy.glsl', 'extern.vispy.glsl.math',
              'extern.vispy.glsl.misc', 'extern.vispy.glsl.lines', 'extern.vispy.glsl.arrows',
              'extern.vispy.glsl.markers', 'extern.vispy.glsl.antialias', 'extern.vispy.glsl.colormaps',
              'extern.vispy.glsl.arrowheads', 'extern.vispy.glsl.transforms', 'extern.vispy.glsl.collections',
              'extern.vispy.plot', 'extern.vispy.plot.tests', 'extern.vispy.util', 'extern.vispy.util.dpi',
              'extern.vispy.util.dpi.tests', 'extern.vispy.util.svg', 'extern.vispy.util.fonts',
              'extern.vispy.util.fonts.tests', 'extern.vispy.util.tests', 'extern.vispy.color',
              'extern.vispy.color.tests', 'extern.vispy.scene', 'extern.vispy.scene.tests',
              'extern.vispy.scene.cameras', 'extern.vispy.scene.cameras.tests', 'extern.vispy.scene.widgets',
              'extern.vispy.ipython', 'extern.vispy.testing', 'extern.vispy.testing.tests', 'extern.vispy.visuals',
              'extern.vispy.visuals.glsl', 'extern.vispy.visuals.line', 'extern.vispy.visuals.text',
              'extern.vispy.visuals.tests', 'extern.vispy.visuals.graphs', 'extern.vispy.visuals.graphs.tests',
              'extern.vispy.visuals.graphs.layouts', 'extern.vispy.visuals.filters', 'extern.vispy.visuals.shaders',
              'extern.vispy.visuals.shaders.tests', 'extern.vispy.visuals.transforms',
              'extern.vispy.visuals.transforms.tests', 'extern.vispy.visuals.collections', 'extern.vispy.geometry',
              'extern.vispy.geometry.tests', 'shwirl.shaders'],

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    #   py_modules=["my_module"],

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['astropy', 'PyOpenGL'],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    # extras_require={
    #     'dev': ['check-manifest'],
    #     'test': ['coverage'],
    # },

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={
        'sample': ['package_data.dat'],
    },

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    data_files=[('my_data', ['data/data_file'])],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'shwirl = shwirl.shwirl:main'
        ]
    },
)

