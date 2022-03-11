# -*- coding: utf-8 -*-
# File: model_mrcnn.py

# Copyright (c) Tensorpack Contributors
# Licensed under the Apache License, Version 2.0 (the "License")

"""
This file is modified from
https://github.com/tensorpack/tensorpack/blob/master/examples/FasterRCNN/modeling/model_mrcnn.py
"""

# pylint: disable=import-error
import tensorflow as tf
from tensorpack.models import Conv2D, Conv2DTranspose, layer_register
from tensorpack.tfutils.argscope import argscope
from tensorpack.tfutils.common import get_tf_version_tuple
from tensorpack.tfutils.scope_utils import under_name_scope
from tensorpack.tfutils.summary import add_moving_summary

from .backbone import GroupNorm

# pylint: enable=import-error


@under_name_scope()
def maskrcnn_loss(mask_logits, fg_labels, fg_target_masks):
    """
    :param mask_logits: #fg x #category xhxw
    :param fg_labels: #fg, in 1~#class, int64
    :param fg_target_masks: #fgxhxw, float32
    """

    if get_tf_version_tuple() >= (1, 14):
        mask_logits = tf.gather(mask_logits, tf.reshape(fg_labels - 1, [-1, 1]), batch_dims=1)  # pylint: disable =E1120
        mask_logits = tf.squeeze(mask_logits, axis=1)
    else:
        indices = tf.stack([tf.range(tf.size(fg_labels, out_type=tf.int64)), fg_labels - 1], axis=1)  # #fgx2
        mask_logits = tf.gather_nd(mask_logits, indices)  # #fg x h x w

    mask_probs = tf.sigmoid(mask_logits)

    # add some training visualizations to tensorboard
    with tf.name_scope("mask_viz"):
        viz = tf.concat([fg_target_masks, mask_probs], axis=1)  # pylint: disable =E1123, E1120
        viz = tf.expand_dims(viz, 3)
        viz = tf.cast(viz * 255, tf.uint8, name="viz")
        tf.summary.image("mask_truth|pred", viz, max_outputs=10)

    loss = tf.nn.sigmoid_cross_entropy_with_logits(labels=fg_target_masks, logits=mask_logits)
    loss = tf.reduce_mean(loss, name="maskrcnn_loss")

    pred_label = mask_probs > 0.5
    truth_label = fg_target_masks > 0.5
    accuracy = tf.reduce_mean(tf.cast(tf.equal(pred_label, truth_label), tf.float32), name="accuracy")
    pos_accuracy = tf.logical_and(tf.equal(pred_label, truth_label), tf.equal(truth_label, True))
    pos_accuracy = tf.reduce_mean(tf.cast(pos_accuracy, tf.float32), name="pos_accuracy")
    fg_pixel_ratio = tf.reduce_mean(tf.cast(truth_label, tf.float32), name="fg_pixel_ratio")

    add_moving_summary(loss, accuracy, fg_pixel_ratio, pos_accuracy)
    return loss


@layer_register(log_shape=True)
def maskrcnn_upXconv_head(feature, num_category, num_convs, norm=None, **kwargs):  # pylint: disable =C0103
    """
    :param feature: size is 7 in C4 models and 14 in FPN models. (NxCx s x s)
    :param num_category: number of categories
    :param num_convs: number of convolution layers
    :param norm: either None or 'GN' (str or None)

    :return mask_logits (N x num_category x 2s x 2s):
    """

    cfg = kwargs["cfg"]
    assert norm in [None, "GN"], norm
    l = feature
    with argscope(
        [Conv2D, Conv2DTranspose],
        data_format="channels_first",
        kernel_initializer=tf.variance_scaling_initializer(  # pylint: disable =E1101
            scale=2.0,
            mode="fan_out",
            distribution="untruncated_normal" if get_tf_version_tuple() >= (1, 12) else "normal",
        ),
    ):
        # c2's MSRAFill is fan_out
        for k in range(num_convs):
            l = Conv2D(f"fcn{k}", l, cfg.MRCNN.HEAD_DIM, 3, activation=tf.nn.relu)
            if norm is not None:
                l = GroupNorm(f"gn{k}", l)
        l = Conv2DTranspose(  # pylint: disable =E1124
            "deconv", l, cfg.MRCNN.HEAD_DIM, 2, strides=2, activation=tf.nn.relu
        )
        l = Conv2D("conv", l, num_category, 1, kernel_initializer=tf.random_normal_initializer(stddev=0.001))
    return l


def maskrcnn_up4conv_head(*args, **kwargs):
    """
    maskrcnn four up-sampled convolutional layers
    """
    return maskrcnn_upXconv_head(*args, num_convs=4, **kwargs)


def maskrcnn_up4conv_gn_head(*args, **kwargs):
    """
    maskrcnn four up-sampled group normalized convolutional layers
    """
    return maskrcnn_upXconv_head(*args, num_convs=4, norm="GN", **kwargs)


def unpackbits_masks(masks):
    """
    :param masks: (Tensor) uint8 Tensor of shape N, H, W. The last dimension is packed bits.

    :return: (Tensor) bool Tensor of shape N, H, 8*W.

    This is a reverse operation of `np.packbits`
    """

    assert masks.dtype == tf.uint8, masks
    bits = tf.constant((128, 64, 32, 16, 8, 4, 2, 1), dtype=tf.uint8)
    unpacked = tf.bitwise.bitwise_and(tf.expand_dims(masks, -1), bits) > 0
    unpacked = tf.reshape(
        unpacked, tf.concat([tf.shape(masks)[:-1], [8 * tf.shape(masks)[-1]]], axis=0)  # pylint: disable =E1123,E1120
    )
    return unpacked
