# -*- coding: utf-8 -*-
# File: file_utils.py
# Copyright (c)  The HuggingFace Team, the AllenNLP library authors.
# Licensed under the Apache License, Version 2.0 (the "License")


"""
Utilities for maintaining dependencies and dealing with external library packages. Parts of this file is adapted from
https://github.com/huggingface/transformers/blob/master/src/transformers/file_utils.py
"""

from shutil import which

import importlib.util
import importlib_metadata  # type: ignore

from packaging import version

from .detection_types import Requirement


# Tensorflow and Tensorpack dependencies
_TF_AVAILABLE = False

try:
    _TF_AVAILABLE = importlib.util.find_spec("tensorflow") is not None
except ValueError:
    pass

_TF_ERR_MSG = "Tensorflow >=2.4.1 must be installed: https://www.tensorflow.org/install/gpu"


def tf_available() -> bool:
    """
    Returns True if TF is installed
    """
    return bool(_TF_AVAILABLE)


def get_tensorflow_requirement() -> Requirement:
    """
    Returns Tensorflow requirement
    """

    tf_requirement_satisfied = False
    if tf_available():
        candidates = (
            "tensorflow",
            "tensorflow-cpu",
            "tensorflow-gpu",
            "tf-nightly",
            "tf-nightly-cpu",
            "tf-nightly-gpu",
            "intel-tensorflow",
            "intel-tensorflow-avx512",
            "tensorflow-rocm",
            "tensorflow-macos",
        )
        tf_version = "0.0"
        for pkg in candidates:
            try:
                tf_version = importlib_metadata.version(pkg)
                break
            except importlib_metadata.PackageNotFoundError:
                pass
        _tf_version_available = tf_version != "0.0"
        if _tf_version_available:
            if version.parse(tf_version) < version.parse("2.4.1"):
                pass
            else:
                tf_requirement_satisfied = True

    return "tensorflow", tf_requirement_satisfied, _TF_ERR_MSG


_TP_AVAILABLE = importlib.util.find_spec("tensorpack") is not None
_TP_ERR_MSG = (
    "Tensorflow models all use the Tensorpack modeling API. Therefore, Tensorpack must be installed: "
    ">>make install-dd-tf"
)


def tensorpack_available() -> bool:
    """
    Returns True if Tensorpack is installed
    """
    return bool(_TP_AVAILABLE)


def get_tensorpack_requirement() -> Requirement:
    """
    Returns Tensorpack requirement
    """
    return "tensorpack", tensorpack_available(), _TP_ERR_MSG


# Pytorch related dependencies
_PYTORCH_AVAILABLE = importlib.util.find_spec("torch") is not None
_PYTORCH_ERR_MSG = "Pytorch must be installed: https://pytorch.org/get-started/locally/#linux-pip"


def pytorch_available() -> bool:
    """
    Returns True if Pytorch is installed
    """
    return bool(_PYTORCH_AVAILABLE)


def get_pytorch_requirement() -> Requirement:
    """
    Returns HF Pytorch requirement
    """
    return "torch", pytorch_available(), _PYTORCH_ERR_MSG


# Transformers
_TRANSFORMERS_AVAILABLE = importlib.util.find_spec("transformers") is not None
_TRANSFORMERS_ERR_MSG = "Transformers must be installed: >>install-dd-pt"


def transformers_available() -> bool:
    """
    Returns True if HF Transformers is installed
    """
    return bool(_TRANSFORMERS_AVAILABLE)


def get_transformers_requirement() -> Requirement:
    """
    Returns HF Transformers requirement
    """
    return "transformers", transformers_available(), _TRANSFORMERS_ERR_MSG


# Detectron2 related requirements
_DETECTRON2_AVAILABLE = importlib.util.find_spec("detectron2") is not None
_DETECTRON2_ERR_MSG = "Detectron2 must be installed: >>install-dd-pt"


def detectron2_available() -> bool:
    """
    Returns True if Detectron2 is installed
    """
    return bool(_DETECTRON2_AVAILABLE)


def get_detectron2_requirement() -> Requirement:
    """
    Returns Detectron2 requirement
    """
    return "detectron2", detectron2_available(), _DETECTRON2_ERR_MSG


# Tesseract related dependencies
_PYTESS_AVAILABLE = importlib.util.find_spec("pytesseract") is not None
_PYTESS_ERR_MSG = "Pytesseract must be installed: https://pypi.org/project/pytesseract/"

_TESS_AVAILABLE = which("tesseract") is not None
_TESS_ERR_MSG = "Tesseract >=4.0 must be installed: https://tesseract-ocr.github.io/tessdoc/Installation.html"


def py_tesseract_available() -> bool:
    """
    Returns True if Pytesseract is installed
    """
    return bool(_PYTESS_AVAILABLE)


def get_py_tesseract_requirement() -> Requirement:
    """
    Returns Pytesseract requirement
    """
    return "pytesseract", py_tesseract_available(), _PYTESS_ERR_MSG


def tesseract_available() -> bool:
    """
    Returns True if Tesseract is installed
    """
    return bool(_TESS_AVAILABLE)


def get_tesseract_requirement() -> Requirement:
    """
    Returns Tesseract requirement
    """
    return "tesseract", tesseract_available(), _TESS_ERR_MSG


# Textract related dependencies
_BOTO3_AVAILABLE = importlib.util.find_spec("boto3") is not None
_BOTO3_ERR_MSG = "Boto3 must be installed: >>make install-aws-dependencies"

_AWS_CLI_AVAILABLE = which("aws") is not None
_AWS_ERR_MSG = "AWS CLI must be installed https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"


def boto3_available() -> bool:
    """
    Returns True if Boto3 is installed
    """

    return bool(_BOTO3_AVAILABLE)


def get_boto3_requirement() -> Requirement:
    """
    Return Boto3 requirement
    """
    return "boto3", boto3_available(), _BOTO3_ERR_MSG


def aws_available() -> bool:
    """
    Returns True if AWS CLI is installed
    """
    return bool(_AWS_CLI_AVAILABLE)


def get_aws_requirement() -> Requirement:
    """
    Return AWS CLI requirement
    """
    return "aws", aws_available(), _AWS_ERR_MSG
