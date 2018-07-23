from __future__ import division
import sys
from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from vispy import io

from .widgets.fits_meta_widget import FitsMetaWidget
from .widgets.group_widgets import GroupWidgets

from shwirl.visual.canvas import Canvas3D

class MainWindow(QMainWindow):
    """MainWindow class.

    This class manages the main Qt window. It includes the initialisation,
    and several functions to handle events.
    """
    def __init__(self, resolution):
        """Initialise the main window, set the basic layout, and connect signals (events handling).

        Parameters
        ----------
            resolution (list):  The resolution of the QWindow in pixel (e.g. appQt.desktop().screenGeometry())

        Returns:
            nothing.
        """
        QMainWindow.__init__(self)

        self.resize(resolution.width(), resolution.height())
        self.setWindowTitle('Shwirl')

        splitter_h = QSplitter(QtCore.Qt.Horizontal)
        splitter_v = QSplitter(QtCore.Qt.Vertical)

        # Menus / viz options
        self.widget_types = ['load_button', 'view', 'rendering_params', 'filtering', 'smoothing', 'image']
        self.widget_types_text = {'load_button': 'Import',
                                  'view': 'Camera and transforms',
                                  'rendering_params': 'Colour',
                                  'filtering': 'Filter',
                                  'smoothing': 'Smooth',
                                  'image': 'Export'}

        self.props = {}
        toolbox = QToolBox()
        for type in self.widget_types:
            self.props[type] = GroupWidgets(type)
            toolbox.addItem(self.props[type], self.widget_types_text[type])

        self.fits_infos = FitsMetaWidget()
        toolbox.addItem(self.fits_infos, 'Metadata')

        splitter_v.addWidget(toolbox)
        splitter_h.addWidget(splitter_v)

        self.setCentralWidget(splitter_h)

        # Histogram
        # self.Canvas2D = Canvas2D()
        # #self.Canvas2D.create_native()
        # self.Canvas2D.native.setParent(self)
        # splitter_v.addWidget(self.Canvas2D.native)

        # Main Canvas3D for 3D rendering
        self.Canvas3D = Canvas3D(resolution)
        self.Canvas3D.create_native()
        self.Canvas3D.native.setParent(self)
        splitter_h.addWidget(self.Canvas3D.native)
        splitter_h.setSizes([resolution.height(), int((resolution.width() / 3) * 5)])

        self.connect_signals()

        QApplication.setStyle(QStyleFactory.create('Cleanlooks'))

    def connect_signals(self):
        """Connect properties to signals.
        """
        # SIGNALS
        # Connect signals (events handling)
        self.props['load_button'].signal_file_loaded.connect(self.load_volume)

        self.props['view'].signal_objet_changed.connect(self.update_rendering_param)
        self.props['view'].signal_camera_changed.connect(self.update_view)
        self.props['view'].signal_fov_changed.connect(self.update_fov)
        self.props['view'].signal_autorotate_changed.connect(self.update_autorotate)
        self.props['view'].signal_scaling_changed.connect(self.update_scaling)
        # self.props['view'].signal_log_scale_changed.connect(self.update_log_scale)

        self.props['rendering_params'].signal_objet_changed.connect(self.update_rendering_param)
        self.props['rendering_params'].signal_threshold_changed.connect(self.update_threshold)
        self.props['rendering_params'].signal_density_factor_changed.connect(self.update_density_factor)
        # self.props.signal_color_scale_changed.connect(self.update_color_scale)

        self.props['smoothing'].signal_filter_size_changed.connect(self.update_filter_size)

        self.props['filtering'].signal_filter_type_changed.connect(self.update_filter_type)
        self.props['filtering'].signal_high_discard_filter_changed.connect(self.update_high_discard_filter)
        self.props['filtering'].signal_low_discard_filter_changed.connect(self.update_low_discard_filter)

        self.props['image'].signal_export_image.connect(self.export_image)

    def keyPressEvent(self, e):
        """Handle the event where a key is pressed.

        Parameters
        ----------
            e (event):  the event.

        """
        if e.key() == QtCore.Qt.Key_Escape:
            sys.exit(0)

    def load_volume(self):
        """Load a volume (3D array).

        This function calls the different functions implied when loading a volume.
        In particular, it transmits the data to the Canvas3D class (set_volume_scene),
        prints the HDU information, set the min and max values based on data, enables widgets,
        sets rendering parameters and view.
        """
        self.Canvas3D.set_volume_scene(self.props['load_button'].loaded_cube)
        self.fits_infos.print_header(self.props['load_button'].loaded_cube[0].header)

        for type in self.widget_types:
            print (type)
            self.props[type].update_discard_filter_text(self.props['load_button'].vol_min,
                                                        self.props['load_button'].vol_max)
            self.props[type].enable_widgets()
            # self.Canvas2D.set_histogram(self.props.loaded_cube)

            self.update_rendering_param()
            self.update_view()

    def update_rendering_param(self):
        """Update the rendering parameter.

        Transmits the updated rendering parameter to the Canvas3D class (Canvas3D.set_rendering_params). If the
        current transfer function is local maximum intensity projection (lmip), it also update the
        related threshold value.
        """
        self.Canvas3D.set_rendering_params(self.props['rendering_params'].combo_tf_method.currentText(),
                               self.props['rendering_params'].combo_cmap.currentText(),
                               self.props['rendering_params'].combo_color_method.currentText(),
                               self.props['rendering_params'].combo_interpolation_method.currentText())

        if self.props['rendering_params'].combo_tf_method.currentText() == 'lmip':
            self.update_threshold()

    def update_view(self):
        """Update the view parameters (e.g. camera, field of view)

        Transmits the updated view parameter to set the camera in the Canvas3D class (Canvas3D.set_camera).
        """
        self.Canvas3D.set_camera(self.props['view'].combo_camera.currentText(),
                                 self.props['view'].slider_fov.value())

    def update_fov(self):
        """Update field of view (fov)

        Transmits the value from the field of view slider to the Canvas3D class (Canvas3D.set_fov).
        """
        self.Canvas3D.set_fov(self.props['view'].slider_fov.value())

    def update_autorotate(self):
        """Update autorotate boolean value

        Transmits autorotate's checkbox value to the Canvas3D class (Canvas3D.set_autorotate).
        """
        self.Canvas3D.set_autorotate(self.props['view'].chk_autorotate.isChecked())

    def update_scaling(self):
        """Update scaling value for either axis

        Transmits the scaling sliders values to the Canvas3D class (Canvas3D.set_scaling).
        """
        self.Canvas3D.set_scaling(self.props['view'].slider_scalex.value(),
                                  self.props['view'].slider_scaley.value(),
                                  self.props['view'].slider_scalez.value())

    def update_threshold(self):
        """Update threshold value

        Transmits the threshold sliders value to the Canvas3D class (Canvas3D.set_threshold).
        """
        self.Canvas3D.set_threshold(self.props['rendering_params'].l_threshold_value.text())

    def update_color_scale(self):
        """Update color scale value

        Transmits the color scale combo box value to the Canvas3D class (Canvas3D.set_threshold).

        warning:

            Color scaling is not currently used. Some code is written, but not yet functional.
        """
        self.Canvas3D.set_color_scale(self.props['rendering_params'].combo_color_scale.currentText())

    def update_density_factor(self):
        """Update density factor value

        Transmits the density factor slider value to the Canvas3D class (Canvas3D.set_density_factor).
        This is used with the AVIP transfer function.
        """
        self.Canvas3D.set_density_factor(self.props['rendering_params'].l_density_factor_value.text())

    def update_filter_size(self):
        """Update the filter size value

        Transmits the box filter and gaussian filter size relevant values to the Canvas3D class
        (Canvas3D.set_box_filter_size, and Canvas3D.set_gaussian_filter respectively).
        """
        self.Canvas3D.set_box_filter_size(self.props['smoothing'].l_filter_size_value.text())
        self.Canvas3D.set_gaussian_filter(self.props['smoothing'].chk_use_gaussian_filter.isChecked(),
                                          self.props['smoothing'].combo_gaussian_filter_size.currentText())

    def update_filter_type(self):
        """Update the filter type

        This function is called when the filter type is changed in the GUI. It transmits the
        filter type to the Canvas3D class (Canvas3D.set_filter_type).
        """
        self.Canvas3D.set_filter_type(self.props['filtering'].combo_filter_type.currentText())

    def update_high_discard_filter(self):
        """Update the high discard filter value

        Transmits the high discard filter value, scaled value, and the type of filtering to the Canvas3D class
        (Canvas3D.set_high_discard_filter).
        """
        self.Canvas3D.set_high_discard_filter(self.props['filtering'].l_high_discard_filter_value.text(),
                                              self.props['filtering'].high_scaled_value,
                                              self.props['filtering'].combo_filter_type.currentText())

    def update_low_discard_filter(self):
        """Update the low discard filter value

        Transmits the low discard filter value, scaled value, and the type of filtering to the Canvas3D class
        (Canvas3D.set_low_discard_filter).
        """
        self.Canvas3D.set_low_discard_filter(self.props['filtering'].l_low_discard_filter_value.text(),
                                             self.props['filtering'].low_scaled_value,
                                             self.props['filtering'].combo_filter_type.currentText())

    def export_image(self):
        """Export an image of the view.

        Open a dialog window to decide where to save the image, and what name it should have. Then, saves the image.
        """
        fileName = QFileDialog.getSaveFileName(self,
                                               'Save still image',
                                               filter='Images (*.png)')
        if fileName[0] != '':
            img = self.Canvas3D.render()
            io.write_png(fileName[0], img)