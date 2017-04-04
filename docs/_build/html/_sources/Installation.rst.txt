Installation
============

Prerequisites
-------------

**Shwirl** utilises `Astropy <http://www.astropy.org>`_
to handle FITS files and World Coordinate System, `Qt <http://www.qtcentre.org>`_ (and
`PyQt <https://www.riverbankcomputing.com/software/pyqt/download5>`_) for the user interface,
and `VisPy <http://vispy.org>`_, an object-oriented Python visualisation library binding onto OpenGL.

These are pre-requisites to be able to use the software.

In particular, current version relies on Python 3 and PyQt5. A bundled version of VisPy is included in the *extern*
repository as custom modifications have been made that are not readily available via the official version.

Example installation procedure
------------------------------

Depending on your operating system and your current configuration, installation steps may vary.
In general, you can install it using the following:

First, install Qt5. It can be downloaded via the `Qt website <qt-project.org/qt5>`_.
Then, install the following python packages: Astropy, PyOpenGL, and PyQt5. These can be installed in a number of ways,
including from source or via python package managers like *pip3*. For example:

.. code:: console

  pip3 install astropy
  pip3 install PyOpenGL
  pip3 install PyQt5

Go download **shwirl** from `GitHub <https://github.com/macrocosme/shwirl>`_. This can be done from
GitHub itself using buttons, or via git (e.g. `git clone https://github.com/macrocosme/shwirl.git`).

Once everything is installed/downloaded, you should be able to start **shwirl**'s the Graphical User Interface (GUI) via something like:

.. code:: console

  python3 shwirl.py

Python 2.7 / PyQt4 users
------------------------
PyQt4 (and Python 2.7) are also supported.



