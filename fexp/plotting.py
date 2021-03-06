"""
Copyright (c) Nikita Moriakov and Jonas Teuwen

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""
import matplotlib
matplotlib.use('agg')

import matplotlib.pyplot as plt
import skimage.measure
from matplotlib.ticker import NullLocator
import matplotlib.patches as mpatches
import numpy.ma as ma
import io
import PIL


def plot_2d(image, mask=None, bboxes=None, points=None,
            overlay=None, linewidth=2, mask_color='r', bbox_color='b', points_color='g',
            overlay_cmap='jet', overlay_threshold=0.1, overlay_alpha=0.1):

    """
    Plot image with contours and point annotations. Contours are automatically extracted from masks.

    Parameters
    ----------
    image : ndarray
        Image data of shape N x M x num channels.
    mask : ndarray
        Mask data of shape N x M.
    bboxes : tuple
        Bounding boxes to overlay. In the form of [[x, y, h, w], ...].
    points : ndarray
        ndarray of shape (num points, 2).
    overlay : ndarray
        Heatmap of data.
    linewidth : int
        Width of plotted lines.
    mask_color : str
        Matplotlib supported color for the masks.
    bbox_color : str
        Matplotlib supported color for the bounding boxes.
    points_color : str
        Matplotlib supported color for the points.
    overlay_cmap : str
    overlay_threshold : float
        Value below which overlay should not be displayed.
    overlay_alpha : float
        Overlay alpha

    Examples
    --------
    Can be used in Tensorboard, for instance as follows:

    >>> plot_overlay = torch.from_numpy(np.array(plot_2d(image_arr, mask=masks_arr)))
    >>> writer.add_image('train/overlay', plot_overlay, epoch, dataformats='HWC')

    Returns
    -------
    PIL Image

    """
    dpi = 100
    width = image.shape[1]
    height = image.shape[0]
    figsize = width / float(dpi), height / float(dpi)

    fig, ax = plt.subplots(1, figsize=figsize)
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)

    cmap = None
    if image.ndim == 3:
        if image.shape[-1] == 1:
            image = image[..., 0]
        elif image.shape[0] == 1:
            image = image[0, ...]

    if image.ndim == 2:
        cmap = 'gray'

    ax.imshow(image, cmap=cmap, aspect='equal', extent=(0, width, height, 0))
    ax.set_adjustable('datalim')

    if mask is not None:
        add_2d_contours(mask, ax, linewidth, mask_color)

    if bboxes is not None:
        for bbox in bboxes:
            add_2d_bbox(bbox, ax, linewidth, bbox_color)

    if overlay is not None:
        add_2d_overlay(overlay, ax, threshold=overlay_threshold, cmap=overlay_cmap, alpha=overlay_alpha)

    if points is not None:
        ax.plot(points[:, 1], points[:, 0], points_color + '.', markersize=2, alpha=1)

    fig.gca().set_axis_off()
    fig.gca().xaxis.set_major_locator(NullLocator())
    fig.gca().yaxis.set_major_locator(NullLocator())

    buffer = io.BytesIO()

    fig.savefig(buffer, pad_inches=0, dpi=dpi)
    buffer.seek(0)
    plt.close()

    pil_image = PIL.Image.open(buffer)

    return pil_image


def add_2d_bbox(bbox, ax, linewidth=0.5, color='b'):
    """Add bounding box to the image.

    Parameters
    ----------
    bbox : tuple
        Tuple of the form (row, col, height, width).
    axis : axis object
    linewidth : float
        thickness of the overlay lines
    color : str
        matplotlib supported color string for contour overlay.

    """
    rect = mpatches.Rectangle(bbox[:2][::-1], bbox[3], bbox[2],
                              fill=False, edgecolor=color, linewidth=linewidth)
    ax.add_patch(rect)


def add_2d_contours(mask, axes, linewidth=0.5, color='r'):
    """Plot the contours around the `1`'s in the mask

    Parameters
    ----------
    mask : ndarray
        2D binary array.
    axis : axis object
        matplotlib axis object.
    linewidth : float
        thickness of the overlay lines.
    color : str
        matplotlib supported color string for contour overlay.
    """
    contours = skimage.measure.find_contours(mask, 0.5)

    for contour in contours:
        axes.plot(*contour[:, [1, 0]].T, color=color, linewidth=linewidth)


def add_2d_overlay(overlay, ax, threshold=0.1, cmap='jet', alpha=0.1):
    """Adds an overlay of the probability map and predicted regions

    overlay : ndarray
    ax : axis object
       matplotlib axis object
    linewidth : float
       thickness of the overlay lines;
    threshold : float
    cmap : str
       matplotlib supported cmap.
    alpha : float
       alpha values for the overlay.
    """
    if threshold:
        overlay = ma.masked_where(overlay < threshold, overlay)

    ax.imshow(overlay, cmap=cmap, alpha=alpha)