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

First, install Qt5. It can be downloaded via the `Qt website <qt-project.org/qt5>`_. You also need PyQt5,
which can be installed via a package manager like pip, brew, etc. E.g.

.. code:: console

  pip3 install PyQt5

Install with pip
~~~~~~~~~~~~~~~~
You can install **shwirl** with pip:

.. code:: console

  pip3 install shwirl

Once installed, in your terminal, you can launch **shwirl** by typing:

.. code:: console

  shwirl

Python 2.7 / PyQt4 users
------------------------
PyQt4 (and Python 2.7) are also supported.



