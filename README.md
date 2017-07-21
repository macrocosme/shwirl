![alt text](shwirl/docs/_static/shwirl_splash.png "Shwirl")

About shwirl
=============

**shwirl** is a custom standalone Python program to visualise spectral data cubes with ray-tracing volume rendering.
The program has been developed to investigate transfer functions and graphics shaders as enablers for
scientific visualisation of astronomical data. Details about transfer functions and shaders developed and implemented in
**shwirl** can be found in a full length article by [Vohl, Fluke, Barnes & Hassan (2017)](https://academic.oup.com/mnras/article-lookup/doi/10.1093/mnras/stx1676).

A transfer function is an arbitrary function that combines volumetric elements (or voxels) to set the colour,
intensity, or transparency level of each pixel in the final image. A graphics shader is an algorithmic kernel
used to compute several properties of the final image such as colour, depth, and/or transparency.
Shaders are particularly suited to computing transfer functions, and are an integral part of the graphics
pipeline on Graphics Processing Units.

The program utilises [Astropy](http://www.astropy.org) to handle FITS files and World Coordinate System, 
[Qt](http://www.qtcentre.org) (and [PyQt](https://www.riverbankcomputing.com/software/pyqt/download5)) for the user interface,
and [VisPy](http://vispy.org), an object-oriented Python visualisation library binding onto OpenGL.
We implemented the algorithms in the fragment shader using the GLSL language.

The software has been tested on Linux, Mac, and
Windows machines, including remote desktop on cloud computing infrastructure.
 
**Disclaimer**: While the software is available for
download and ready to visualise data, this is not intended as a full software release just yet. 

Documentation
-------------
Documentation can be found at [readthedocs](http://shwirl.readthedocs.io/en/latest/).

Installation
------------
You need Qt5, PyQt5. 
See documentation for more details. 

pip
---
When Qt and PyQt is installed, you can install via pip, e.g.

`pip3 install shwirl`

and run with 

`shwirl`

Issues, requests and general inquiries
--------------------------------------
Please send issues, feature requests and/or general inquiries to Dany Vohl via http://macrocosme.github.io/#contact.
You can also simply open a [new issue](https://github.com/macrocosme/shwirl/issues) on github directly.

License
-------
shwirl is licensed under the terms of the (new) BSD license. 
A copy of the license is included within this repository.

Copyright
---------
Copyright (c) 2017, Dany Vohl
All rights reserved.

