# Adapted from glue-vispy-viewer (https://github.com/glue-viz/glue-vispy-viewers)
# TODO: Need to include license...

from ..extern.vispy import scene
# from ..extern.vispy.geometry import create_cube
from ..extern.vispy.visuals.transforms import STTransform, ChainTransform
import numpy as np

class AxesVisual3D(object):

    def __init__(self, parent, data_shape, view=None, transform=None, tick_label_margin=40,
                 axis_label_margin=200, **kwargs):

        self.view = view

        # Add a 3D cube to show us the unit cube. The 1.001 factor is to make
        # sure that the grid lines are not 'hidden' by volume renderings on the
        # front side due to numerical precision.
        # vertices, filled_indices, outline_indices = create_cube()
        vertices, filled_indices, outline_indices = self.create_cube(data_shape)
        self.axis = scene.visuals.Mesh(vertices['position'],
                                       outline_indices, parent=self.view.scene,
                                       color=kwargs['axis_color'], mode='lines')

        self.axis.transform = transform

        self.xax = scene.visuals.Axis(pos=[[0, 0],
                                           [data_shape[2], 0]],
                                      tick_direction=(0, -1),
                                      parent=parent,
                                      axis_label='X',
                                      anchors=['center', 'middle'],
                                      tick_label_margin=tick_label_margin * data_shape[2],
                                      axis_label_margin=axis_label_margin * data_shape[2],
                                      **kwargs)

        self.yax = scene.visuals.Axis(pos=[[0, 0],
                                           [0, data_shape[1]]],
                                      tick_direction=(1, 0),
                                      parent=parent,
                                      axis_label='Y',
                                      anchors=['center', 'middle'],
                                      tick_label_margin=-tick_label_margin * data_shape[1],
                                      axis_label_margin=-axis_label_margin * data_shape[1],
                                      **kwargs)

        self.zax = scene.visuals.Axis(pos=[[0, 0],
                                           [0, data_shape[0]]],
                                      tick_direction=(-1, 0),
                                      parent=parent,
                                      axis_label='Z',
                                      tick_label_margin=tick_label_margin * data_shape[0],
                                      axis_label_margin=axis_label_margin * data_shape[0],
                                      anchors=['center', 'middle'], **kwargs)

        self.xtr = STTransform()
        self.xtr = self.xtr.as_matrix()
        self.xtr.rotate(45, (1, 0, 0))
        self.xtr.translate((0, -1.02, -1.02))

        self.ytr = STTransform()
        self.ytr = self.ytr.as_matrix()
        self.ytr.rotate(135, (0, 1, 0))
        self.ytr.translate((1.02, 0, 1.02))

        self.ztr = STTransform()
        self.ztr = self.ztr.as_matrix()
        self.ztr.rotate(45, (0, 1, 0))
        self.ztr.rotate(90, (1, 0, 0))
        self.ztr.translate((-1.02, -1.02, 0.))

        self.xax.transform = ChainTransform(transform, self.xtr)
        self.yax.transform = ChainTransform(transform, self.ytr)
        self.zax.transform = ChainTransform(transform, self.ztr)

    @property
    def transform(self):
        return self.axis.transform

    @transform.setter
    def transform(self, transform):
        self.axis.transform = transform
        self.xax.transform = ChainTransform(transform, self.xtr)
        self.yax.transform = ChainTransform(transform, self.ytr)
        self.zax.transform = ChainTransform(transform, self.ztr)

    @property
    def tick_color(self):
        return self.xax.tick_color

    @tick_color.setter
    def tick_color(self, value):
        self.xax.tick_color = value
        self.yax.tick_color = value
        self.zax.tick_color = value

    @property
    def label_color(self):
        return self._label_color

    @label_color.setter
    def label_color(self, value):
        self.xax.label_color = value
        self.yax.label_color = value
        self.zax.label_color = value

    @property
    def axis_color(self):
        return self._axis_color

    @axis_color.setter
    def axis_color(self, value):
        self.axis.color = value

    @property
    def tick_font_size(self):
        return self.xax.tick_font_size

    @tick_font_size.setter
    def tick_font_size(self, value):
        self.xax.tick_font_size = value
        self.yax.tick_font_size = value
        self.zax.tick_font_size = value

    @property
    def axis_font_size(self):
        return self.xax.axis_font_size

    @axis_font_size.setter
    def axis_font_size(self, value):
        self.xax.axis_font_size = value
        self.yax.axis_font_size = value
        self.zax.axis_font_size = value

    @property
    def xlabel(self):
        return self.xax.axis_label

    @xlabel.setter
    def xlabel(self, value):
        self.xax.axis_label = value

    @property
    def ylabel(self):
        return self.yax.axis_label

    @ylabel.setter
    def ylabel(self, value):
        self.yax.axis_label = value

    @property
    def zlabel(self):
        return self.zax.axis_label

    @zlabel.setter
    def zlabel(self, value):
        self.zax.axis_label = value

    @property
    def xlim(self):
        return self.xax.domain

    @xlim.setter
    def xlim(self, value):
        self.xax.domain = value

    @property
    def ylim(self):
        return self.yax.domain

    @ylim.setter
    def ylim(self, value):
        self.yax.domain = value

    @property
    def zlim(self):
        return self.zax.domain

    @zlim.setter
    def zlim(self, value):
        self.zax.domain = value

    @property
    def parent(self):
        return self.axis.parent

    @parent.setter
    def parent(self, value):
        self.axis.parent = value
        self.xax.parent = value
        self.yax.parent = value
        self.zax.parent = value

    def create_cube(self, shape):
        """ Generate vertices & indices for a filled and outlined cube

        Parameters
        ----------
        shape : list
            List representing the shape of the numpy array.

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