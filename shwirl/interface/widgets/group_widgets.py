from vispy.color import get_colormaps
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QLabel, QTextEdit, QGridLayout, QVBoxLayout, QPushButton,
    QComboBox, QCheckBox, QSlider, QLineEdit, QFileDialog, QGroupBox
)
import numpy as np
from astropy.io import fits

class GroupWidgets(QWidget):
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
        """Initialise the GroupWidgets class

        Instanciate the widget's components for a given `type` of widget.

        Parameters
        -----------
            type : str
                Type of widget (one of MainWindow.widget_types).

            parent : class
                Parent class.
        """
        super(GroupWidgets, self).__init__(parent)

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
            self.tf_method = ['mip', 'lmip', 'avip', 'iso']
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
            self.color_method = ['Moment 0', 'Moment 1', 'rgb_cube']
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
            self.slider_filter_size.setMaximum(10)
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

    def showLoadFitsDialog(self):
        """Show the dialog window to load a fits file.
        """
        filename = QFileDialog.getOpenFileName(self,
                                               'Open file',
                                               filter='FITS Images (*.fits, *.FITS)')

        if filename[0] != "":
            # Load file
            # print(filename)
            self.loaded_cube = fits.open(filename[0])

            try:
                self.vol_min = self.loaded_cube[0].header["DATAMIN"]
                self.vol_max = self.loaded_cube[0].header["DATAMAX"]
            except:
                # print("Warning: DATAMIN and DATAMAX not present in header; evaluating min and max")
                if self.loaded_cube[0].header["NAXIS"] == 3:
                    self.vol_min = np.nanmin(self.loaded_cube[0].data)
                    self.vol_max = np.nanmax(self.loaded_cube[0].data)
                else:
                    self.vol_min = np.nanmin(self.loaded_cube[0].data[0])
                    self.vol_max = np.nanmax(self.loaded_cube[0].data[0])

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

    # def update_clim(self):
    #     self.signal_file_loaded.emit()

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

    # def update_log_scale(self):
    #     self.signal_log_scale_changed.emit()

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
        # if self.combo_filter_type.currentText() == 'Rescale':
        #     for widget in self.widgets_dict['high_discard_filter']:
        #         widget.show()
        # else:
        #     for widget in self.widgets_dict['high_discard_filter']:
        #         widget.hide()
        #
        #     self.reset_discard_filters_values()

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