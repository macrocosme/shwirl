# -*- coding: utf-8 -*-
from __future__ import division

# Basic imports
import sys
import numpy as np

# Vispy imports
from extern.vispy import scene, plot, io
from extern.vispy.color import get_colormaps, BaseColormap
from extern.vispy import gloo

# from vispy.geometry import create_cube
from shades import RenderVolume

# Astropy imports
from astropy import wcs
from astropy.io import fits

# Window related
try:
    from sip import setapi

    setapi("QVariant", 2)
    setapi("QString", 2)
except ImportError:
    pass

from PyQt4 import QtGui, QtCore


# gloo.gl.use_gl('gl2 debug')

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        # self.resize(1800, 1000)
        self.resize(800, 600)
        self.setWindowTitle('Shaded Astro Data Cube')

        splitter_h = QtGui.QSplitter(QtCore.Qt.Horizontal)
        splitter_v = QtGui.QSplitter(QtCore.Qt.Vertical)

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
        # splitter_h.addWidget(splitter_v)

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
        self.props.signal_scaling_changed.connect(self.update_scaling)
        self.props.signal_threshold_changed.connect(self.update_threshold)
        # self.props.signal_color_scale_changed.connect(self.update_color_scale)
        self.props.signal_filter_size_changed.connect(self.update_filter_size)
        self.props.signal_low_discard_filter_changed.connect(self.update_low_discard_filter)
        self.props.signal_density_factor_changed.connect(self.update_density_factor)
        self.props.signal_export_image.connect(self.export_image)

        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))

    def load_volume(self):
        self.Canvas3D.set_volume_scene(self.props.loaded_cube)
        self.fits_infos.print_header(self.props.loaded_cube[0].header)
        # self.Canvas2D.set_histogram(self.props.loaded_cube)

    def update_view(self):
        # vr_method, cmap
        self.Canvas3D.set_data(self.props.combo_vr_method.currentText(),
                               self.props.combo_cmap.currentText(),
                               self.props.combo_color_method.currentText(),
                               self.props.combo_interpolation_method.currentText())

        if self.props.combo_vr_method.currentText() == 'lmip':
            self.update_threshold(self.props.l_threshold_value.text())

    def update_camera(self):
        self.Canvas3D.set_camera(self.props.combo_camera.currentText(),
                                 self.props.slider_fov.value())

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

    def update_low_discard_filter(self):
        self.Canvas3D.set_low_discard_filter(self.props.l_low_discard_filter_value.text())

    def update_density_factor(self):
        self.Canvas3D.set_density_factor(self.props.l_density_factor_value.text())

    def export_image(self):
        img = self.Canvas3D.render()
        io.write_png('images/image.png', img)


class FitsMetaWidget(QtGui.QWidget):
    """
    Widget for editing Volume parameters
    """

    # signal_objet_changed = QtCore.pyqtSignal(name='objectChanged')

    def __init__(self, parent=None):
        super(FitsMetaWidget, self).__init__(parent)

        l_title = QtGui.QLabel("Fits Primary Header")

        self.l_header = QtGui.QTextEdit("No fits loaded ")
        self.l_header.setReadOnly(True)

        font = self.l_header.font()
        font.setFamily("Avenir")
        font.setPointSize(12)

        gbox = QtGui.QGridLayout()
        # ------ Adding Widgets
        gbox.addWidget(l_title, 0, 1)
        gbox.addWidget(self.l_header, 1, 1)

        vbox = QtGui.QVBoxLayout()
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


class ObjectWidget(QtGui.QWidget):
    """
    Widget for editing Volume parameters
    """
    signal_objet_changed = QtCore.pyqtSignal(name='objectChanged')
    signal_file_loaded = QtCore.pyqtSignal(name='fileLoaded')
    signal_camera_changed = QtCore.pyqtSignal(name='cameraChanged')
    signal_scaling_changed = QtCore.pyqtSignal(name='scalingChanged')
    signal_threshold_changed = QtCore.pyqtSignal(name='thresholdChanged')
    signal_color_scale_changed = QtCore.pyqtSignal(name='color_scaleChanged')
    signal_filter_size_changed = QtCore.pyqtSignal(name='filter_sizeChanged')
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

        self.load_button = QtGui.QPushButton("Load FITS", self)
        self.load_button.clicked.connect(self.showDialog)
        array = [self.load_button]
        serialize_widgets('fits_button', array)

        l_cam = QtGui.QLabel("Camera ")
        self.camera = ['Turntable', 'Fly', 'Arcball']  # 'PerspectiveCamera',
        self.combo_camera = QtGui.QComboBox(self)
        self.combo_camera.addItems(self.camera)
        self.combo_camera.currentIndexChanged.connect(self.update_camera)
        array = [l_cam, self.combo_camera]
        serialize_widgets('camera', array)

        l_fov = QtGui.QLabel("Field of View ")
        self.slider_fov = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_fov.setMinimum(0)
        self.slider_fov.setMaximum(160)
        self.slider_fov.setValue(60)
        self.slider_fov.setTickInterval(5)
        self.l_fov_value = QtGui.QLineEdit(str(self.slider_fov.value()))
        self.slider_fov.valueChanged.connect(self.update_camera)
        array = [l_fov, self.slider_fov, self.l_fov_value]
        serialize_widgets('field_of_view', array)

        l_vr_method = QtGui.QLabel("VR method ")
        # self.l_vr_method = ['mip', 'translucent', 'iso', 'additive']
        self.vr_method = ['mip', 'lmip', 'translucent', 'MeanIP', 'iso']
        self.combo_vr_method = QtGui.QComboBox(self)
        self.combo_vr_method.addItems(self.vr_method)
        self.combo_vr_method.currentIndexChanged.connect(self.update_param)
        array = [l_vr_method, self.combo_vr_method]
        serialize_widgets('vr_method', array)

        l_density_factor = QtGui.QLabel("Density regulator ")
        self.slider_density_factor = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_density_factor.setMinimum(0)
        self.slider_density_factor.setMaximum(10000)
        self.slider_density_factor.setValue(10000)
        self.l_density_factor_value = QtGui.QLineEdit(str(1))
        self.slider_density_factor.valueChanged.connect(self.update_density_factor)
        array = [l_density_factor, self.slider_density_factor, self.l_density_factor_value]
        serialize_widgets('density_factor', array)

        l_color_method = QtGui.QLabel("Color method ")
        self.color_method = ['voxel', 'velocity/redshift']
        self.combo_color_method = QtGui.QComboBox(self)
        self.combo_color_method.addItems(self.color_method)
        self.combo_color_method.currentIndexChanged.connect(self.update_param)
        array = [l_color_method, self.combo_color_method]
        serialize_widgets('color_method', array)

        l_threshold = QtGui.QLabel("Threshold ")
        self.slider_threshold = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_threshold.setMinimum(0)
        self.slider_threshold.setMaximum(10000)
        self.slider_threshold.setValue(10000)
        self.l_threshold_value = QtGui.QLineEdit(str(self.slider_threshold.value()))
        self.slider_threshold.valueChanged.connect(self.update_threshold)
        array = [l_threshold, self.slider_threshold, self.l_threshold_value]
        serialize_widgets('threshold', array)

        l_interpolation_method = QtGui.QLabel("Interpolation method ")
        self.interpolation_method = ['linear', 'nearest']  # ,
        # 'bilinear', 'hanning', 'hamming', 'hermite',
        # 'kaiser', 'quadric', 'bicubic', 'catrom',
        # 'mitchell', 'spline16', 'spline36', 'gaussian',
        # 'bessel', 'sinc', 'lanczos', 'blackman']
        self.combo_interpolation_method = QtGui.QComboBox(self)
        self.combo_interpolation_method.addItems(self.interpolation_method)
        self.combo_interpolation_method.currentIndexChanged.connect(self.update_param)
        array = [l_interpolation_method, self.combo_interpolation_method]
        serialize_widgets('interpolation_method', array)

        l_cmap = QtGui.QLabel("Cmap ")
        self.cmap = list(get_colormaps().keys())
        self.combo_cmap = QtGui.QComboBox(self)
        self.combo_cmap.addItems(self.cmap)
        self.combo_cmap.currentIndexChanged.connect(self.update_param)
        array = [l_cmap, self.combo_cmap]
        serialize_widgets('cmap', array)

        # l_color_scale = QtGui.QLabel("Color scale ")
        # self.color_scale = ['linear', 'log', 'exp']
        # self.combo_color_scale = QtGui.QComboBox(self)
        # self.combo_color_scale.addItems(self.color_scale)
        # self.combo_color_scale.currentIndexChanged.connect(self.update_color_scale)
        # array = [l_color_scale, self.combo_color_scale]
        # serialize_widgets('color_scale', array)

        l_scalex = QtGui.QLabel("Scale X ")
        self.slider_scalex = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_scalex.setMinimum(1)
        self.slider_scalex.setMaximum(20)
        self.slider_scalex.setValue(1)
        self.slider_scalex.setTickInterval(1)
        self.l_scalex_value = QtGui.QLineEdit(str(self.slider_scalex.value()))
        self.slider_scalex.valueChanged.connect(self.update_scaling)
        array = [l_scalex, self.slider_scalex, self.l_scalex_value]
        serialize_widgets('scale_x', array)

        l_scaley = QtGui.QLabel("Scale Y ")
        self.slider_scaley = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_scaley.setMinimum(1)
        self.slider_scaley.setMaximum(20)
        self.slider_scaley.setValue(1)
        self.slider_scaley.setTickInterval(1)
        self.l_scaley_value = QtGui.QLineEdit(str(self.slider_scaley.value()))
        self.slider_scaley.valueChanged.connect(self.update_scaling)
        array = [l_scaley, self.slider_scaley, self.l_scaley_value]
        serialize_widgets('scale_y', array)

        l_scalez = QtGui.QLabel("Scale Z ")
        self.slider_scalez = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_scalez.setMinimum(1)
        self.slider_scalez.setMaximum(20)
        self.slider_scalez.setValue(1)
        self.slider_scalez.setTickInterval(1)
        self.l_scalez_value = QtGui.QLineEdit(str(self.slider_scalez.value()))
        self.slider_scalez.valueChanged.connect(self.update_scaling)
        array = [l_scalez, self.slider_scalez, self.l_scalez_value]
        serialize_widgets('scale_z', array)

        l_filter_size = QtGui.QLabel("Filter size ")
        self.slider_filter_size = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_filter_size.setMinimum(0)
        self.slider_filter_size.setMaximum(10)
        self.slider_filter_size.setValue(0)
        self.l_filter_size_value = QtGui.QLineEdit(str(self.slider_filter_size.value() + 1))
        self.slider_filter_size.valueChanged.connect(self.update_filter_size)
        array = [l_filter_size, self.slider_filter_size, self.l_filter_size_value]
        serialize_widgets('filter_size', array)

        l_use_gaussian_filter = QtGui.QLabel("Activate Gaussian filter")
        self.use_gaussian_filter = ['0', '1']  # 'PerspectiveCamera',
        self.combo_use_gaussian_filter = QtGui.QComboBox(self)
        self.combo_use_gaussian_filter.addItems(self.use_gaussian_filter)
        self.combo_use_gaussian_filter.currentIndexChanged.connect(self.update_gaussian_filter_size)
        array = [l_use_gaussian_filter, self.combo_use_gaussian_filter]
        serialize_widgets('use_gaussian_filter', array)

        l_gaussian_filter_size = QtGui.QLabel("Gaussian filter size ")
        self.gaussian_filter_size = ['5', '9', '13']  # 'PerspectiveCamera',
        self.combo_gaussian_filter_size = QtGui.QComboBox(self)
        self.combo_gaussian_filter_size.addItems(self.gaussian_filter_size)
        self.combo_gaussian_filter_size.currentIndexChanged.connect(self.update_gaussian_filter_size)
        array = [l_gaussian_filter_size, self.combo_gaussian_filter_size]
        serialize_widgets('gaussian_filter_size', array)

        l_low_discard_filter = QtGui.QLabel("Low discard filter ")
        self.slider_low_discard_filter = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_low_discard_filter.setMinimum(0)
        self.slider_low_discard_filter.setMaximum(10000)
        self.slider_low_discard_filter.setValue(0)
        self.l_low_discard_filter_value = QtGui.QLineEdit(str(self.slider_low_discard_filter.value()))
        self.slider_low_discard_filter.valueChanged.connect(self.update_low_discard_filter)
        array = [l_low_discard_filter, self.slider_low_discard_filter, self.l_low_discard_filter_value]
        serialize_widgets('low_discard_filter', array)

        self.export_image_button = QtGui.QPushButton("export_image", self)
        self.export_image_button.clicked.connect(self.export_image)
        array = [self.export_image_button]
        serialize_widgets('export_image', array)

        gbox = QtGui.QGridLayout()

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

        vbox = QtGui.QVBoxLayout()
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
        filename = QtGui.QFileDialog.getOpenFileName(self,
                                                     'Open file',
                                                     '/Users/danyvohl/code/data')

        if filename != "":
            # Load file
            self.loaded_cube = fits.open(filename)

            try:
                self.vol_min = self.loaded_cube[0].header["DATAMIN"]
                self.vol_max = self.loaded_cube[0].header["DATAMAX"]

                print("DATAMIN", self.vol_min)
                print("DATAMAX", self.vol_max)
            except:
                print("DATAMIN and DATAMAX not present in header; evaluating min and max")
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
            self.l_low_discard_filter_value.setText(str(self.vol_min))

            self.signal_file_loaded.emit()
            self.signal_objet_changed.emit()
            self.signal_camera_changed.emit()

    def update_clim(self):
        self.signal_file_loaded.emit()

    def update_camera(self, option):
        self.l_fov_value.setText(str(self.slider_fov.value()))
        self.signal_camera_changed.emit()

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
        self.l_filter_size_value.setText(str(self.slider_filter_size.value() + self.slider_filter_size.value() + 1))
        self.signal_filter_size_changed.emit()

    def update_gaussian_filter_size(self):
        self.signal_filter_size_changed.emit()

    def update_low_discard_filter(self):

        # (log_x - np.min(log_x)) * (nbins / (np.max(log_x) - np.min(log_x)))

        scaled_value = self.scale_value(self.slider_low_discard_filter.value(),
                                        self.slider_low_discard_filter.minimum(),
                                        self.slider_low_discard_filter.maximum(),
                                        self.vol_min,
                                        self.vol_max)

        self.l_low_discard_filter_value.setText(str(scaled_value))
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
        self._fg = (0.5, 0.5, 0.5, 1)

        scene.SceneCanvas.__init__(self,
                                   keys='interactive',
                                   size=(800, 600),
                                   show=True)

        self._configure_canvas()

        # Add a 3D axis to keep us oriented
        # scene.visuals.XYZAxis(parent=self.view.scene)

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

        # colorbar
        # row 0, column 0
        self.cbar_left = self.grid.add_widget(None, row=0, col=0, border_color='#404040', bgcolor="#404040")
        self.cbar_left.width_max = 0

        # 2D histogram
        # row 1, column 0
        # self.view_histogram = self.grid.add_view(row=1, col=0, border_color='#404040', bgcolor="#404040")
        # self.view_histogram.camera = 'panzoom'
        # self.camera_histogram = self.view_histogram.camera

        # 3D visualisation
        # row 0-1, column 1
        self.view = self.grid.add_view(row=0, col=1, row_span=2,
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
                                         label_str=label,
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
            # self.grid.remove_widget(self.cbar_left)
            self.grid.remove_widget(self.cbar)
            self.cbar_left = self.grid.add_widget(self.cbar, row=0, col=0)
            self.cbar_left.width_max = self.cbar_left.width_min = CBAR_LONG_DIM

        else:  # self.cbar.orientation == "right"
            self.grid.remove_widget(self.cbar_right)
            self.cbar_right = self.grid.add_widget(self.cbar, row=2, col=2)
            self.cbar_right.width_max = \
                self.cbar_right.width_min = CBAR_LONG_DIM

            # return cbar

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
        # self.camera_histogram = self.view_histogram.camera

        self.hist = scene.Histogram(data, bins, color, orientation)
        self.view_histogram.add(self.hist)
        self.view_histogram.camera.set_range()
        # return self.hist

    def set_volume_scene(self, cube):
        # # Set up a viewbox to display the image with interactive pan/zoom
        if self.view:
            self.central_widget.remove_widget(self.grid)
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

            print
            cube[0].data.shape
            if len(cube[0].data.shape) == 4:
                # Currently forces a hard 2048 limit to avoid overflowing the gpu texture memory...
                data = cube[0].data[0][:2048, :2048, :2048]
                self.vel_axis = cube[0].data[0].shape[0]
            else:
                # Currently forces a hard 2048 limit to avoid overflowing the gpu texture memory...
                # data = cube[0].data[:2048, :2048, :2048]
                data = cube[0].data[:, 60:-60, :]
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
                self.vel_delt = cube[0].header['CDELT3']

                if self.vel_type == 'VELO-HEL':
                    # Currently in m/s
                    self.vel_type = 'km/s'
                    self.clim_vel = np.int(np.round(float(self.vel_val) / 1000)), np.int(np.round((float(self.vel_val) +
                                                                                                   float(
                                                                                                       self.vel_delt) *
                                                                                                   self.vel_axis) / 1000))
                else:
                    if self.vel_type == 'FELO-HEL':
                        self.vel_type = 'km/s'

                    self.clim_vel = np.int(np.round(float(self.vel_val))), np.int(np.round((float(self.vel_val) +
                                                                                            float(self.vel_delt) *
                                                                                            self.vel_axis)))
            except:
                self.clim_vel = 0, self.vel_axis

            data = np.flipud(np.rollaxis(data, 1))

            self.volume = RenderVolume(data,
                                       parent=self.view.scene,
                                       threshold=0.225,
                                       emulate_texture=False)
            # clim=[clim_min, clim_max])

            # Add a mesh to simulate a box around the volume rendering. Acts as 3D axis.
            # Should eventually add measurements taken from fits header (RA, DEC...).
            vertices, filled_indices, outline_indices = self.create_cube(data.shape)
            self.axis = scene.visuals.Mesh(vertices['position'],
                                           outline_indices,
                                           color="white",
                                           parent=self.view.scene,
                                           mode='lines')

            # Add colorbar
            self.colorbar(label=str(self.vel_type),
                          clim=self.volume.clim,
                          # label=str(self.bunit),
                          # clim=self.volume.clim,
                          cmap="hsl",
                          border_width=0,
                          border_color="#404040")

            # self.histogram(data.ravel())

            self.view.add(self.axis)

            self.freeze()

        except ValueError as e:
            t = e
            print
            t

    def create_cube(self, shape):
        """ Generate vertices & indices for a filled and outlined cube

        Returns
        -------
        vertices : array
            Array of vertices suitable for use as a VertexBuffer.
        filled : array
            Indices to use to produce a filled cube.
        outline : array
            Indices to use to produce an outline of the cube.
        """
        vtype = [('position', np.float32, 3),
                 ('texcoord', np.float32, 2),
                 ('normal', np.float32, 3),
                 ('color', np.float32, 4)]
        itype = np.uint32

        # Vertices positions
        x0, x1 = -0.5, shape[2] - 0.5
        y0, y1 = -0.5, shape[1] - 0.5
        z0, z1 = -0.5, shape[0] - 0.5

        p = np.array([[x0, y0, z0],
                      [x1, y0, z0],
                      [x0, y1, z0],
                      [x1, y1, z0],
                      [x0, y0, z1],
                      [x1, y0, z1],
                      [x0, y1, z1],
                      [x1, y1, z1]])

        # Face Normals
        n = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0],
                      [-1, 0, 1], [0, -1, 0], [0, 0, -1]])

        # Vertice colors
        c = np.array([[1, 1, 1, 1], [0, 1, 1, 1], [0, 0, 1, 1], [1, 0, 1, 1],
                      [1, 0, 0, 1], [1, 1, 0, 1], [0, 1, 0, 1], [0, 0, 0, 1]])

        # Texture coords
        t = np.array([[0, 0], [0, 1], [1, 1], [1, 0]])

        faces_p = [0, 1, 2, 3,
                   0, 3, 4, 5,
                   0, 5, 6, 1,
                   1, 6, 7, 2,
                   7, 4, 3, 2,
                   4, 7, 6, 5]
        faces_c = [0, 1, 2, 3,
                   0, 3, 4, 5,
                   0, 5, 6, 1,
                   1, 6, 7, 2,
                   7, 4, 3, 2,
                   4, 7, 6, 5]
        faces_n = [0, 0, 0, 0,
                   1, 1, 1, 1,
                   2, 2, 2, 2,
                   3, 3, 3, 3,
                   4, 4, 4, 4,
                   5, 5, 5, 5]
        faces_t = [0, 1, 2, 3,
                   0, 1, 2, 3,
                   0, 1, 2, 3,
                   3, 2, 1, 0,
                   0, 1, 2, 3,
                   0, 1, 2, 3]

        vertices = np.zeros(24, vtype)
        vertices['position'] = p[faces_p]
        vertices['normal'] = n[faces_n]
        vertices['color'] = c[faces_c]
        vertices['texcoord'] = t[faces_t]

        filled = np.resize(
            np.array([0, 1, 2, 0, 2, 3], dtype=itype), 6 * (2 * 3))
        filled += np.repeat(4 * np.arange(6, dtype=itype), 6)
        filled = filled.reshape((len(filled) // 3, 3))

        outline = np.resize(
            np.array([0, 1, 1, 3, 3, 2, 2, 0], dtype=itype), 6 * (2 * 4))
        # outline += np.repeat(4 * np.arange(6, dtype=itype), 8)

        outline = np.array([0, 1, 0, 2, 2, 3, 1, 3,
                            0, 6, 1, 7, 2, 10, 3, 14,
                            6, 7, 6, 10, 10, 14, 7, 14])  # 3,11, ])#2,9, 3,10 ])

        return vertices, filled, outline

    # def set_data(self, data, vr_method, cmap, clim_min, clim_max):
    def set_data(self, vr_method, cmap, combo_color_method, interpolation_method):
        self.volume.method = vr_method
        self.volume.cmap = cmap
        self.volume.color_method = combo_color_method
        self.volume.interpolation = interpolation_method

        if (self.volume.color_method == 0):
            label = str(self.bunit)
            clim = self.volume.clim
        else:
            label = str(self.vel_type)
            clim = self.clim_vel

        # print ('clim', clim)

        self.cbar.clim = clim
        self.cbar.label = label
        self.cbar.cmap = cmap

        # self.volume.set_data(data, [clim_min, clim_max])

    def set_threshold(self, threshold):
        try:
            threshold = float(threshold)
        except:
            print("Threshold: need to be a float")
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
        self.volume.color_scale = color_scale

    def set_filter_size(self, filter_size):
        self.volume.filter_size = filter_size

    def set_gaussian_filter(self, use_gaussian_filter, gaussian_filter_size):
        self.volume.use_gaussian_filter = use_gaussian_filter
        self.volume.gaussian_filter_size = gaussian_filter_size

    def set_low_discard_filter(self, low_discard_filter_value):
        self.volume.low_discard_filter_value = low_discard_filter_value

    def set_density_factor(self, density_factor):
        # print (density_factor)
        self.volume.density_factor = density_factor

    def set_camera(self, cam, fov):
        if cam == 'PerspectiveCamera':
            self.view.camera = scene.cameras.PerspectiveCamera(parent=self.view.scene,
                                                               fov=float(fov),
                                                               name='PerspectiveCamera',
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

    def set_scaling(self, scalex, scaley, scalez):
        # TODO: get translation right to stay centered.
        self.axis.transform = self.volume.transform = scene.STTransform(scale=(scalex, scaley, scalez),
                                                                        translate=(
                                                                        -scalex ** 2, -scaley ** 2, -scalez ** 2))

    def set_transform(self, x, y, z):
        self.unfreeze()
        self.axis.transform = self.volume.transform = scene.STTransform(translate=(x, y, z))
        self.freeze()


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    appQt = QtGui.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    appQt.exec_()