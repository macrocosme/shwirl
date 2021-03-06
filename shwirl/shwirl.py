# -*- coding: utf-8 -*-
from __future__ import division

# Basic imports
import sys
import numpy as np

# Vispy imports
from .extern.vispy import app, scene, io
from .extern.vispy.color import get_colormaps
from .extern.vispy.gloo import gl
from .shaders import RenderVolume
from .shaders.axes import AxesVisual3D
# Astropy imports
from astropy.io import fits
from blimpy import Waterfall

# PyQt5 imports
try:
    from PyQt5 import QtGui, QtCore, QtWidgets
    from PyQt5.QtWidgets import *
    from PyQt5.QtGui import QColor, QPixmap
    from PyQt5.QtCore import Qt, pyqtSignal
except:
    try:
        try:
            from sip import setapi

            setapi("QVariant", 2)
            setapi("QString", 2)
        except ImportError:
            pass

        from PyQt4 import QtGui, QtCore
        from PyQt4.QtCore import Qt, pyqtSignal
        from PyQt4.QtGui import *
    except:
        print ("Requires PyQt5 or PyQt4. None found.")
        exit()

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

        # self.resize(1800, 1000)
        self.resize(resolution.width(), resolution.height())
        self.setWindowTitle('Shwirl')

        splitter_h = QSplitter(Qt.Horizontal)
        splitter_v = QSplitter(Qt.Vertical)

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
            self.props[type] = ObjectWidget(type)
            toolbox.addItem(self.props[type], self.widget_types_text[type])

        self.fits_infos = FitsMetaWidget()
        toolbox.addItem(self.fits_infos, 'Metadata')

        splitter_v.addWidget(toolbox)
        splitter_h.addWidget(splitter_v)

        self.setCentralWidget(splitter_h)

        self.Canvas3D = Canvas3D(resolution)
        self.Canvas3D.create_native()
        self.Canvas3D.native.setParent(self)

        # Main Canvas3D for 3D rendering
        splitter_h.addWidget(self.Canvas3D.native)

        splitter_h.setSizes([resolution.height(), int((resolution.width() / 3) * 5)])


        # Connect signals (events handling)
        self.props['load_button'].signal_file_loaded.connect(self.load_volume)

        # self.props['load_button'].signal_objet_changed.connect(self.update_rendering_param)
        self.props['view'].signal_objet_changed.connect(self.update_rendering_param)
        self.props['rendering_params'].signal_objet_changed.connect(self.update_rendering_param)

        # self.props['load_button'].signal_camera_changed.connect(self.update_view)
        self.props['view'].signal_camera_changed.connect(self.update_view)
        self.props['view'].signal_fov_changed.connect(self.update_fov)

        self.props['view'].signal_autorotate_changed.connect(self.update_autorotate)
        # self.props['view'].signal_log_scale_changed.connect(self.update_log_scale)
        self.props['view'].signal_scaling_changed.connect(self.update_scaling)
        self.props['rendering_params'].signal_threshold_changed.connect(self.update_threshold)
        self.props['rendering_params'].signal_density_factor_changed.connect(self.update_density_factor)
        # self.props.signal_color_scale_changed.connect(self.update_color_scale)
        self.props['smoothing'].signal_filter_size_changed.connect(self.update_filter_size)
        self.props['filtering'].signal_filter_type_changed.connect(self.signal_filter_type)
        self.props['filtering'].signal_high_discard_filter_changed.connect(self.update_high_discard_filter)
        self.props['filtering'].signal_low_discard_filter_changed.connect(self.update_low_discard_filter)
        self.props['image'].signal_export_image.connect(self.export_image)

        QApplication.setStyle(QStyleFactory.create('Cleanlooks'))

    def keyPressEvent(self, e):
        """Handle the event where a key is pressed.

        Parameters
        ----------
            e (event):  the event.

        """
        if e.key() == QtCore.Qt.Key_Escape:
            print ("blabla")
            self.app.quit()

    def load_volume(self):
        """Load a volume (3D array).

        This function calls the different functions implied when loading a volume.
        In particular, it transmits the data to the Canvas3D class (set_volume_scene),
        prints the HDU information, set the min and max values based on data, enables widgets,
        sets rendering parameters and view.
        """
        self.Canvas3D.set_volume_scene(self.props['load_button'].loaded_cube)
        try:
            self.fits_infos.print_header(self.props['load_button'].loaded_cube[0].header, 'fits')
        except:
            # This is shady. The type should be properly assessed.
            self.fits_infos.print_header(self.props['load_button'].loaded_cube.header, 'filterbank')
            pass

        for type in self.widget_types:
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

    def signal_filter_type(self):
        """Qt signal - filter type

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


class FitsMetaWidget(QWidget):
    """Widget to render the FITS HDU information"""

    def __init__(self, parent=None):
        """Initialise the layout, including QTextEdit widget.
        """
        super(FitsMetaWidget, self).__init__(parent)

        l_title = QLabel("Fits Primary Header")

        self.l_header = QTextEdit("No fits loaded ")
        self.l_header.setReadOnly(True)

        font = self.l_header.font()
        font.setFamily("Avenir")
        font.setPointSize(12)

        gbox = QGridLayout()
        # ------ Adding Widgets
        gbox.addWidget(l_title, 0, 1)
        gbox.addWidget(self.l_header, 1, 1)

        vbox = QVBoxLayout()
        vbox.addLayout(gbox)
        vbox.addStretch(1.0)

        self.setLayout(vbox)

    def print_header(self, header, type='fits'):
        """Print the Primary HDU information of the fits file

        Parameters
        ----------
            header : astropy.io.fits.header, dict
                HDU taken from a fits file.
        """
        self.l_header.clear()
        if type=='fits':
            self.l_header.insertPlainText('card\tvalue\tcomment\n')
            for card in header.cards:
                self.l_header.setTextColor(QColor('blue'))
                self.l_header.insertPlainText(str(card[0]) + "\t")
                self.l_header.setTextColor(QColor('black'))
                self.l_header.insertPlainText(str(card[1]) + "\t")
                self.l_header.setTextColor(QColor('red'))
                self.l_header.insertPlainText(str(card[2]) + "\n")
        elif type=='filterbank':
            self.l_header.insertPlainText('card\t\tvalue\n')
            for key in header.keys():
                self.l_header.setTextColor(QColor('blue'))
                self.l_header.insertPlainText("%s\t\t" % (key))
                self.l_header.setTextColor(QColor('black'))
                self.l_header.insertPlainText("%s\n" % (str(header[key])))


        sb = self.l_header.verticalScrollBar()
        sb.setValue(sb.maximum())


class ObjectWidget(QWidget):
    """Class for the object widget creating the Qt signals
    """
    signal_objet_changed = pyqtSignal(name='objectChanged')
    signal_file_loaded = pyqtSignal(name='fileLoaded')
    signal_camera_changed = pyqtSignal(name='cameraChanged')
    signal_fov_changed = pyqtSignal(name='fovChanged')
    signal_autorotate_changed = pyqtSignal(name='autorotateChanged')
    # signal_log_scale_changed = pyqtSignal(name='log_scaleChanged')
    signal_scaling_changed = pyqtSignal(name='scalingChanged')
    signal_threshold_changed = pyqtSignal(name='thresholdChanged')
    signal_color_scale_changed = pyqtSignal(name='color_scaleChanged')
    signal_filter_size_changed = pyqtSignal(name='filter_sizeChanged')
    signal_filter_type_changed = pyqtSignal(name='filter_typeChanged')
    signal_high_discard_filter_changed = pyqtSignal(name='high_discard_filterChanged')
    signal_low_discard_filter_changed = pyqtSignal(name='low_discard_filterChanged')
    signal_density_factor_changed = pyqtSignal(name='density_factorChanged')
    signal_export_image = pyqtSignal(name='export_image')

    def __init__(self, type, parent=None):
        """Initialise the ObjectWidget class

        Instanciate the widget's components for a given `type` of widget.

        Parameters
        -----------
            type : str
                Type of widget (one of MainWindow.widget_types).

            parent : class
                Parent class.
        """
        super(ObjectWidget, self).__init__(parent)

        self.loaded_cube = None

        self.widgets_array = []
        self.widgets_dict = {}
        self.widgets_group_dict = {}
        self.widgets_group_array = []

        def serialize_widgets(key, group, array):
            """Serialize widgets

            Add a new widget to a widget array using its key, and a group it belongs to.

            Parameters
            ----------
            key : str
                Key used to describe the widget
            group : str
            array : list
            """
            self.widgets_array.append(array)
            self.widgets_dict[key] = array
            try:
                self.widgets_group_dict[group].append([key, array])
            except:
                self.widgets_group_array.append(group)
                self.widgets_group_dict[group] = []
                self.widgets_group_dict[group].append([key, array])

        if type == 'load_button':
            self.load_button = QPushButton("Load Spectral Cube", self)
            self.load_button.clicked.connect(self.showLoadFitsDialog)
            array = [self.load_button]
            serialize_widgets('fits_button', '', array)

        elif type == 'view':
            l_cam = QLabel("camera ")
            self.camera = ['Turntable', 'Fly', 'Arcball']  # 'Perspectivecamera',
            self.combo_camera = QComboBox(self)
            self.combo_camera.addItems(self.camera)
            self.combo_camera.currentIndexChanged.connect(self.update_view)
            array = [l_cam, self.combo_camera]
            serialize_widgets('camera', '', array)

            self.chk_autorotate = QCheckBox("Autorotate")
            self.chk_autorotate.setChecked(False)
            self.chk_autorotate.stateChanged.connect(self.update_autorotate)
            array = [self.chk_autorotate]
            serialize_widgets('autorotate', '', array)

            # self.chk_log_scale = QCheckBox("Log scale")
            # self.chk_log_scale.setChecked(False)
            # self.chk_log_scale.stateChanged.connect(self.update_log_scale)
            # array = [self.chk_log_scale]
            # serialize_widgets('log_scale', array)

            l_fov = QLabel("Field of View ")
            self.slider_fov = QSlider(Qt.Horizontal, self)
            self.slider_fov.setMinimum(0)
            self.slider_fov.setMaximum(160)
            self.slider_fov.setValue(60)
            self.slider_fov.setTickInterval(5)
            self.l_fov_value = QLineEdit(str(self.slider_fov.value()))
            self.slider_fov.valueChanged.connect(self.update_fov)
            array = [l_fov, self.slider_fov, self.l_fov_value]
            serialize_widgets('field_of_view', '', array)

            l_scalex = QLabel("Scale X ")
            self.slider_scalex = QSlider(Qt.Horizontal, self)
            self.slider_scalex.setMinimum(1)
            self.slider_scalex.setMaximum(20)
            self.slider_scalex.setValue(1)
            self.slider_scalex.setTickInterval(1)
            self.l_scalex_value = QLineEdit(str(self.slider_scalex.value()))
            self.slider_scalex.valueChanged.connect(self.update_scaling)
            array = [l_scalex, self.slider_scalex, self.l_scalex_value]
            serialize_widgets('scale_x', '', array)

            l_scaley = QLabel("Scale Y ")
            self.slider_scaley = QSlider(Qt.Horizontal, self)
            self.slider_scaley.setMinimum(1)
            self.slider_scaley.setMaximum(20)
            self.slider_scaley.setValue(1)
            self.slider_scaley.setTickInterval(1)
            self.l_scaley_value = QLineEdit(str(self.slider_scaley.value()))
            self.slider_scaley.valueChanged.connect(self.update_scaling)
            array = [l_scaley, self.slider_scaley, self.l_scaley_value]
            serialize_widgets('scale_y', '', array)

            l_scalez = QLabel("Scale Z ")
            self.slider_scalez = QSlider(Qt.Horizontal, self)
            self.slider_scalez.setMinimum(1)
            self.slider_scalez.setMaximum(20)
            self.slider_scalez.setValue(1)
            self.slider_scalez.setTickInterval(1)
            self.l_scalez_value = QLineEdit(str(self.slider_scalez.value()))
            self.slider_scalez.valueChanged.connect(self.update_scaling)
            array = [l_scalez, self.slider_scalez, self.l_scalez_value]
            serialize_widgets('scale_z', '', array)

        elif type == 'rendering_params':
            l_tf_method = QLabel("Transfer function ")
            # self.l_tf_method = ['mip', 'translucent', 'translucent2', 'iso', 'additive']
            self.tf_method = ['mip', 'lmip', 'avip', 'iso', 'minip']
            self.combo_tf_method = QComboBox(self)
            self.combo_tf_method.addItems(self.tf_method)
            self.combo_tf_method.currentIndexChanged.connect(self.update_param)
            array = [l_tf_method, self.combo_tf_method]
            serialize_widgets('tf_method', '', array)

            l_density_factor = QLabel("Density regulator ")
            self.slider_density_factor = QSlider(Qt.Horizontal, self)
            self.slider_density_factor.setMinimum(0)
            self.slider_density_factor.setMaximum(10000)
            self.slider_density_factor.setValue(0)
            self.l_density_factor_value = QLineEdit(str(1))
            self.slider_density_factor.valueChanged.connect(self.update_density_factor)
            array = [l_density_factor, self.slider_density_factor, self.l_density_factor_value]
            serialize_widgets('density_factor', '', array)
            for widget in self.widgets_dict['density_factor']:
                widget.hide()

            l_color_method = QLabel("Colour method ")
            self.color_method = ['Moment 0', 'Moment 1', 'Sigmas', 'rgb_cube']
            self.combo_color_method = QComboBox(self)
            self.combo_color_method.addItems(self.color_method)
            self.combo_color_method.currentIndexChanged.connect(self.update_param)
            array = [l_color_method, self.combo_color_method]
            serialize_widgets('color_method', '', array)

            l_threshold = QLabel("Threshold ")
            self.slider_threshold = QSlider(Qt.Horizontal, self)
            self.slider_threshold.setMinimum(0)
            self.slider_threshold.setMaximum(10000)
            self.slider_threshold.setValue(10000)
            self.l_threshold_value = QLineEdit(str(self.slider_threshold.value()))
            self.slider_threshold.valueChanged.connect(self.update_threshold)
            array = [l_threshold, self.slider_threshold, self.l_threshold_value]
            serialize_widgets('threshold', '', array)
            for widget in self.widgets_dict['threshold']:
                widget.hide()

            l_interpolation_method = QLabel("Interpolation method ")
            self.interpolation_method = ['linear', 'nearest']  # ,
            # 'bilinear', 'hanning', 'hamming', 'hermite',
            # 'kaiser', 'quadric', 'bicubic', 'catrom',
            # 'mitchell', 'spline16', 'spline36', 'gaussian',
            # 'bessel', 'sinc', 'lanczos', 'blackman']
            self.combo_interpolation_method = QComboBox(self)
            self.combo_interpolation_method.addItems(self.interpolation_method)
            self.combo_interpolation_method.currentIndexChanged.connect(self.update_param)
            array = [l_interpolation_method, self.combo_interpolation_method]
            serialize_widgets('interpolation_method', '', array)

            l_cmap = QLabel("Colour map ")
            self.cmap = sorted(list(get_colormaps().keys()), key=str.lower)
            self.combo_cmap = QComboBox(self)
            self.combo_cmap.addItems(self.cmap)
            self.combo_cmap.setCurrentIndex(self.cmap.index('hsl'))
            self.combo_cmap.currentIndexChanged.connect(self.update_param)
            array = [l_cmap, self.combo_cmap]
            serialize_widgets('cmap', '', array)

        # l_color_scale = QLabel("Color scale ")
        # self.color_scale = ['linear', 'log', 'exp']
        # self.combo_color_scale = QComboBox(self)
        # self.combo_color_scale.addItems(self.color_scale)
        # self.combo_color_scale.currentIndexChanged.connect(self.update_color_scale)
        # array = [l_color_scale, self.combo_color_scale]
        # serialize_widgets('color_scale', array)

        elif type == 'smoothing':
            l_filter_size = QLabel("Box size")
            self.slider_filter_size = QSlider(Qt.Horizontal, self)
            self.slider_filter_size.setMinimum(0)
            self.slider_filter_size.setMaximum(5)
            self.slider_filter_size.setValue(0)
            self.l_filter_size_value = QLineEdit(str(self.slider_filter_size.value() + 1))
            self.slider_filter_size.valueChanged.connect(self.update_filter_size)
            array = [l_filter_size, self.slider_filter_size, self.l_filter_size_value]
            serialize_widgets('filter_size', '', array)

            # l_use_gaussian_filter = QLabel("Activate Gaussian smoothing")
            # self.use_gaussian_filter = ['0', '1']  # 'Perspectivecamera',
            # self.combo_use_gaussian_filter = QComboBox(self)
            # self.combo_use_gaussian_filter.addItems(self.use_gaussian_filter)
            # self.combo_use_gaussian_filter.currentIndexChanged.connect(self.update_gaussian_filter_size)
            # array = [l_use_gaussian_filter, self.combo_use_gaussian_filter]
            # serialize_widgets('use_gaussian_filter', array)

            l_gaussian_filter_size = QLabel("Gaussian size")
            self.chk_use_gaussian_filter = QCheckBox("Activate")
            self.chk_use_gaussian_filter.setChecked(False)
            self.chk_use_gaussian_filter.stateChanged.connect(self.update_gaussian_filter_size)
            self.gaussian_filter_size = ['5', '9', '13']  # 'Perspectivecamera',
            self.combo_gaussian_filter_size = QComboBox(self)
            self.combo_gaussian_filter_size.addItems(self.gaussian_filter_size)
            self.combo_gaussian_filter_size.currentIndexChanged.connect(self.update_gaussian_filter_size)
            array = [l_gaussian_filter_size, self.combo_gaussian_filter_size, self.chk_use_gaussian_filter]
            serialize_widgets('gaussian_filter_size', '', array)

        elif type == 'filtering':
            l_filter_type = QLabel("Filter type")
            self.filter_type = ['Filter out', 'Rescale']  # 'Perspectivecamera',
            self.combo_filter_type = QComboBox(self)
            self.combo_filter_type.addItems(self.filter_type)
            self.combo_filter_type.currentIndexChanged.connect(self.update_filter_type)
            array = [l_filter_type, self.combo_filter_type]
            serialize_widgets('filter_type', '', array)

            l_high_discard_filter = QLabel("high filter ")
            self.slider_high_discard_filter = QSlider(Qt.Horizontal, self)
            self.slider_high_discard_filter.setMinimum(0)
            self.slider_high_discard_filter.setMaximum(10000)
            self.slider_high_discard_filter.setValue(10000)
            self.l_high_discard_filter_value = QLineEdit(str(self.slider_high_discard_filter.value()))
            self.slider_high_discard_filter.valueChanged.connect(self.update_high_discard_filter)
            array = [l_high_discard_filter, self.slider_high_discard_filter, self.l_high_discard_filter_value]
            serialize_widgets('high_discard_filter', '', array)
            # for widget in self.widgets_dict['high_discard_filter']:
            #     widget.hide()

            l_low_discard_filter = QLabel("Low filter ")
            self.slider_low_discard_filter = QSlider(Qt.Horizontal, self)
            self.slider_low_discard_filter.setMinimum(0)
            self.slider_low_discard_filter.setMaximum(10000)
            self.slider_low_discard_filter.setValue(0)
            self.l_low_discard_filter_value = QLineEdit(str(self.slider_low_discard_filter.value()))
            self.slider_low_discard_filter.valueChanged.connect(self.update_low_discard_filter)
            array = [l_low_discard_filter, self.slider_low_discard_filter, self.l_low_discard_filter_value]
            serialize_widgets('low_discard_filter', '', array)

        elif type == 'image':
            self.export_image_button = QPushButton("Save image to...", self)
            self.export_image_button.clicked.connect(self.export_image)
            array = [self.export_image_button]
            serialize_widgets('export_image', '', array)

        # for group in self.widgets_group_array:
        # groupboxes = []
        # groupbox = QGroupBox(group)

        # Add widgets to the grid layout, which is added to the box, which is added to the group.
        widgets_i = 0
        gbox2 = QGridLayout()
        group_i = 0
        for group in self.widgets_group_array:
            groupbox = QGroupBox(group)
            gbox = QGridLayout()
            # toolbox = QToolBox()
            for key, widgets in self.widgets_group_dict[group]:
            # for widgets in self.widgets_array:
                widget_i = 1
                for widget in widgets:

                    gbox.addWidget(widget, widgets_i, widget_i)
                    # toolbox.addItem(widget, key)
                    if type != 'load_button':
                    # if widgets_i > 0:
                        widget.setEnabled(False)

                    widget_i += 1
                widgets_i += 1

            # groupbox.setLayout(gridbox)
            groupbox.setLayout(gbox)

            # toolbox.addItem(gbox)
            gbox2.addWidget(groupbox, group_i, 0)
            group_i += 1

        vbox = QVBoxLayout()
        # vbox.addItem(gbox2)
        vbox.addItem(gbox2)
        vbox.addStretch(1.0)

        self.setLayout(vbox)

    def update_param(self):
        """Update parameter related to a given transfer function.
        """
        if self.combo_tf_method.currentText() in ['avip', 'translucent2']:
            for widget in self.widgets_dict['density_factor']:
                widget.show()
        else:
            for widget in self.widgets_dict['density_factor']:
                widget.hide()

        if self.combo_tf_method.currentText() == 'lmip' or self.combo_tf_method.currentText() == 'iso':
            for widget in self.widgets_dict['threshold']:
                widget.show()
        else:
            for widget in self.widgets_dict['threshold']:
                widget.hide()

        self.signal_objet_changed.emit()

    def clean_data(self, data, threshold_time=3.25, threshold_frequency=2.75, bin_size=32,
                  n_iter_time=3, n_iter_frequency=3, clean_type='time'):
        """ Take filterbank object and mask
        RFI time samples with average spectrum.
        Parameters:
        ----------
        data :
            filterbank data object
        threshold_time : float
            units of sigma
        threshold_frequency : float
            units of sigma
        bin_size : int
            quantization bin size
        n_iter_time : int
            Number of iteration for time cleaning
        n_iter_frequency : int
            Number of iteration for frequency cleaning
        clean_type : str
            type of cleaning to be done.
            Accepted values: 'time', 'frequency', 'both'
        Returns:
        -------
        cleaned filterbank object
        """
        # Clean in time
        print (type(data))
        print(data.shape)

        if clean_type in ['time', 'both']:
            for i in range(n_iter_time):
                dfmean = np.mean(data, axis=0)
                dtmean = np.mean(data, axis=1)

                # ('data.data', (1536, 265149), 'dfmean', (265149,), 'dtmean', (1536,))

                stdevf = np.std(dfmean)
                medf = np.median(dfmean)
                maskf = np.where(np.abs(dfmean - medf) > threshold_time * stdevf)[0]

                # replace with mean spectrum
                data[:, maskf] = dtmean[:, None] * np.ones(len(maskf))[None]

        # Clean in frequency
        # remove bandpass by averaging over bin_size ajdacent channels
        if clean_type in ['frequency', 'both']:
            for i in range(n_iter_frequency):
                for i in range(data.shape[1]):
                    dtmean_nobandpass = data[:, i] - dtmean.reshape(-1, bin_size).mean(-1).repeat(bin_size)
                    stdevt = np.std(dtmean_nobandpass)
                    medt = np.median(dtmean_nobandpass)
                    maskt = np.abs(dtmean_nobandpass - medt) > threshold_frequency * stdevt

                    # replace with mean bin values
                    data[maskt, i] = dtmean.reshape(-1, bin_size).mean(-1).repeat(bin_size)[maskt]
        return data

    def showLoadFitsDialog(self):
        """Show the dialog window to load a fits file.
        """
        filename = QFileDialog.getOpenFileName(self,
                                               'Open file',
                                               filter='FITS Images (*.fits, *.FITS)')
                                               #filter='FITS Images (*.fits, *.FITS); SigProc Filterbank (*.fil)')

        if filename[0] != "":
            if filename[0].split('.')[-1] in ['fits', 'FITS']:
                # Load file
                # print(filename)
                self.loaded_cube = fits.open(filename[0])

                try:
                    self.vol_min = self.loaded_cube[0].header["DATAMIN"]
                    self.vol_max = self.loaded_cube[0].header["DATAMAX"]

                    # print("DATAMIN", self.vol_min)
                    # print("DATAMAX", self.vol_max)
                except:
                    # print("Warning: DATAMIN and DATAMAX not present in header; evaluating min and max")
                    if self.loaded_cube[0].header["NAXIS"] == 3:
                        self.vol_min = np.nanmin(self.loaded_cube[0].data)
                        self.vol_max = np.nanmax(self.loaded_cube[0].data)
                    else:
                        self.vol_min = np.nanmin(self.loaded_cube[0].data[0])
                        self.vol_max = np.nanmax(self.loaded_cube[0].data[0])

                # # Will trigger update clim
                # self.l_clim_min.setText(str(min))
                # self.l_clim_max.setText(str(max))

                # for widgets in self.widgets_array:
                #     for widget in widgets:
                #         widget.setEnabled(True)
            if filename[0].split('.')[-1] in ['fil']:
                # Load file
                self.loaded_cube = Waterfall(filename[0], max_load=5.5, load_data=False)
                self.loaded_cube.read_data(f_start=None, f_stop=None, t_start=0, t_stop=10 * 12500 + 1024)
                print (self.loaded_cube.data.shape)
                self.loaded_cube.data = self.clean_data(np.swapaxes(np.swapaxes(self.loaded_cube.data, 0, 2), 1, 2)[:,:,0])
                self.loaded_cube.data = np.expand_dims(np.fliplr(np.swapaxes(self.loaded_cube.data, 0, 1)), axis=2)
                # median = np.median(self.loaded_cube.data)
                # std = np.std(self.loaded_cube.data)
                # mask = np.abs(self.loaded_cube.data - median) > (2.698*std)
                #
                # print ("mask", mask)

                # from astropy import visualization
                # stretch = visualization.AsinhStretch(0.01) + visualization.MinMaxInterval()
                # self.loaded_cube.data = stretch(self.loaded_cube.data)

                try:
                    self.vol_min = self.loaded_cube.header["DATAMIN"]
                    self.vol_max = self.loaded_cube.header["DATAMAX"]
                except:
                    self.vol_min = np.nanmin(self.loaded_cube.data)
                    self.vol_max = np.nanmax(self.loaded_cube.data)

            self.signal_file_loaded.emit()

    def update_discard_filter_text(self, min, max):
        """Update the discard filter text field.

        Parameters
        ----------
        min : int, float
            Minimum value to be used by the filter
        max : int, float
            Maximum value to be used by the filter
        """
        self.vol_min = min
        self.vol_max = max
        try:
            self.l_high_discard_filter_value.setText(self.format_digits(self.vol_max))
            self.l_low_discard_filter_value.setText(self.format_digits(self.vol_min))
        except:
            pass

    def enable_widgets(self):
        """Enable widgets.

        At launch, all widgets except the `load fits` button are disabled. This function enables all widgets.
        """
        for widgets in self.widgets_array:
            for widget in widgets:
                widget.setEnabled(True)

    def format_digits(self, value):
        """Format digits to be printed.

        This function converts a numerical value to string
        """
        if isinstance(value, int):
            return str(value)
        else:
            return "{:.4f}".format(value)

    def update_view(self):
        """Update view.

        Emits the Qt signal informing that the camera has changed.
        """
        self.signal_camera_changed.emit()

    def update_fov(self):
        """Update view.

        Updates the field of view value text string.
        Emits the Qt signal informing that the field of view has changed.
        """
        self.l_fov_value.setText(str(self.slider_fov.value()))
        self.signal_fov_changed.emit()

    def update_autorotate(self):
        """Update autorotate.

        Emits the Qt signal informing that autorotate has changed.
        """
        self.signal_autorotate_changed.emit()

    def update_scaling(self):
        """Update scaling.

        Updates the scale (x,y,z) value text strings.
        Emits the Qt signal informing that scaling has changed.
        """
        self.l_scalex_value.setText(str(self.slider_scalex.value()))
        self.l_scaley_value.setText(str(self.slider_scaley.value()))
        self.l_scalez_value.setText(str(self.slider_scalez.value()))
        self.signal_scaling_changed.emit()

    def update_threshold(self):
        """Update threshold.

        Computes the scaled value relative to the global min max of the data.
        Updates the threshold text field with the new scaled_value.
        Emits the Qt signal informing that threshold has changed.
        """
        scaled_value = self.scale_value(self.slider_threshold.value(),
                                        self.slider_threshold.minimum(),
                                        self.slider_threshold.maximum(),
                                        self.vol_min,
                                        self.vol_max)

        self.l_threshold_value.setText(str(scaled_value))
        self.signal_threshold_changed.emit()

    def update_color_scale(self):
        """Update color scale.

        Emits the Qt signal informing that color scale has changed.
        """
        self.signal_color_scale_changed.emit()

    def update_filter_size(self):
        """Update filter size.

        Updates the filter size text field.
        Emits the Qt signal informing that filter size has changed.
        """
        self.l_filter_size_value.setText(str(self.slider_filter_size.value() + self.slider_filter_size.value() + 1))
        self.signal_filter_size_changed.emit()

    def update_filter_type(self):
        """Update filter type.

        Emits the Qt signal informing that filter type has changed.
        """
        self.signal_filter_type_changed.emit()

    def update_gaussian_filter_size(self):
        """Update gaussian filter kernel size

        Emits the Qt signal informing that gaussian filter kernel size has changed.
        """
        self.signal_filter_size_changed.emit()

    def update_high_discard_filter(self):
        """Update the high discard filter value.

        Computes the scaled value relative to the global min max of the data.
        Updates the high discard filter text field with the new scaled value.
        Emits the Qt signal informing that high discard filter has changed.
        """
        # (log_x - np.min(log_x)) * (nbins / (np.max(log_x) - np.min(log_x)))
        self.high_scaled_value = self.scale_value(self.slider_high_discard_filter.value(),
                                                  self.slider_high_discard_filter.minimum(),
                                                  self.slider_high_discard_filter.maximum(),
                                                  self.vol_min,
                                                  self.vol_max)

        if isinstance(self.high_scaled_value, int):
            self.l_high_discard_filter_value.setText(str(self.high_scaled_value))
        else:
            self.l_high_discard_filter_value.setText("{:.4f}".format(self.high_scaled_value))

        self.signal_high_discard_filter_changed.emit()

    def update_low_discard_filter(self):
        """Update the low discard filter value.

        Computes the scaled value relative to the global min max of the data.
        Updates the low discard filter text field with the new scaled value.
        Emits the Qt signal informing that low discard filter has changed.
        """
        # (log_x - np.min(log_x)) * (nbins / (np.max(log_x) - np.min(log_x)))
        self.low_scaled_value = self.scale_value(self.slider_low_discard_filter.value(),
                                                 self.slider_low_discard_filter.minimum(),
                                                 self.slider_low_discard_filter.maximum(),
                                                 self.vol_min,
                                                 self.vol_max)

        if isinstance(self.l_low_discard_filter_value, int):
            self.l_low_discard_filter_value.setText(str(self.low_scaled_value))
        else:
            self.l_low_discard_filter_value.setText("{:.4f}".format(self.low_scaled_value))

        self.signal_low_discard_filter_changed.emit()

    def update_density_factor(self):
        """Update the density factor.

        Computes the scaled value relative to the global min max of the data.
        Updates the density factor text field with the new scaled value.
        Emits the Qt signal informing that high discard filter has changed.
        """
        scaled_value = self.format_digits(self.scale_value(self.slider_density_factor.value(),
                                                           self.slider_density_factor.minimum(),
                                                           self.slider_density_factor.maximum(),
                                                           0.001,
                                                           2))

        self.l_density_factor_value.setText(str(scaled_value))
        self.signal_density_factor_changed.emit()

    def scale_value(self, old_value, old_min, old_max, new_min, new_max):
        """Scale a value from it's original range to another, arbitrary, range.

        Parameters
        ----------
        old_value : int, float
            Value to be scaled
        old_min : int, float
            Minimum of the original range
        old_max : int, float
            Maximum of the original range
        new_min : int, float
            Minimum of the new range
        new_max : int, float
            Maximum of the new range

        Return
        ------
            new_value : float
                Scaled value
        """
        old_range = old_max - old_min
        if old_range == 0:
            new_range = new_min
        else:
            new_range = (new_max - new_min)
            new_value = (((old_value - old_min) * new_range) / old_range) + new_min

        return new_value

    def export_image(self):
        """Export image.

        Emits the Qt signal informing that export image has been triggered.
        """
        self.signal_export_image.emit()


class Canvas3D(scene.SceneCanvas):
    """Class describing the 3D canvas where the visualisation is plotted"""
    def __init__(self, resolution):
        """Initialise the vispy canvas3D

        Parameters
        ----------
        resolution : appQt.desktop().screenGeometry()
            Width and height of the canvas.
        """
        self._configured = False
        self._fg = (0.5, 0.5, 0.5, 1)

        scene.SceneCanvas.__init__(self,
                                   keys='interactive',
                                   size=(resolution.width(), resolution.height()),
                                   show=True)
        self.unfreeze()
        self.window_resolution = resolution
        self.freeze()

        # self.measure_fps()

        self._configure_canvas()

        # Add a 3D axis to keep us oriented
        # scene.visuals.XYZAxis(parent=self.view.scene)

    def _configure_canvas(self):
        """Configure the vispy canvas

        Sets the background color, add and configure the grid to define where the colorbar and
        the main visualisation will be.
        """
        self.unfreeze()

        # Set up a viewbox to display the image with interactive pan/zoom
        # and colorbar

        self.central_widget.bgcolor = "#404040"
        self.grid = self.central_widget.add_grid(spacing=0, margin=0)
        self._configure_3d()

        self.freeze()

    def _configure_3d(self):
        """Configure the vispy canvas grid.
        """
        if self._configured:
            return

        # c0      c1      c2
        #  r0 +---------------|
        #     | cbar  |  view |
        #  r1 +---------------|


        #     c0      c1      c2
        #  r0 +---------------|
        #     | cbar  |       |
        #  r1 +-------- view  |
        #     | hist  |       |
        #  r2 +---------------|

        #     c0      c1      c2
        #  r0 +---------------|
        #     | cbar  |       |
        #  r1 +--------  3D   |
        #     | 2D    |       |
        #  r2 +---------------|

        # colorbar
        # row 0, column 0
        self.cbar_left = self.grid.add_widget(None, row=0, col=0, border_color='#404040', bgcolor="#404040")
        self.cbar_left.width_max = 0

        # 2D histogram
        # row 1, column 0
        # self.view_histogram = self.grid.add_view(row=1, col=0, border_color='#404040', bgcolor="#404040")
        # self.view_histogram.camera = 'panzoom'
        # self.camera_histogram = self.view_histogram.camera

        # self.view_2D = self.grid.add_view(row=1, col=0, border_color='#404040', bgcolor="#404040")
        # self.view_histogram.camera = 'panzoom'


        # 3D visualisation
        # row 0-1, column 1
        self.view = self.grid.add_view(row=0, col=1, #row_span=2,
                                       border_color='#404040', bgcolor="#404040")
        self.view.camera = 'turntable'
        self.camera = self.view.camera

        self._configured = True

    def colorbar(self, cmap, position="left",
                 label="", clim=("", ""),
                 border_width=0.0, border_color="#404040",
                 **kwargs):
        """Show a ColorBar

        Parameters
        ----------
        cmap : str | vispy.color.ColorMap
            Either the name of the ColorMap to be used from the standard
            set of names (refer to `vispy.color.get_colormap`),
            or a custom ColorMap object.
            The ColorMap is used to apply a gradient on the colorbar.
        position : {'left', 'right', 'top', 'bottom'}
            The position of the colorbar with respect to the plot.
            'top' and 'bottom' are placed horizontally, while
            'left' and 'right' are placed vertically
        label : str
            The label that is to be drawn with the colorbar
            that provides information about the colorbar.
        clim : tuple (min, max)
            the minimum and maximum values of the data that
            is given to the colorbar. This is used to draw the scale
            on the side of the colorbar.
        border_width : float (in px)
            The width of the border the colormap should have. This measurement
            is given in pixels
        border_color : str | vispy.color.Color
            The color of the border of the colormap. This can either be a
            str as the color's name or an actual instace of a vipy.color.Color

        Returns
        -------
        colorbar : instance of ColorBarWidget

        See also
        --------
        ColorBarWidget
        """
        self.cbar = scene.ColorBarWidget(orientation=position,
                                         label=label,
                                         cmap=cmap,
                                         clim=clim,
                                         border_width=border_width,
                                         border_color=border_color,
                                         **kwargs)

        if self.window_resolution.width() <= 3000:
            self.CBAR_LONG_DIM = 150
            self.cbar.label.font_size = 15
            self.cbar.label.color = "white"
            self.cbar.ticks[0].font_size = 12
            self.cbar.ticks[1].font_size = 12
            self.cbar.ticks[0].color = "white"
            self.cbar.ticks[1].color = "white"
        else:
            self.CBAR_LONG_DIM = 300
            self.cbar.label.font_size = 60
            self.cbar.label.color = "white"
            self.cbar.ticks[0].font_size = 45
            self.cbar.ticks[1].font_size = 45
            self.cbar.ticks[0].color = "white"
            self.cbar.ticks[1].color = "white"

        # colorbar - column 1
        # view - column 2

        if self.cbar.orientation == "bottom":
            self.grid.remove_widget(self.cbar)
            self.cbar_bottom = self.grid.add_widget(self.cbar, row=2, col=1)
            self.cbar_bottom.height_max = \
                self.cbar_bottom.height_max = self.CBAR_LONG_DIM

        elif self.cbar.orientation == "top":
            self.grid.remove_widget(self.cbar)
            self.cbar_top = self.grid.add_widget(self.cbar, row=0, col=1)
            self.cbar_top.height_max = self.cbar_top.height_max = self.CBAR_LONG_DIM

        elif self.cbar.orientation == "left":
            self.grid.remove_widget(self.cbar)
            self.cbar_left = self.grid.add_widget(self.cbar, row=0, col=0)
            self.cbar_left.width_max = self.cbar_left.width_min = self.CBAR_LONG_DIM

        else:
            self.grid.remove_widget(self.cbar)
            self.cbar_right = self.grid.add_widget(self.cbar, row=2, col=2)
            self.cbar_right.width_max = \
                self.cbar_right.width_min = self.CBAR_LONG_DIM

    def histogram(self, data, bins=100, color='w', orientation='h'):
        """Calculate and show a histogram of data

        Parameters
        ----------
        data : array-like
            Data to histogram. Currently only 1D data is supported.
        bins : int | array-like
            Number of bins, or bin edges.
        color : instance of Color
            Color of the histogram.
        orientation : {'h', 'v'}
            Orientation of the histogram.
        """
        self.view_histogram = self.grid.add_view(row=1, col=0, border_color='#404040', bgcolor="#404040")
        self.view_histogram.camera = 'panzoom'
        self.hist = scene.Histogram(data, bins, color, orientation)
        self.view_histogram.add(self.hist)
        self.view_histogram.camera.set_range()

    def set_volume_scene(self, cube):
        """Set volume scene

        Configures the vispy canvas to display the 3D visualisation.

        Parameters
        ----------
        cube : astropy.io.fits
            FITS file opened with astropy.io.fits containing the volumetric data (e.g. spectral cube).

        TO DO
        -----
        Move some of the code from this function to atomic functions (e.g. header information for cmap).

        """
        # Set up a viewbox to display the image with interactive pan/zoom
        if self.view:
            canvas = self.central_widget.remove_widget(self.grid)
            self._configure_canvas()

        self.unfreeze()
        self.view = self.grid.add_view(row=0, col=1, border_color='#404040', bgcolor="#404040")

        try:
            cube = cube[0]
        except:
            pass

        try:
            # Quick fix -- will need to be a bit more clever.
            self.parse_header_info_for_axes_labels(cube)

            if len(cube.data.shape) == 4:
                # Currently forces a hard 2048 limit to avoid overflowing the gpu texture memory...
                data = cube.data[0][:2048, :2048, :2048]

                self.vel_axis = cube.data[0].shape[0]
            else:
                # Currently forces a hard 2048 limit to avoid overflowing the gpu texture memory...
                print (cube.shape)
                data = cube.data[:2048, :2048, :2048]
                # data = cube.data[:,60:-60,:]
                # data = cube.data[:, :, :]
                self.vel_axis = cube.data.shape[0]

            try:
                self.bunit = cube.header['BUNIT']
            except:
                self.bunit = "unknown"

            try:
                self.vel_type = cube.header['CTYPE3']
            except:
                self.vel_type = "Epoch"

            try:
                # TODO: Possibly use astropy's wcs module for all of this.
                self.vel_val = cube.header['CRVAL3']
                lim_is_set = False
                try:
                    self.vel_delt = cube.header['CDELT3']
                    set_lim = True
                except:
                    # print("No CDELT3 card in header.")
                    set_lim = False

                if self.vel_type == 'VELO-HEL' or self.vel_type == 'FELO-HEL':
                    self.vel_type += ' (km/s)'
                    if set_lim:
                        self.clim_vel = np.int(np.round(float(self.vel_val) / 1000)), np.int(
                            np.round((float(self.vel_val) +
                                      float(self.vel_delt) *
                                      self.vel_axis) / 1000))
                        lim_is_set = True

                elif self.vel_type == 'FREQ':
                    if cube.header['CUNIT3'] == 'Hz':
                        self.vel_type += ' (T' + cube.header['CUNIT3'] + ')'  # Hz to THz
                        self.clim_vel = float(self.vel_val) / (1000 * 1000 * 1000), \
                                        (float(self.vel_val) + float(self.vel_delt) * self.vel_axis) / (
                                        1000 * 1000 * 1000)
                        lim_is_set = True
                    else:
                        self.vel_type += ' (' + cube.header['CUNIT3'] + ')'
                        self.clim_vel = np.int(np.round(float(self.vel_val))), \
                                        np.int(np.round((float(self.vel_val) +
                                                         float(self.vel_delt) *
                                                         self.vel_axis)))
                        lim_is_set = True
                elif self.vel_type == 'WAVE':
                    self.vel_type += ' (' + cube.header['CUNIT3'] + ')'

                if set_lim == True and lim_is_set == False:
                    self.clim_vel = np.int(np.round(float(self.vel_val))), np.int(np.round((float(self.vel_val) +
                                                                                            float(self.vel_delt) *
                                                                                            self.vel_axis)))
                    lim_is_set = True

                if set_lim == False:
                    try:
                        self.vel_delt = cube.header['STEP']
                        self.clim_vel = np.int(np.round(float(self.vel_val))), np.int(np.round((float(self.vel_val) +
                                                                                                float(self.vel_delt) *
                                                                                                self.vel_axis)))
                    except:
                        self.clim_vel = 0, self.vel_axis

            except:
                self.vel_val = "Undefined"

            data = np.flipud(np.rollaxis(data, 1))

            self.volume = RenderVolume(data,
                                       parent=self.view.scene,
                                       threshold=0.225,
                                       emulate_texture=False)

            # %%%%%%%%%%%%%%%%%%%%%%%%%%
            # Axes labels
            # %%%%%%%%%%%%%%%%%%%%%%%%%%
            self.data_shape = data.shape
            self.axis = AxesVisual3D(
                parent=self.view.scene,
                data_shape=self.data_shape,
                axis_color="white",
                tick_color="white",
                text_color="white",
                tick_width=1.5,
                minor_tick_length=0,
                major_tick_length=50,
                axis_width=1.5,
                tick_label_margin=5,
                axis_label_margin=10,
                tick_font_size=10,
                axis_font_size=15,
                view=self.view,
                transform=scene.STTransform(
                    scale=(1, 1, 1),
                    translate=(0, 0, 0),
                )
            )

            self.axis.xlabel = self.axes_info[0]['label']
            self.axis.ylabel = self.axes_info[1]['label']
            self.axis.zlabel = self.axes_info[2]['label']

            self.axis.xlim = self.axes_info[0]['minval'], self.axes_info[0]['maxval']
            self.axis.ylim = self.axes_info[1]['minval'], self.axes_info[1]['maxval']
            self.axis.zlim = self.axes_info[2]['minval'], self.axes_info[2]['maxval']

            # Increase line width for more visibility
            gl.glLineWidth(1.5)
            # %%%%%%%%%%%%%%%%%%%%%%%%%%

            # Cheat to make the box width bigger.
            #
            pos = np.array([[0, 0, 0], [1, 1, 1]])
            self.line = scene.Line(pos=pos,
                              color='green',
                              method='gl',
                              width=2,
                              connect='strip',
                              parent=self.view.scene)
            self.line.antialias = 1

            # Add colorbar
            self.colorbar(label=str(self.vel_type),
                          clim=self.volume.clim,
                          # label=str(self.bunit),
                          # clim=self.volume.clim,
                          cmap="hsl",
                          border_width=0,
                          border_color="#404040")
            self.show_colorbar = True

            # self.histogram(data.ravel())

            # self.rotation and self.timer used for autorotate.
            self.rotation = scene.MatrixTransform()
            self.timer = app.Timer(connect=self.rotate)
            self.angle = 0.

            self.freeze()

        except ValueError as e:
            t = e
            print(t)

    def set_rendering_params(self, tf_method, cmap, combo_color_method, interpolation_method):
        """Set rendering parameters for the visualised volume.

        Parameters
        ----------
        tf_method : str
            Transfer function method
        cmap : str
            Color map (e.g. hot, RbBl...)
        combo_color_method : str
            Color method (e.g. mom0, mom1, rgb)
        interpolation_method : str
            Interpolation method
        """
        self.volume.method = tf_method
        self.volume.cmap = cmap
        self.volume.color_method = combo_color_method
        self.volume.interpolation = interpolation_method

        if (self.volume.color_method == 0):
            label = str(self.bunit)
            clim = self.volume.clim
            self.cbar_left.visible = True
            self.show_colorbar = True

        elif (self.volume.color_method == 2):
            self.cbar_left.visible = False
            self.show_colorbar = False
        elif (self.volume.color_method == 3):
            self.cbar_left.visible = False
            self.show_colorbar = False
        else:
            label = str(self.vel_type)
            clim = self.clim_vel
            self.cbar_left.visible = True
            self.show_colorbar = True

        if self.show_colorbar:
            self.cbar.clim = clim
            self.cbar.label_str = label
            self.cbar.cmap = cmap

    def set_threshold(self, threshold):
        """Set threshold value for the visualised volume.

        Parameters
        ----------
        threshold : int, float
        """
        try:
            threshold = float(threshold)
        except:
            print("Threshold: needs to be a float")
            pass

        try:
            threshold -= self.volume.clim[0]
            threshold /= self.volume.clim[1] - self.volume.clim[0]
            self.volume.threshold = threshold
            # print (self.volume.threshold)
        except:
            print("Invalid threshold")
            pass

    def set_color_scale(self, color_scale):
        """Set color scale value for the visualised volume.

        Parameters
        ----------
        color_scale: str
            Scaling function (e.g. linear, log, exp)
        """
        self.volume.color_scale = color_scale

    def set_box_filter_size(self, filter_size):
        """Set box filter kernel size value for the visualised volume.

        Parameters
        ----------
        filter_size: int
            Filter kernel size. Number of neighbours considered during the convolution.
        """
        self.volume.filter_size = filter_size

    def set_filter_type(self, filter_type):
        """Set box filter type for the visualised volume.

        The two filter methods currently available are `filter out`, or `rescale`.

        Parameters
        ----------
        filter_type : int
            Type of filter
        """
        self.volume.filter_type = filter_type

    def set_gaussian_filter(self, use_gaussian_filter, gaussian_filter_size):
        """Set gaussian filter parameters.

        Parameters
        ----------
        use_gaussian_filter : int
            0 or 1, compute the gaussian filter (1) or not (0).
        gaussian_filter_size : int
            Size of the kernel. Number of neighbours considered during the convolution.
        """
        self.volume.use_gaussian_filter = use_gaussian_filter
        self.volume.gaussian_filter_size = gaussian_filter_size

    def set_high_discard_filter(self, high_discard_filter_value, scaled_value, filter_type):
        """Set high discard filter value (values higher than this will be discarded).

        Parameters
        ----------
        high_discard_filter_value : int, float
            Upper limit.
        scaled_value : int, float
            High discard value scaled to data range
        filter_type : str
            Filter type
        """
        self.volume.high_discard_filter_value = high_discard_filter_value
        self.update_clim("high", scaled_value, filter_type)

    def set_low_discard_filter(self, low_discard_filter_value, scaled_value, filter_type):
        """Set low discard value (values lower than this will be discarded).

        Parameters
        ----------
        low_discard_filter_value : int, float
            Lower limit
        scaled_value : int, float
            Scaled value
        filter_type : str
            Filter type
        """
        self.volume.low_discard_filter_value = low_discard_filter_value
        self.update_clim("low", scaled_value, filter_type)

    def update_clim(self, type, value, filter_type):
        """Update color limit (clim)

        Parameters
        ----------
        type : str
            bound type (low or high)
        value : int, float
            New value to be set
        filter_type : str
            Filter type
        """
        # print("self.volume.color_method", self.volume.color_method)
        if self.volume.color_method == 0:
            if filter_type == 'Rescale':
                if type == "low":
                    self.cbar.clim = [value, self.cbar.clim[1]]
                if type == "high":
                    self.cbar.clim = [self.cbar.clim[0], value]

    def set_density_factor(self, density_factor):
        """Set density factor

        Parameters
        ----------
        density_factor : int, float
            Factor used with AVIP to set the transparency level
        """
        # print (density_factor)
        self.volume.density_factor = density_factor

    def set_fov(self, fov):
        """Set the field of view of the camera.

        Parameters
        ----------
        fov : int, float
            Field of view
        """
        self.view.camera.fov = fov

    def set_camera(self, cam, fov):
        """Set camera type.

        Parameters
        ----------
        cam : str
            Camera type (based on vispy's cameras)
        fov : int, float
            Camera's field of view
        """
        if cam == 'Perspectivecamera':
            self.view.camera = scene.cameras.PerspectiveCamera(parent=self.view.scene,
                                                               fov=float(fov),
                                                               name='Perspectivecamera',
                                                               center=(0.5, 0.5, 0.5))
        if cam == 'Turntable':
            self.view.camera = scene.cameras.TurntableCamera(parent=self.view.scene,
                                                             elevation=0.,
                                                             azimuth=0.,
                                                             fov=float(fov),
                                                             name='Turntable')
        if cam == 'Fly':
            self.view.camera = scene.cameras.FlyCamera(parent=self.view.scene,
                                                       fov=float(fov),
                                                       name='Fly')
        if cam == 'Arcball':
            self.view.camera = scene.cameras.ArcballCamera(parent=self.view.scene,
                                                           fov=float(fov),
                                                           name='Arcball')

    def set_autorotate(self, flag):
        """Set autorotate value.

        Parameters
        ----------
        flag : bool
            Should it autorotate or not. True: autorotate. False: will not autorotate
        """
        if flag == True:
            # self.set_camera("Perspectivecamera", 60)
            # self.timer.start(0.01, 100)
            self.timer.start(0.01)
        else:
            self.timer.stop()

    def rotate(self, event):
        """Perform a rotation of the visualisation.

        Function to which a timer connects to.
        """
        # self.angle += .005
        self.angle = 3.6
        # self.rotation.rotate(self.angle, (0, 0, 1))
        # self.axis.transform = self.volume.transform = self.rotation
        self.view.camera.orbit(self.angle, 0)

    def set_log_scale(self, flag):
        """Set the log scaling.

        Parameters
        ----------
        flag : bool
            Log scale or not.

        Note
        ----
        Not currently being used.
        """
        self.volume.log_scale = flag

    def set_scaling(self, scalex, scaley, scalez):
        """Set x, y, or z scaling (transform).

        Parameters
        ----------
        scalex : int, float
            scaling factor for the x axis
        scaley: int, float
            scaling factor for the y axis
        scalez: int, float
            scaling factor for the z axis
        """
        self.axis.transform = self.volume.transform = scene.STTransform(
            scale=(scalex, scalez, scaley),
            translate=(-scalex ** 2, -scalez ** 2, -scaley ** 2)
        )

    def parse_header_info_for_axes_labels(self, cube):
        """Collect information from cube's header

        :param cube: astropy.fits
        """
        self.axes_info = [{}, {}, {}]
        if len(cube.data.shape) == 4:
            index = [1, 3, 2]
            for i in range(3):
                self.axes_info[i]['label'] = cube.header['CTYPE' + str(index[i])]
                self.axes_info[i]['minval'] = cube.header['CRVAL' + str(index[i])]
                self.axes_info[i]['maxval'] = (cube.data[0].shape[2 - i] *
                                               cube.header['CDELT' + str(index[i])]) - self.axes_info[i]['minval']
        else:
            index = [1, 3, 2]
            for i in range(3):
                self.axes_info[i]['label'] = cube.header['CTYPE' + str(index[i])]
                self.axes_info[i]['minval'] = cube.header['CRVAL' + str(index[i])]
                self.axes_info[i]['maxval'] = (cube.data.shape[2 - i] *
                                               cube.header['CDELT' + str(index[i])]) - cube.header['CRVAL' + str(index[i])]


# -----------------------------------------------------------------------------
def main():
    appQt = QApplication(sys.argv)
    resolution = appQt.desktop().screenGeometry()

    # Create and display the splash screen
    splash_pix = QPixmap('shwirl/images/splash_screen.png')
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    splash.show()
    appQt.processEvents()

    win = MainWindow(resolution)
    win.show()
    appQt.exec_()

if __name__ == '__main__':
    appQt = QApplication(sys.argv)
    resolution = appQt.desktop().screenGeometry()
    appQt.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    appQt.setAttribute(QtCore.Qt.QT_AUTO_SCREEN_SCALE_FACTOR)

    # Create and display the splash screen
    splash_pix = QPixmap('shwirl/images/splash_screen.png')
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    splash.show()
    appQt.processEvents()

    win = MainWindow(resolution)
    win.show()
    appQt.exec_()
