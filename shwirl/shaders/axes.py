# Adapted from glue-vispy-viewer (https://github.com/glue-viz/glue-vispy-viewers)
# TODO: Need to include license...

import numpy as np
from vispy import scene

# from vispy.geometry import create_cube


# Per-display-axis colours for the orientation triad (x, y, z), matching the
# order used by ``create_cube``: shape[2]=x, shape[1]=y, shape[0]=z.
TRIAD_COLORS = ((1.0, 0.35, 0.35, 1.0),   # x  – warm red
                (0.4, 0.9, 0.4, 1.0),     # y  – green
                (0.45, 0.6, 1.0, 1.0))    # z  – blue


class AxesVisual3D:
    """Minimal, readable 3D annotation for the data cube.

    Rather than dense per-edge WCS ticks (hard to read and overlapping in 3D),
    this draws:

    - the cube outline;
    - a small **orientation triad** at the near corner (three short coloured
      arrows + short axis names) that rotates with the data, so the viewer can
      always tell which way each axis runs.

    Numeric axis *ranges* are shown separately by a screen-fixed info panel
    (built in ``shwirl.shwirl``), keeping the 3D scene uncluttered.
    """

    def __init__(self, parent, data_shape, view=None, transform=None,
                 axis_names=("X", "Y", "Z"), **kwargs):

        self.view = view
        self._names = list(axis_names)
        self._text_color = kwargs.get("text_color", "white")
        self._axis_color = kwargs.get("axis_color", "white")
        font_size = kwargs.get("axis_font_size", 14)

        # Cube extents in data coordinates (x=shape[2], y=shape[1], z=shape[0]).
        self._ext = (data_shape[2], data_shape[1], data_shape[0])
        scene_parent = self.view.scene

        # --- Cube outline -----------------------------------------------------
        vertices, _filled, outline_indices = self.create_cube(data_shape)
        self.axis = scene.visuals.Mesh(vertices['position'], outline_indices,
                                       parent=scene_parent,
                                       color=self._axis_color, mode='lines')

        # --- Orientation triad ------------------------------------------------
        triad_pos, triad_col = self._triad_segments()
        self.triad = scene.visuals.Line(pos=triad_pos, color=triad_col,
                                        connect='segments', width=4,
                                        method='gl', parent=scene_parent)

        self.labels = scene.visuals.Text(text=self._names,
                                         pos=self._label_positions(),
                                         color=self._text_color,
                                         font_size=font_size, bold=True,
                                         parent=scene_parent)

        self.transform = transform

    # -- geometry ----------------------------------------------------------
    def _corner(self):
        """Near/min corner of the cube (data coordinates)."""
        return np.array([-0.5, -0.5, -0.5])

    def _arm(self):
        """Triad arm length: a fraction of the largest cube extent."""
        return 0.30 * max(self._ext)

    def _triad_segments(self):
        c = self._corner()
        arm = self._arm()
        dirs = np.eye(3) * arm
        pos = np.empty((6, 3), np.float32)
        col = np.empty((6, 4), np.float32)
        for i in range(3):
            pos[2 * i] = c
            pos[2 * i + 1] = c + dirs[i]
            col[2 * i] = col[2 * i + 1] = TRIAD_COLORS[i]
        return pos, col

    def _label_positions(self):
        c = self._corner()
        arm = self._arm()
        return np.array([c + [arm * 1.25, 0, 0],
                         c + [0, arm * 1.25, 0],
                         c + [0, 0, arm * 1.25]], np.float32)

    # -- public API (kept compatible with shwirl.shwirl usage) -------------
    @property
    def transform(self):
        return self.axis.transform

    @transform.setter
    def transform(self, transform):
        for v in (self.axis, self.triad, self.labels):
            v.transform = transform

    def _set_name(self, index, value):
        self._names[index] = str(value)
        self.labels.text = self._names

    @property
    def xlabel(self):
        return self._names[0]

    @xlabel.setter
    def xlabel(self, value):
        self._set_name(0, value)

    @property
    def ylabel(self):
        return self._names[1]

    @ylabel.setter
    def ylabel(self, value):
        self._set_name(1, value)

    @property
    def zlabel(self):
        return self._names[2]

    @zlabel.setter
    def zlabel(self, value):
        self._set_name(2, value)

    # Numeric ranges are shown by the screen-fixed info panel, so the lim
    # setters are accepted for API compatibility but intentionally inert.
    @property
    def xlim(self):
        return None

    @xlim.setter
    def xlim(self, value):
        pass

    @property
    def ylim(self):
        return None

    @ylim.setter
    def ylim(self, value):
        pass

    @property
    def zlim(self):
        return None

    @zlim.setter
    def zlim(self, value):
        pass

    @property
    def tick_color(self):
        return self._axis_color

    @tick_color.setter
    def tick_color(self, value):
        # No separate tick visuals any more; kept for API compatibility.
        pass

    @property
    def label_color(self):
        return self._text_color

    @label_color.setter
    def label_color(self, value):
        self._text_color = value
        self.labels.color = value

    @property
    def axis_color(self):
        return self._axis_color

    @axis_color.setter
    def axis_color(self, value):
        self._axis_color = value
        self.axis.color = value

    @property
    def parent(self):
        return self.axis.parent

    @parent.setter
    def parent(self, value):
        for v in (self.axis, self.triad, self.labels):
            v.parent = value

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
