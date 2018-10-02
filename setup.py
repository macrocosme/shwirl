# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
# with open(path.join(here, 'README.md'), encoding='utf-8') as f:
#     long_description = f.read()

package_data = {'.images': ['*.png']}

for subpackage in ['antialias', 'arrowheads', 'arrows', 'collections',
                   'colormaps', 'lines', 'markers', 'math', 'misc',
                   'transforms']:
    package_data['.extern.vispy.glsl.' + subpackage] = ['*.vert','*.frag', "*.glsl"]

for subpackage in ['.extern.vispy.io._data']:
    package_data[subpackage] = ['*.npy', '*.*']

setup(
    name='shwirl',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.1.13',

    description='Meaningful colouring of spectral cube data with volume rendering',
    # long_description=long_description,

    # The project's main homepage.
    url='https://github.com/macrocosme/shwirl',
    # url='',

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
    packages=['shwirl.images', 'shwirl.extern', 'shwirl.extern.vispy', 'shwirl.extern.vispy.io', 'shwirl.extern.vispy.io.tests',
              'shwirl.extern.vispy.io._data', 'shwirl.extern.vispy.app',
              'shwirl.extern.vispy.app.tests', 'shwirl.extern.vispy.app.backends', 'shwirl.extern.vispy.app.backends.tests',
              'shwirl.extern.vispy.app.backends.ipython', 'shwirl.extern.vispy.ext', 'shwirl.extern.vispy.ext._bundled',
              'shwirl.extern.vispy.ext._bundled.cassowary', 'shwirl.extern.vispy.gloo', 'shwirl.extern.vispy.gloo.gl',
              'shwirl.extern.vispy.gloo.gl.tests', 'shwirl.extern.vispy.gloo.tests', 'shwirl.extern.vispy.glsl', 'shwirl.extern.vispy.glsl.math',
              'shwirl.extern.vispy.glsl.misc', 'shwirl.extern.vispy.glsl.lines', 'shwirl.extern.vispy.glsl.arrows',
              'shwirl.extern.vispy.glsl.markers', 'shwirl.extern.vispy.glsl.antialias', 'shwirl.extern.vispy.glsl.colormaps',
              'shwirl.extern.vispy.glsl.arrowheads', 'shwirl.extern.vispy.glsl.transforms', 'shwirl.extern.vispy.glsl.collections',
              'shwirl.extern.vispy.plot', 'shwirl.extern.vispy.plot.tests', 'shwirl.extern.vispy.util', 'shwirl.extern.vispy.util.dpi',
              'shwirl.extern.vispy.util.dpi.tests', 'shwirl.extern.vispy.util.svg', 'shwirl.extern.vispy.util.fonts',
              'shwirl.extern.vispy.util.fonts.tests', 'shwirl.extern.vispy.util.tests', 'shwirl.extern.vispy.color',
              'shwirl.extern.vispy.color.tests', 'shwirl.extern.vispy.scene', 'shwirl.extern.vispy.scene.tests',
              'shwirl.extern.vispy.scene.cameras', 'shwirl.extern.vispy.scene.cameras.tests', 'shwirl.extern.vispy.scene.widgets',
              'shwirl.extern.vispy.ipython', 'shwirl.extern.vispy.testing', 'shwirl.extern.vispy.testing.tests', 'shwirl.extern.vispy.visuals',
              'shwirl.extern.vispy.visuals.glsl', 'shwirl.extern.vispy.visuals.line', 'shwirl.extern.vispy.visuals.text',
              'shwirl.extern.vispy.visuals.tests', 'shwirl.extern.vispy.visuals.graphs', 'shwirl.extern.vispy.visuals.graphs.tests',
              'shwirl.extern.vispy.visuals.graphs.layouts', 'shwirl.extern.vispy.visuals.filters', 'shwirl.extern.vispy.visuals.shaders',
              'shwirl.extern.vispy.visuals.shaders.tests', 'shwirl.extern.vispy.visuals.transforms',
              'shwirl.extern.vispy.visuals.transforms.tests', 'shwirl.extern.vispy.visuals.collections', 'shwirl.extern.vispy.geometry',
              'shwirl.extern.vispy.geometry.tests', 'shwirl.shaders', 'shwirl'],

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    #   py_modules=["my_module"],

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['scipy', 'numpy', 'astropy', 'PyOpenGL', 'six'],

    include_package_data=True,

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
    package_data=package_data,

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    data_files=[],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'shwirl = shwirl.shwirl:main'
        ]
    },
)

