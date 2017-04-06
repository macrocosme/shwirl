About
=====

**Shwirl** is a custom standalone Python program to visualise spectral data cubes with ray-tracing volume rendering.
The program has been developed to investigate transfer functions and graphics shaders as enablers for
scientific visualisation of astronomical data. Details about transfer functions and shaders developed and implemented in
**shwirl** can be found in a full length article by Vohl, Fluke, Barnes & Hassan (Submitted).

A transfer function is an arbitrary function that combines volumetric elements (or voxels) to set the colour,
intensity, or transparency level of each pixel in the final image. A graphics shader is an algorithmic kernel
used to compute several properties of the final image such as colour, depth, and/or transparency.
Shaders are particularly suited to computing transfer functions, and are an integral part of the graphics
pipeline on Graphics Processing Units.

The code is available at https://github.com/macrocosme/shwirl. The program is built on top of `Astropy <http://www.astropy.org>`_
to handle FITS files and World Coordinate System, `Qt <http://www.qtcentre.org>`_ (and
`PyQt <https://www.riverbankcomputing.com/software/pyqt/download5>`_) for the user interface,
and `VisPy <http://vispy.org>`_, an object-oriented Python visualisation library binding onto OpenGL.
We implemented the algorithms in the fragment shader using the GLSL language.

The software has been used on Linux, Mac, and
Windows machines, including remote desktop on cloud computing infrastructure.

GPUs
----
Up to now, we have tested the code on NVIDIA GeForce GTX TITAN X, NVIDIA GeForce GT 750M, and NVIDIA GRID K1.
Rendering speed will vary depending on your hardware.

Issues, requests and general inquiries
--------------------------------------
Please send issues, feature requests and/or general inquiries to Dany Vohl via http://macrocosme.github.io/#contact.
You can also simply open a `new issue <https://github.com/macrocosme/shwirl/issues>`_ on github directly.