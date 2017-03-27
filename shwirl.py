# -*- coding: utf-8 -*-
from __future__ import division

# Basic imports
import sys
import numpy as np

# Vispy imports
from vispy import app, scene, plot, io
from vispy.util.transforms import perspective, translate, rotate
from vispy.color import get_colormaps, BaseColormap
#from vispy.geometry import create_cube
from shades import RenderVolume
from shades.axes import AxesVisual3D

from vispy import gloo

# Astropy imports
from astropy import wcs
from astropy.io import fits
import os

# Window related
# try:
#     from sip import setapi
#     setapi("QVariant", 2)
#     setapi("QString", 2)
# except ImportError:
#     pass

#TODO: Change '/Users/danyvohl/code/data' to something like os.getenv('HOME')


from PyQt5 import QtGui, QtCore, QtWidgets

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

        #self.resize(1800, 1000)
        self.resize(800, 600)
        self.setWindowTitle('ONECUBE')

        splitter_h = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter_v = QtWidgets.QSplitter(QtCore.Qt.Vertical)

        self.Canvas3D = Canvas3D()
        self.Canvas3D.create_native()
        self.Canvas3D.native.setParent(self)

        # Histogram
        # self.Canvas2D = Canvas2D()
        # #self.Canvas2D.create_native()
        # self.Canvas2D.native.setParent(self)
        # splitter_v.addWidget(self.Canvas2D.native)

        # Main Canvas3D for 3D rendering
        splitter_h.addWidget(self.Canvas3D.native)
        #splitter_h.addWidget(splitter_v)

        # Menus / viz options
        self.props = ObjectWidget()
        splitter_v.addWidget(self.props)

        # FITS metadata
        self.fits_infos = FitsMetaWidget()
        splitter_v.addWidget(self.fits_infos)
        splitter_h.addWidget(splitter_v)

        self.setCentralWidget(splitter_h)

        # Connect signals (events handling)
        self.props.signal_file_loaded.connect(self.load_volume)
        self.props.signal_objet_changed.connect(self.update_view)
        self.props.signal_camera_changed.connect(self.update_camera)
        self.props.signal_autorotate_changed.connect(self.update_autorotate)
        self.props.signal_log_scale_changed.connect(self.update_log_scale)
        self.props.signal_scaling_changed.connect(self.update_scaling)
        self.props.signal_threshold_changed.connect(self.update_threshold)
        # self.props.signal_color_scale_changed.connect(self.update_color_scale)
        self.props.signal_filter_size_changed.connect(self.update_filter_size)
        self.props.signal_filter_type_changed.connect(self.signal_filter_type)
        self.props.signal_high_discard_filter_changed.connect(self.update_high_discard_filter)
        self.props.signal_low_discard_filter_changed.connect(self.update_low_discard_filter)
        self.props.signal_density_factor_changed.connect(self.update_density_factor)
        self.props.signal_export_image.connect(self.export_image)

        QtWidgets.QApplication.setStyle(QtWidgets.QStyleFactory.create('Cleanlooks'))

    def load_volume(self):
        self.Canvas3D.set_volume_scene(self.props.loaded_cube)
        self.fits_infos.print_header(self.props.loaded_cube[0].header)
        #self.Canvas2D.set_histogram(self.props.loaded_cube)

    def update_view(self):
        # vr_method, cmap
        self.Canvas3D.set_data(self.props.combo_vr_method.currentText(),
                               self.props.combo_cmap.currentText(),
                               self.props.combo_color_method.currentText(),
                               self.props.combo_interpolation_method.currentText())

        if self.props.combo_vr_method.currentText() == 'lmip' :
            print("thres", self.props.l_threshold_value.text())
            #self.update_threshold(self.props.l_threshold_value.text())
            self.update_threshold()

    def update_camera(self):
        self.Canvas3D.set_camera(self.props.combo_camera.currentText(),
                                 self.props.slider_fov.value())

    def update_autorotate(self):
        self.Canvas3D.set_autorotate(self.props.chk_autorotate.isChecked())
        
    def update_log_scale(self):
        self.Canvas3D.set_log_scale(self.props.chk_log_scale.isChecked())

    def update_scaling(self):
        self.Canvas3D.set_scaling(self.props.slider_scalex.value(),
                                 self.props.slider_scaley.value(),
                                 self.props.slider_scalez.value())

    def update_threshold(self):
        self.Canvas3D.set_threshold(self.props.l_threshold_value.text())

    def update_color_scale(self):
        self.Canvas3D.set_color_scale(self.props.combo_color_scale.currentText())

    def update_filter_size(self):
        self.Canvas3D.set_filter_size(self.props.l_filter_size_value.text())
        self.Canvas3D.set_gaussian_filter(self.props.combo_use_gaussian_filter.currentText(),
                                          self.props.combo_gaussian_filter_size.currentText())

    def signal_filter_type(self):
        self.Canvas3D.set_filter_type(self.props.combo_filter_type.currentText())

    def update_high_discard_filter(self):
        self.Canvas3D.set_high_discard_filter(self.props.l_high_discard_filter_value.text(), self.props.high_scaled_value)
        
    def update_low_discard_filter(self):
        self.Canvas3D.set_low_discard_filter(self.props.l_low_discard_filter_value.text(), self.props.low_scaled_value)

    def update_density_factor(self):
        self.Canvas3D.set_density_factor(self.props.l_density_factor_value.text())

    def export_image(self):
        fileName = QtWidgets.QFileDialog.getSaveFileName(self,
                                                         'Save still image',
                                                         os.getenv('HOME'),
                                                         # '/Users/danyvohl/code/data',
                                                         initialFilter='Images (*.png)')
        if fileName:
            #print ("save image as", fileName)
            img = self.Canvas3D.render()
            io.write_png(fileName[0] + '.png', img)

class FitsMetaWidget(QtWidgets.QWidget):
    """
    Widget for editing Volume parameters
    """
    #signal_objet_changed = QtCore.pyqtSignal(name='objectChanged')

    def __init__(self, parent=None):
        super(FitsMetaWidget, self).__init__(parent)

        l_title = QtWidgets.QLabel("Fits Primary Header")

        self.l_header = QtWidgets.QTextEdit("No fits loaded ")
        self.l_header.setReadOnly(True)

        font = self.l_header.font()
        font.setFamily("Avenir")
        font.setPointSize(12)

        gbox = QtWidgets.QGridLayout()
        # ------ Adding Widgets
        gbox.addWidget(l_title, 0, 1)
        gbox.addWidget(self.l_header, 1, 1)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(gbox)
        vbox.addStretch(1.0)

        self.setLayout(vbox)

    def print_header(self, header):

        self.l_header.clear()
        self.l_header.insertPlainText('card\tvalue\tcomment\n')
        for card in header.cards:
            self.l_header.setTextColor(QtGui.QColor('blue'))
            self.l_header.insertPlainText(str(card[0]) + "\t")
            self.l_header.setTextColor(QtGui.QColor('black'))
            self.l_header.insertPlainText(str(card[1]) + "\t")
            self.l_header.setTextColor(QtGui.QColor('red'))
            self.l_header.insertPlainText(str(card[2]) + "\n")

        sb = self.l_header.verticalScrollBar()
        sb.setValue(sb.maximum())

class ObjectWidget(QtWidgets.QWidget):
    """
    Widget for editing Volume parameters
    """
    signal_objet_changed = QtCore.pyqtSignal(name='objectChanged')
    signal_file_loaded = QtCore.pyqtSignal(name='fileLoaded')
    signal_camera_changed = QtCore.pyqtSignal(name='cameraChanged')
    signal_autorotate_changed = QtCore.pyqtSignal(name='autorotateChanged')
    signal_log_scale_changed = QtCore.pyqtSignal(name='log_scaleChanged')
    signal_scaling_changed = QtCore.pyqtSignal(name='scalingChanged')
    signal_threshold_changed = QtCore.pyqtSignal(name='thresholdChanged')
    signal_color_scale_changed = QtCore.pyqtSignal(name='color_scaleChanged')
    signal_filter_size_changed = QtCore.pyqtSignal(name='filter_sizeChanged')
    signal_filter_type_changed = QtCore.pyqtSignal(name='filter_typeChanged')
    signal_high_discard_filter_changed = QtCore.pyqtSignal(name='high_discard_filterChanged')
    signal_low_discard_filter_changed = QtCore.pyqtSignal(name='low_discard_filterChanged')
    signal_density_factor_changed = QtCore.pyqtSignal(name='density_factorChanged')
    signal_export_image = QtCore.pyqtSignal(name='export_image')

    def __init__(self, parent=None):
        super(ObjectWidget, self).__init__(parent)

        self.loaded_cube = None

        self.widgets_array = []
        self.widgets_dict = {}
        def serialize_widgets(key, array):
            self.widgets_array.append(array)
            self.widgets_dict[key] = array

        self.load_button = QtWidgets.QPushButton("Load FITS", self)
        self.load_button.clicked.connect(self.showDialog)
        array = [self.load_button]
        serialize_widgets('fits_button', array)

        l_cam = QtWidgets.QLabel("Camera ")
        self.camera = ['Turntable', 'Fly', 'Arcball'] # 'PerspectiveCamera'
        self.combo_camera = QtWidgets.QComboBox(self)
        self.combo_camera.addItems(self.camera)
        self.combo_camera.currentIndexChanged.connect(self.update_camera)
        array = [l_cam, self.combo_camera]
        serialize_widgets('camera', array)

        self.chk_autorotate = QtWidgets.QCheckBox("Autorotate")
        self.chk_autorotate.setChecked(False)
        self.chk_autorotate.stateChanged.connect(self.update_autorotate)
        array = [self.chk_autorotate]
        serialize_widgets('autorotate', array)

        # self.chk_log_scale = QtWidgets.QCheckBox("Log scale")
        # self.chk_log_scale.setChecked(False)
        # self.chk_log_scale.stateChanged.connect(self.update_log_scale)
        # array = [self.chk_log_scale]
        # serialize_widgets('log_scale', array)

        l_fov = QtWidgets.QLabel("Field of View ")
        self.slider_fov = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_fov.setMinimum(0)
        self.slider_fov.setMaximum(160)
        self.slider_fov.setValue(60)
        self.slider_fov.setTickInterval(5)
        self.l_fov_value = QtWidgets.QLineEdit(str(self.slider_fov.value()))
        self.slider_fov.valueChanged.connect(self.update_camera)
        array = [l_fov, self.slider_fov, self.l_fov_value]
        serialize_widgets('field_of_view',array)

        l_vr_method = QtWidgets.QLabel("VR method ")
        #self.l_vr_method = ['mip', 'translucent', 'iso', 'additive']
        self.vr_method = ['mip', 'lmip', 'translucent', 'MeanIP', 'iso']
        self.combo_vr_method = QtWidgets.QComboBox(self)
        self.combo_vr_method.addItems(self.vr_method)
        self.combo_vr_method.currentIndexChanged.connect(self.update_param)
        array = [l_vr_method, self.combo_vr_method]
        serialize_widgets('vr_method', array)

        l_density_factor = QtWidgets.QLabel("Density regulator ")
        self.slider_density_factor = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_density_factor.setMinimum(0)
        self.slider_density_factor.setMaximum(10000)
        self.slider_density_factor.setValue(0)
        self.l_density_factor_value = QtWidgets.QLineEdit(str(1))
        self.slider_density_factor.valueChanged.connect(self.update_density_factor)
        array = [l_density_factor, self.slider_density_factor, self.l_density_factor_value]
        serialize_widgets('density_factor', array)
        for widget in self.widgets_dict['density_factor']:
            widget.hide()

        l_color_method = QtWidgets.QLabel("Color method ")
        self.color_method = ['voxel', 'velocity/redshift', 'rgb_cube']
        self.combo_color_method = QtWidgets.QComboBox(self)
        self.combo_color_method.addItems(self.color_method)
        self.combo_color_method.currentIndexChanged.connect(self.update_param)
        array = [l_color_method, self.combo_color_method]
        serialize_widgets('color_method', array)

        l_threshold = QtWidgets.QLabel("Threshold ")
        self.slider_threshold = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_threshold.setMinimum(0)
        self.slider_threshold.setMaximum(10000)
        self.slider_threshold.setValue(10000)
        self.l_threshold_value = QtWidgets.QLineEdit(str(self.slider_threshold.value()))
        self.slider_threshold.valueChanged.connect(self.update_threshold)
        array = [l_threshold, self.slider_threshold, self.l_threshold_value]
        serialize_widgets('threshold', array)

        l_interpolation_method = QtWidgets.QLabel("Interpolation method ")
        self.interpolation_method = ['linear', 'nearest']#,
                                     # 'bilinear', 'hanning', 'hamming', 'hermite',
                                     # 'kaiser', 'quadric', 'bicubic', 'catrom',
                                     # 'mitchell', 'spline16', 'spline36', 'gaussian',
                                     # 'bessel', 'sinc', 'lanczos', 'blackman']
        self.combo_interpolation_method = QtWidgets.QComboBox(self)
        self.combo_interpolation_method.addItems(self.interpolation_method)
        self.combo_interpolation_method.currentIndexChanged.connect(self.update_param)
        array = [l_interpolation_method, self.combo_interpolation_method]
        serialize_widgets('interpolation_method', array)

        l_cmap = QtWidgets.QLabel("Cmap ")
        self.cmap = sorted(list(get_colormaps().keys()), key=str.lower)
        self.combo_cmap = QtWidgets.QComboBox(self)
        self.combo_cmap.addItems(self.cmap)
        self.combo_cmap.currentIndexChanged.connect(self.update_param)
        array = [l_cmap, self.combo_cmap]
        serialize_widgets('cmap', array)

        # l_color_scale = QtWidgets.QLabel("Color scale ")
        # self.color_scale = ['linear', 'log', 'exp']
        # self.combo_color_scale = QtWidgets.QComboBox(self)
        # self.combo_color_scale.addItems(self.color_scale)
        # self.combo_color_scale.currentIndexChanged.connect(self.update_color_scale)
        # array = [l_color_scale, self.combo_color_scale]
        # serialize_widgets('color_scale', array)

        l_scalex = QtWidgets.QLabel("Scale X ")
        self.slider_scalex = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_scalex.setMinimum(1)
        self.slider_scalex.setMaximum(20)
        self.slider_scalex.setValue(1)
        self.slider_scalex.setTickInterval(1)
        self.l_scalex_value = QtWidgets.QLineEdit(str(self.slider_scalex.value()))
        self.slider_scalex.valueChanged.connect(self.update_scaling)
        array = [l_scalex, self.slider_scalex, self.l_scalex_value]
        serialize_widgets('scale_x', array)

        l_scaley = QtWidgets.QLabel("Scale Y ")
        self.slider_scaley = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_scaley.setMinimum(1)
        self.slider_scaley.setMaximum(20)
        self.slider_scaley.setValue(1)
        self.slider_scaley.setTickInterval(1)
        self.l_scaley_value = QtWidgets.QLineEdit(str(self.slider_scaley.value()))
        self.slider_scaley.valueChanged.connect(self.update_scaling)
        array = [l_scaley, self.slider_scaley, self.l_scaley_value]
        serialize_widgets('scale_y', array)

        l_scalez = QtWidgets.QLabel("Scale Z ")
        self.slider_scalez = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_scalez.setMinimum(1)
        self.slider_scalez.setMaximum(20)
        self.slider_scalez.setValue(1)
        self.slider_scalez.setTickInterval(1)
        self.l_scalez_value = QtWidgets.QLineEdit(str(self.slider_scalez.value()))
        self.slider_scalez.valueChanged.connect(self.update_scaling)
        array = [l_scalez, self.slider_scalez, self.l_scalez_value]
        serialize_widgets('scale_z', array)

        l_filter_size = QtWidgets.QLabel("Box filter size ")
        self.slider_filter_size = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_filter_size.setMinimum(0)
        self.slider_filter_size.setMaximum(10)
        self.slider_filter_size.setValue(0)
        self.l_filter_size_value = QtWidgets.QLineEdit(str(self.slider_filter_size.value() + 1))
        self.slider_filter_size.valueChanged.connect(self.update_filter_size)
        array = [l_filter_size, self.slider_filter_size, self.l_filter_size_value]
        serialize_widgets('filter_size', array)

        l_use_gaussian_filter = QtWidgets.QLabel("Activate Gaussian filter")
        self.use_gaussian_filter = ['0', '1']  # 'PerspectiveCamera',
        self.combo_use_gaussian_filter = QtWidgets.QComboBox(self)
        self.combo_use_gaussian_filter.addItems(self.use_gaussian_filter)
        self.combo_use_gaussian_filter.currentIndexChanged.connect(self.update_gaussian_filter_size)
        array = [l_use_gaussian_filter, self.combo_use_gaussian_filter]
        serialize_widgets('use_gaussian_filter', array)

        l_gaussian_filter_size = QtWidgets.QLabel("Gaussian filter size ")
        self.gaussian_filter_size = ['5', '9', '13']  # 'PerspectiveCamera',
        self.combo_gaussian_filter_size = QtWidgets.QComboBox(self)
        self.combo_gaussian_filter_size.addItems(self.gaussian_filter_size)
        self.combo_gaussian_filter_size.currentIndexChanged.connect(self.update_gaussian_filter_size)
        array = [l_gaussian_filter_size, self.combo_gaussian_filter_size]
        serialize_widgets('gaussian_filter_size', array)

        l_filter_type = QtWidgets.QLabel("Type of filter")
        self.filter_type = ['Filter out', 'Rescale']  # 'PerspectiveCamera',
        self.combo_filter_type = QtWidgets.QComboBox(self)
        self.combo_filter_type.addItems(self.filter_type)
        self.combo_filter_type.currentIndexChanged.connect(self.update_filter_type)
        array = [l_filter_type, self.combo_filter_type]
        serialize_widgets('filter_type', array)

        l_high_discard_filter = QtWidgets.QLabel("high discard filter ")
        self.slider_high_discard_filter = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_high_discard_filter.setMinimum(0)
        self.slider_high_discard_filter.setMaximum(10000)
        self.slider_high_discard_filter.setValue(10000)
        self.l_high_discard_filter_value = QtWidgets.QLineEdit(str(self.slider_high_discard_filter.value()))
        self.slider_high_discard_filter.valueChanged.connect(self.update_high_discard_filter)
        array = [l_high_discard_filter, self.slider_high_discard_filter, self.l_high_discard_filter_value]
        serialize_widgets('high_discard_filter', array)
        for widget in self.widgets_dict['high_discard_filter']:
            widget.hide()
        
        l_low_discard_filter = QtWidgets.QLabel("Low discard filter ")
        self.slider_low_discard_filter = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_low_discard_filter.setMinimum(0)
        self.slider_low_discard_filter.setMaximum(10000)
        self.slider_low_discard_filter.setValue(0)
        self.l_low_discard_filter_value = QtWidgets.QLineEdit(str(self.slider_low_discard_filter.value()))
        self.slider_low_discard_filter.valueChanged.connect(self.update_low_discard_filter)
        array = [l_low_discard_filter, self.slider_low_discard_filter, self.l_low_discard_filter_value]
        serialize_widgets('low_discard_filter', array)

        self.export_image_button = QtWidgets.QPushButton("export_image", self)
        self.export_image_button.clicked.connect(self.export_image)
        array = [self.export_image_button]
        serialize_widgets('export_image', array)

        gbox = QtWidgets.QGridLayout()

        # Add widgets to the grid layout
        widgets_i = 0
        for widgets in self.widgets_array:
            widget_i = 1
            for widget in widgets:
                gbox.addWidget(widget, widgets_i, widget_i)
                if widgets_i > 0:
                    widget.setEnabled(False)

                widget_i += 1
            widgets_i += 1

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(gbox)
        vbox.addStretch(1.0)

        self.setLayout(vbox)

    def update_param(self, option):
        if self.combo_vr_method.currentText() == 'translucent':
            for widget in self.widgets_dict['density_factor']:
                widget.show()
        else:
            for widget in self.widgets_dict['density_factor']:
                widget.hide()

        if self.combo_vr_method.currentText() == 'lmip' or self.combo_vr_method.currentText() == 'iso':
            for widget in self.widgets_dict['threshold']:
                widget.show()
        else:
            for widget in self.widgets_dict['threshold']:
                widget.hide()

        self.signal_objet_changed.emit()

    def showDialog(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self,
                                                  'Open file',
                                                  os.getenv('HOME'))
                                                  #'/Users/danyvohl/code/data')

        if filename[0] != "":
            # Load file
            print(filename)
            self.loaded_cube = fits.open(filename[0])

            try:
                self.vol_min = self.loaded_cube[0].header["DATAMIN"]
                self.vol_max = self.loaded_cube[0].header["DATAMAX"]

                print ("DATAMIN", self.vol_min)
                print ("DATAMAX", self.vol_max)
            except:
                print ("DATAMIN and DATAMAX not present in header; evaluating min and max")
                if self.loaded_cube[0].header["NAXIS"] == 3:
                    self.vol_min = np.nanmin(self.loaded_cube[0].data)
                    self.vol_max = np.nanmax(self.loaded_cube[0].data)
                else:
                    self.vol_min = np.nanmin(self.loaded_cube[0].data[0])
                    self.vol_max = np.nanmax(self.loaded_cube[0].data[0])

            # # Will trigger update clim
            # self.l_clim_min.setText(str(min))
            # self.l_clim_max.setText(str(max))

            for widgets in self.widgets_array:
                for widget in widgets:
                    widget.setEnabled(True)

            # Update label
            self.l_high_discard_filter_value.setText(str(self.vol_min))
            self.l_low_discard_filter_value.setText(str(self.vol_min))

            self.signal_file_loaded.emit()
            self.signal_objet_changed.emit()
            self.signal_camera_changed.emit()

    def update_clim(self):
        self.signal_file_loaded.emit()

    def update_camera(self, option):
        self.l_fov_value.setText(str(self.slider_fov.value()))
        self.signal_camera_changed.emit()

    def update_autorotate(self):
        self.signal_autorotate_changed.emit()
        
    def update_log_scale(self):
        self.signal_log_scale_changed.emit()

    def update_scaling(self):
        self.l_scalex_value.setText(str(self.slider_scalex.value()))
        self.l_scaley_value.setText(str(self.slider_scaley.value()))
        self.l_scalez_value.setText(str(self.slider_scalez.value()))
        self.signal_scaling_changed.emit()

    def update_threshold(self):
        scaled_value = self.scale_value(self.slider_threshold.value(),
                                        self.slider_threshold.minimum(),
                                        self.slider_threshold.maximum(),
                                        self.vol_min,
                                        self.vol_max)

        self.l_threshold_value.setText(str(scaled_value))
        self.signal_threshold_changed.emit()

    def update_color_scale(self):
        self.signal_color_scale_changed.emit()

    def update_filter_size(self):
        self.l_filter_size_value.setText(str(self.slider_filter_size.value() + self.slider_filter_size.value()+1 ))
        self.signal_filter_size_changed.emit()

    def update_filter_type(self):
        if self.combo_filter_type.currentText() == 'Rescale':
            for widget in self.widgets_dict['high_discard_filter']:
                widget.show()
        else:
            for widget in self.widgets_dict['high_discard_filter']:
                widget.hide()

        self.signal_filter_type_changed.emit()

    def update_gaussian_filter_size(self):
        self.signal_filter_size_changed.emit()

    def update_high_discard_filter(self):

        #(log_x - np.min(log_x)) * (nbins / (np.max(log_x) - np.min(log_x)))

        self.high_scaled_value = self.scale_value(self.slider_high_discard_filter.value(),
                                        self.slider_high_discard_filter.minimum(),
                                        self.slider_high_discard_filter.maximum(),
                                        self.vol_min,
                                        self.vol_max)

        self.l_high_discard_filter_value.setText(str(self.high_scaled_value))
        self.signal_high_discard_filter_changed.emit()
    
    def update_low_discard_filter(self):

        #(log_x - np.min(log_x)) * (nbins / (np.max(log_x) - np.min(log_x)))

        self.low_scaled_value = self.scale_value(self.slider_low_discard_filter.value(),
                                        self.slider_low_discard_filter.minimum(),
                                        self.slider_low_discard_filter.maximum(),
                                        self.vol_min,
                                        self.vol_max)

        self.l_low_discard_filter_value.setText(str(self.low_scaled_value))
        self.signal_low_discard_filter_changed.emit()

    def update_density_factor(self):
        scaled_value = self.scale_value(self.slider_density_factor.value(),
                                        self.slider_density_factor.minimum(),
                                        self.slider_density_factor.maximum(),
                                        0.001,
                                        1)

        self.l_density_factor_value.setText(str(scaled_value))
        self.signal_density_factor_changed.emit()


    def scale_value(self, old_value, old_min, old_max, new_min, new_max):
        """
        Scale a value from it's original range to another, arbitrary, range

        :param old_value: Value to be scaled
        :param old_min: Minimum of the original range
        :param old_max: Maximum of the original range
        :param new_min: Minimum of the new range
        :param new_max: Maximum of the new range
        :return: Scaled value
        """
        old_range = old_max - old_min
        if old_range == 0:
            new_range = new_min
        else:
            new_range = (new_max - new_min)
            new_value = (((old_value - old_min) * new_range) / old_range) + new_min

        return new_value

    def export_image(self):
        self.signal_export_image.emit()

class Canvas3D(scene.SceneCanvas):

    def __init__(self):
        self._configured = False
        self._fg=(0.5, 0.5, 0.5, 1)

        scene.SceneCanvas.__init__(self,
                                   keys='interactive',
                                   size=(800, 600),
                                   show=True)
        #self.measure_fps()

        self._configure_canvas()

        # Add a 3D axis to keep us oriented
        #scene.visuals.XYZAxis(parent=self.view.scene)

    def _configure_canvas(self):
        self.unfreeze()

        # Set up a viewbox to display the image with interactive pan/zoom
        # and colorbar

        self.central_widget.bgcolor = "#404040"
        self.grid = self.central_widget.add_grid(spacing=0, margin=0)
        self._configure_3d()

        self.freeze()

    def _configure_3d(self):
        if self._configured:
            return

        #     c0      c1      c2
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
        self.cbar_left = self.grid.add_widget(None, row=0, col=0,border_color='#404040', bgcolor="#404040")
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
        self.view = self.grid.add_view(row=0, col=1,row_span=2,
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

        self.cbar.label.font_size = 15
        self.cbar.label.color = "white"
        self.cbar.ticks[0].font_size = 8
        self.cbar.ticks[1].font_size = 8
        self.cbar.ticks[0].color = "white"
        self.cbar.ticks[1].color = "white"

        CBAR_LONG_DIM = 200

        # colorbar - column 1
        # view - column 2

        if self.cbar.orientation == "bottom":
            self.grid.remove_widget(self.cbar_bottom)
            self.cbar_bottom = self.grid.add_widget(self.cbar, row=2, col=1)
            self.cbar_bottom.height_max = \
                self.cbar_bottom.height_max = CBAR_LONG_DIM

        elif self.cbar.orientation == "top":
            self.grid.remove_widget(self.cbar_top)
            self.cbar_top = self.grid.add_widget(self.cbar, row=0, col=1)
            self.cbar_top.height_max = self.cbar_top.height_max = CBAR_LONG_DIM

        elif self.cbar.orientation == "left":
            #self.grid.remove_widget(self.cbar_left)
            self.grid.remove_widget(self.cbar)
            self.cbar_left = self.grid.add_widget(self.cbar, row=0, col=0)
            self.cbar_left.width_max = self.cbar_left.width_min = CBAR_LONG_DIM

        else:  # self.cbar.orientation == "right"
            self.grid.remove_widget(self.cbar_right)
            self.cbar_right = self.grid.add_widget(self.cbar, row=2, col=2)
            self.cbar_right.width_max = \
                self.cbar_right.width_min = CBAR_LONG_DIM

        #return cbar

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

        Returns
        -------
        hist : instance of Polygon
            The histogram polygon.
        """
        self.view_histogram = self.grid.add_view(row=1, col=0, border_color='#404040', bgcolor="#404040")
        self.view_histogram.camera = 'panzoom'
        #self.camera_histogram = self.view_histogram.camera

        self.hist = scene.Histogram(data, bins, color, orientation)
        self.view_histogram.add(self.hist)
        self.view_histogram.camera.set_range()
        #return self.hist

    def set_volume_scene(self, cube):
        # # Set up a viewbox to display the image with interactive pan/zoom
        if self.view:
            canvas = self.central_widget.remove_widget(self.grid)
            self._configure_canvas()

        self.unfreeze()
        self.view = self.grid.add_view(row=0, col=1, row_span=2,
                                       border_color='#404040', bgcolor="#404040")

        try:
            # Quick fix -- will need to be a bit more clever.
            # print cube[0].data.shape
            # if len(cube[0].data.shape) == 4:
            #     # Currently forces a hard 2048 limit to avoid overflowing the gpu texture memory...
            #     data = cube[0].data[0][:2048,:2048,:2048]
            #     self.clim_vel = 0, cube[0].data[0].shape[0]
            # else:
            #     # Currently forces a hard 2048 limit to avoid overflowing the gpu texture memory...
            #     data = cube[0].data[:2048,:2048,:2048]
            #     self.clim_vel = 0, cube[0].data.shape[0]
            #
            # try:
            #     self.bunit = cube[0].header['BUNIT']
            # except:
            #     self.bunit = "unknown"
            #
            # try:
            #     self.vel = cube[0].header['CTYPE3']
            # except:
            #     self.vel = "unknown"

            data = self.parse_header_info(cube)

            self.volume = RenderVolume(data,
                                       parent=self.view.scene,
                                       threshold=0.225,
                                       emulate_texture=False)
                                       #clim=[clim_min, clim_max])

            # TODO: Should spread this...
            self.data_shape = data.shape

            self.aspect = [1.,1.,1.]
            self.aspect[0] = 1.
            self.aspect[1] = self.data_shape[1] / self.data_shape[2]
            self.aspect[2] = self.data_shape[0] / self.data_shape[2]

            scale_cube = [2 / self.data_shape[2] * 1 * self.aspect[0],
                          2 / self.data_shape[1] * 1 * self.aspect[1],
                          2 / self.data_shape[0] * 1 * self.aspect[2]]

            translate_cube = [-0.5 * self.data_shape[2] * scale_cube[0],
                              -0.5 * self.data_shape[1] * scale_cube[1],
                              -0.5 * self.data_shape[0] * scale_cube[2]]

            self.volume.transform = scene.STTransform(scale=scale_cube, translate=translate_cube)



            # Add a mesh to simulate a box around the volume rendering. Acts as 3D axis.
            # Should eventually add measurements taken from fits header (RA, DEC...).
            #vertices, filled_indices, outline_indices = self.create_cube(data.shape)

            #factor = np.max(data.shape)

            # self.axis = AxesVisual3D(data.shape, vertices, filled_indices, outline_indices,
            #                          axis_color="white", tick_color="white", text_color="white",
            #                          tick_width=1, minor_tick_length=2,
            #                          major_tick_length=4, axis_width=0,
            #                          tick_label_margin=15*factor, axis_label_margin=40*factor,
            #                          tick_font_size=7*factor, axis_font_size=12*factor,
            #                          view=self.view,
            #                          transform=scene.STTransform())

            scale_axis = [self.aspect[0],
                          self.aspect[1],
                          self.aspect[2]]

            self.axes = AxesVisual3D(axis_color="white", tick_color="white", text_color="white",
                                     tick_width=1.5, minor_tick_length=0,
                                     major_tick_length=15, axis_width=0,
                                     tick_label_margin=40, axis_label_margin=200,
                                     tick_font_size=28, axis_font_size=45,
                                     view=self.view,
                                     transform=scene.STTransform(scale=scale_axis))

            self.axes.xlabel = self.axes_info[0]['label']
            self.axes.ylabel = self.axes_info[1]['label']
            self.axes.zlabel = self.axes_info[2]['label']

            # self.axis.tick_font_size = 28
            # self.axis.axis_font_size = 35

            # self.axis.xlabel = self.options.x_att.label
            # self.axis.ylabel = self.options.y_att.label
            # self.axis.zlabel = self.options.z_att.label
            #
            #self.axis.xlim = self.options.x_min, self.options.x_max
            self.axes.xlim = self.axes_info[0]['minval'], self.axes_info[0]['maxval']
            self.axes.ylim = self.axes_info[1]['minval'], self.axes_info[1]['maxval']
            self.axes.zlim = self.axes_info[2]['minval'], self.axes_info[2]['maxval']


            # self.axis = scene.visuals.Mesh(vertices['position'],
            #                                outline_indices,
            #                                color="white",
            #                                parent=self.view.scene,
            #                                mode='lines')
            # self.view.scene.add(self.axis)

            # Cheat to make the box width bigger.
            #
            # pos = np.array([[0, 0, 0], [1, 1, 1]])
            # self.line = scene.Line(pos=pos,
            #                   color='green',
            #                   method='gl',
            #                   width=2,
            #                   connect='strip',
            #                   parent=self.view.scene)
            # self.line.antialias = 1


            # Add colorbar
            self.colorbar(label=str(self.vel_type),
                          clim=self.volume.clim,
                          #label=str(self.bunit),
                          #clim=self.volume.clim,
                          cmap="hsl",
                          border_width=0,
                          border_color="#404040")

            # self.histogram(data.ravel())



            # self.rotation and self.timer used for autorotate.
            self.rotation = scene.MatrixTransform()
            self.timer = app.Timer(connect=self.rotate)
            self.angle = 0.

            self.freeze()

        except ValueError as e:
            t = e
            print (t)

    #def set_data(self, data, vr_method, cmap, clim_min, clim_max):
    def set_data(self, vr_method, cmap, combo_color_method, interpolation_method):
        self.volume.method = vr_method
        self.volume.cmap = cmap
        self.volume.color_method = combo_color_method
        self.volume.interpolation = interpolation_method

        print (self.volume.color_method)
        if (self.volume.color_method == 0):
            label = str(self.bunit)
            print ("label", label)
            clim = self.volume.clim
        else:
            label = str(self.vel_type)
            print("label", label)
            clim = self.clim_vel

        # print ('clim', clim)

        self.cbar.clim = clim
        self.cbar.label_str = label
        self.cbar.cmap = cmap

        #self.volume.set_data(data, [clim_min, clim_max])

    def set_threshold(self, threshold):
        try:
            threshold = float(threshold)
        except:
            print ("Threshold: need to be a float")
            pass

        try:
            threshold -= self.volume.clim[0]
            threshold /= self.volume.clim[1] - self.volume.clim[0]
            self.volume.threshold = threshold
            # print (self.volume.threshold)
        except:
            print ("Invalid threshold")
            pass

    def set_color_scale(self, color_scale):
        self.volume.color_scale = color_scale

    def set_filter_size(self, filter_size):
        self.volume.filter_size = filter_size

    def set_filter_type(self, filter_type):
        self.volume.filter_type = filter_type

    def set_gaussian_filter(self, use_gaussian_filter, gaussian_filter_size):
        self.volume.use_gaussian_filter = use_gaussian_filter
        self.volume.gaussian_filter_size = gaussian_filter_size

    def set_high_discard_filter(self, high_discard_filter_value, scaled_value):
        self.volume.high_discard_filter_value = high_discard_filter_value
        self.update_clim("high", scaled_value)
   
    def set_low_discard_filter(self, low_discard_filter_value, scaled_value):
        self.volume.low_discard_filter_value = low_discard_filter_value
        self.update_clim("low", scaled_value)

    def update_clim(self, type, value):
        print("self.volume.color_method", self.volume.color_method)
        if (self.volume.color_method == 0):
            if type == "low":
                self.cbar.clim = [value, self.cbar.clim[1]]
            if type == "high":
                self.cbar.clim = [self.cbar.clim[0], value]

    def set_density_factor(self, density_factor):
        # print (density_factor)
        self.volume.density_factor = density_factor

    def set_camera(self, cam, fov):
        if cam == 'PerspectiveCamera':
            if fov == 0:
                if self.visible_axes:
                    self.axes.parent = self.view.scene
                else:
                    self.axes.parent = None

            self.view.camera = scene.cameras.PerspectiveCamera(parent=self.view.scene,
                                                               fov=float(fov),
                                                               name='PerspectiveCamera',
                                                               center=(0, 0, 0),
                                                               distance=4.)
        if cam == 'Turntable':
            self.view.camera = scene.cameras.TurntableCamera(parent=self.view.scene,
                                                             elevation=0.,
                                                             azimuth=0.,
                                                             fov=float(fov),
                                                             name='Turntable',
                                                             center=(0, 0, 0),
                                                             distance=4.)
        if cam == 'Fly':
            self.view.camera = scene.cameras.FlyCamera(parent=self.view.scene,
                                                       fov=float(fov),
                                                       name='Fly',
                                                       center=(0, 0, 0))
        if cam == 'Arcball':
            self.view.camera = scene.cameras.ArcballCamera(parent=self.view.scene,
                                                           fov=float(fov),
                                                           name='Arcball',
                                                           center=(0, 0, 0))

    def set_autorotate(self, flag):
        if flag == True:
            # self.set_camera("PerspectiveCamera", 60)
            self.timer.start(0.01)
        else:
            self.timer.stop()

    def rotate(self, event):
        #self.angle += .005
        self.angle = 1.5
        # self.rotation.rotate(self.angle, (0, 0, 1))
        # self.axis.transform = self.volume.transform = self.rotation
        self.view.camera.orbit(self.angle, 0)

    def set_log_scale(self, flag):
        self.volume.log_scale = flag

    def set_scaling(self, scalex, scaley, scalez):
        scale_cube = [2 / self.data_shape[2] * scalex * self.aspect[0],
                      2 / self.data_shape[1] * scaley * self.aspect[1],
                      2 / self.data_shape[0] * scalez * self.aspect[2]]

        translate_cube = [-0.5 * self.data_shape[2] * scale_cube[0],
                          -0.5 * self.data_shape[1] * scale_cube[1],
                          -0.5 * self.data_shape[0] * scale_cube[2]]

        self.volume.transform = scene.STTransform(scale=scale_cube, translate=translate_cube)

        # TODO: adjust translation rate to be slower (currently very easily get off the window)
        # TODO: fix axes scaling to fit volume

        # self.aspect = [1., 1., 1.]
        # self.aspect[0] = 1.
        # self.aspect[1] = self.data_shape[1] / self.data_shape[2]
        # self.aspect[2] = self.data_shape[0] / self.data_shape[2]

        scale_axis = [scalex * self.aspect[0],
                      scaley * self.aspect[1],
                      scalez * self.aspect[2]]

        self.axes.transform = scene.STTransform(scale=scale_axis)

    def parse_header_info(self, cube):
        # create 3
        self.axes_info = [{},{},{}]

        #CTYPE1, CRVAL1, and CDELT1
        print(cube[0].data.shape)
        if len(cube[0].data.shape) == 4:
            # Test
            # cube[0].data = np.swapaxes(cube[0].data, 0, 1)
            index = [1,3,2]
            for i in range(3):
                self.axes_info[i]['label'] = cube[0].header['CTYPE' + str(index[i])]
                self.axes_info[i]['minval'] = cube[0].header['CRVAL' + str(index[i])]
                self.axes_info[i]['maxval'] = (cube[0].data[0].shape[2-i] * cube[0].header['CDELT' + str(index[i])]) - self.axes_info[i]['minval']

            # Currently forces a hard 2048 limit to avoid overflowing the gpu texture memory...
            data = cube[0].data[0][:2048, :2048, :2048]
            # data = cube[0].data[0][75:150, 110:150, 100:150]

            self.vel_axis = cube[0].data[0].shape[0]
        else:
            index = [1,3,2]
            for i in range(3):
                self.axes_info[i]['label'] = cube[0].header['CTYPE' + str(index[i])]
                self.axes_info[i]['minval'] = cube[0].header['CRVAL' + str(index[i])]
                self.axes_info[i]['maxval'] = (cube[0].data.shape[2-i] * cube[0].header['CDELT' + str(index[i])]) - cube[0].header['CRVAL' + str(index[i])]
            
            # Currently forces a hard 2048 limit to avoid overflowing the gpu texture memory...
            data = cube[0].data[:2048, :2048, :2048]
            # data = cube[0].data[:,60:-60,:]
            # data = cube[0].data[:, :, :]
            self.vel_axis = cube[0].data.shape[0]

        try:
            self.bunit = cube[0].header['BUNIT']
        except:
            self.bunit = "unknown"

        try:
            self.vel_type = cube[0].header['CTYPE3']
        except:
            self.vel_type = "Epoch"

        try:
            self.vel_val = cube[0].header['CRVAL3']

            if self.vel_type == 'VELO-HEL' or self.vel_type == 'FELO-HEL':
                self.vel_type += ' (km/s)'
            elif self.vel_type == 'WAVE':
                self.vel_type += ' (' + cube[0].header['CUNIT3'] + ')'
        except:
            self.vel_val = "Undefined"

        try:
            self.vel_delt = cube[0].header['CDELT3']

            if self.vel_type == 'VELO-HEL':
                # Currently in m/s
                self.clim_vel = np.int(np.round(float(self.vel_val) / 1000)), np.int(np.round((float(self.vel_val) +
                                                                                               float(self.vel_delt) *
                                                                                               self.vel_axis) / 1000))
            else:
                self.clim_vel = np.int(np.round(float(self.vel_val))), np.int(np.round((float(self.vel_val) +
                                                                                        float(self.vel_delt) *
                                                                                        self.vel_axis)))
        except:
            try:
                self.vel_delt = cube[0].header['STEP']
                self.clim_vel = np.int(np.round(float(self.vel_val))), np.int(np.round((float(self.vel_val) +
                                                                                        float(self.vel_delt) *
                                                                                        self.vel_axis)))
            except:
                self.clim_vel = 0, self.vel_axis

        data = np.flipud(np.rollaxis(data, 1))
        return data


# -----------------------------------------------------------------------------
# gloo.gl.use_gl('gl2 debug')
if __name__ == '__main__':
    appQt = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    appQt.exec_()