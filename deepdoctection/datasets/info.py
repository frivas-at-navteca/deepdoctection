# -*- coding: utf-8 -*-
# File: info.py

# Copyright 2021 Dr. Janis Meyer. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Module for storing dataset info (e.g. general meta data or categories)
"""

from dataclasses import dataclass, field
from itertools import chain
from typing import Dict, List, Optional, Union

from ..utils.logger import logger

__all__ = ["DatasetInfo", "DatasetCategories"]


def _get_dict(l: List[str], name_as_key: bool, starts_with: int = 1) -> Dict[str, str]:
    """
    Converts a list into a dict, where keys/values are the list indices.

    :param l: A list of categories
    :param name_as_key: Whether to return the dict with category names as key (True)
    :param starts_with: index count start
    :return: A dictionary of list indices/list elements.
    """
    if name_as_key:
        return {v: str(k) for k, v in enumerate(l, starts_with)}
    return {str(k): v for k, v in enumerate(l, starts_with)}


@dataclass
class DatasetInfo:
    """
    DatasetInfo is a simple dataclass that stores some meta-data information about a dataset.

    :attr:`name`: Name of the dataset. Using the name you can retrieve the dataset from the
    :class:`registry.DatasetRegistry`.

    :attr:`description`: Short description of the dataset.

    :attr:`license`: License to the dataset.

    :attr:`url`: url, where the dataset can be downloaded from.

    :attr:`splits`: A dict of splits. The value must store the relative path, where the split can be found.
    """

    name: str
    description: str = field(default="")
    license: str = field(default="")
    url: Union[str, List[str]] = field(default="")
    splits: Dict[str, str] = field(default_factory=dict)

    def get_split(self, key: str) -> str:
        """
        Get the split directory by its key (if it exists).

        :param key: The key to a split (i.e. "train", "val", "test")
        :return: The local directory path to the split. An empty string if the key doesn't exist.
        """

        return self.splits.get(key, "")


@dataclass
class DatasetCategories:
    """
    Categories and their sub-categories are managed in this separate class. Since categories can be filtered or
    sub-categories can be swapped with categories, the list of all categories must be adapted at the same time
    after replacement/filtering. DatasetCategories manages these transformations. The class is also responsible
    for the index/category name relationship and guarantees that a sequence of natural numbers for the categories
    is always returned as the category-id even after replacing and/or filtering.

    :attr:`init_categories`: A list of category names. The list must include all categories that can occur within the
    annotations.

    :attr:`init_sub_categories`: A dict of categories/sub-categories. Each sub-category that can appear in the
    annotations in combination with a category must be listed.

    **Example:**

        An annotation file hast the category/sub-category combinations for three datapoints: (cat1,s1),(cat1,s2),
        (cat2,s2). You must list :attr:`init_categories`, :attr:`init_sub_categories` as follows:

        .. code-block:: python

            init_categories = [cat1,cat2]
            init_sub_categories = {cat1: [s1,s2],cat2: [s2]}

    Use :meth:`filter_categories` or :meth:`set_cat_to_sub_cat` to filter or swap categories with sub-categories.
    """

    init_categories: List[str] = field(default_factory=list)
    init_sub_categories: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._categories_update = self.init_categories
        self._cat_to_sub_cat: Optional[Dict[str, str]] = None

    def get_categories(
        self, as_dict: bool = True, name_as_key: bool = False, init: bool = False, filtered: bool = False
    ) -> Union[Dict[str, str], List[str]]:
        """
        Get categories of a dataset. The returned value also respects modifications of the inventory like filtered
        categories of replaced categories with sub categories. However, you must correctly pass arguments to return the
        state you want.

        :param as_dict: Will pass a dict if set to 'True' otherwise a list.
        :param name_as_key: Categories are stored as key/value pair in a dict with integers as keys. name_as_key set to
                            "False" will swap keys and values.
        :param init: If set to "True" it will return the list/dict of categories as initially provided. Manipulations
                     due to replacing/filtering will not be regarded.
        :param filtered: If set to "True" will return an unfiltered list of all categories. If a replacing has been
                         invoked selected sub categories will be returned.
        :return: A dict of index/category names (or the other way around) or a list of category names.
        """
        if init:
            if as_dict:
                return _get_dict(self.init_categories, name_as_key)
            return self.init_categories
        if filtered:
            if as_dict:
                if hasattr(self, "_categories_filter_update"):
                    return _get_dict(self._categories_filter_update, name_as_key)
                return _get_dict(self._categories_update, name_as_key)
            if hasattr(self, "_categories_filter_update"):
                return self._categories_filter_update
            return self._categories_update
        if as_dict:
            return _get_dict(self._categories_update, name_as_key)
        return self._categories_update

    def get_sub_categories(
        self, categories: Optional[Union[str, List[str]]] = None
    ) -> Dict[str, Union[str, List[str]]]:
        """
        Returns a dict of list with a category name and their sub categories.

        :param categories: A single category or list of category names
        :return: Dict with all selected categories.
        """
        if isinstance(categories, str):
            categories = [categories]
        if categories is None:
            categories = self.get_categories(as_dict=False, filtered=True)  # type: ignore
            if categories is None:
                categories = []

        sub_cat: Dict[str, Union[str, List[str]]] = {}
        for cat in categories:  # pylint: disable=R1702
            assert cat in self.get_categories(
                as_dict=False, filtered=True
            ), f"{cat} not in categories, maybe has been replaced with sub category"
            sub_cat_dict = self.init_sub_categories.get(cat)
            if sub_cat_dict is None:
                if self._cat_to_sub_cat:
                    for key, val in self._cat_to_sub_cat.items():
                        possible_sub_cats = self.init_sub_categories[key]
                        for pos in possible_sub_cats:
                            if pos == val:
                                sub_cat_dict_key = self.init_sub_categories[key]
                                sub_cat_list = sub_cat_dict_key.get(cat)
                                if sub_cat_list is None:
                                    sub_cat[cat] = []
                                else:
                                    sub_cat[cat] = sub_cat_list
            else:
                sub_cat[cat] = list(sub_cat_dict.keys())

        return sub_cat

    def set_cat_to_sub_cat(self, cat_to_sub_cat: Dict[str, str]) -> None:
        """
        Change category representation if sub-categories are available. Pass a dictionary of the main category
        and the requested sub-category. This will change the dictionary of categories and the category names
        and category ids of the image annotation in the dataflow. Using more than one sub category per category will
        not make sense.

        **Example:**

            .. code-block:: python

                  cat_to_sub_cat={cat1: sub_cat1}

            will replace cat1 with sub_cat1 as category. This will also be respected when returning datapoints.

        :param cat_to_sub_cat: A dict of pairs of category/sub-category. Note that the combination must be available
                               according to the initial settings.
        """

        logger.info("Will reset all previous updates")
        self._categories_update = self.init_categories
        categories = self.get_categories(name_as_key=True)
        cats_or_sub_cats = [
            self.init_sub_categories.get(cat, {cat: [cat]}).get(cat_to_sub_cat.get(cat, cat), [cat])
            for cat in categories
        ]
        self._cat_to_sub_cat = cat_to_sub_cat
        self._categories_update = list(chain(*cats_or_sub_cats))

    def filter_categories(self, categories: Union[str, List[str]]) -> None:
        """
        Filter categories of a dataset. This will keep all the categories chosen and remove all others.

        :param categories: A single category name or a list of category names.
        """
        if isinstance(categories, str):
            categories = [categories]
        self._categories_filter_update = [cat for cat in self._categories_update if cat in categories]

    @property
    def cat_to_sub_cat(self) -> Optional[Dict[str, str]]:
        """
        cat_to_sub_cat
        """
        return self._cat_to_sub_cat

    def is_cat_to_sub_cat(self) -> bool:
        """
        returns "True" if a category is replaced with sub categories
        """
        if self._cat_to_sub_cat is not None:
            return True
        return False

    def is_filtered(self) -> bool:
        """
        return "True" if categories are filtered
        """
        if hasattr(self, "_categories_filter_update"):
            return True
        return False


def get_merged_categories(*categories: DatasetCategories) -> DatasetCategories:
    """
    Given a set of DatasetCategories a DatasetCategories instance will be returned that summarize the category
    properties of merged dataset. This means it will save the union of all possible categories as its init categories.
    Regarding sub categories, only those will be accessible if and only if they are a sub category of a category for all
    merged datasets. E.g. if dataset A has category "foo" with sub category "foo":"bak" and dataset B has category "foo"
    as well but no sub category than the merged dataset will have no sub categories at all. Whereas in a similar setting
    dataset B has sub category "foo":"bak", then "bak" will be an optional sub category for the merged dataset as well.


    :param categories: A tuple/list of dataset categories
    :return: An instance of DatasetCategories to be used as DatasetCategories for merged datasets
    """

    # working with lists is not possible as the order of categories is important here
    init_categories = []
    for cat in categories:
        for label in cat.init_categories:
            if label not in init_categories:
                init_categories.append(label)

    # select categories with sub categories. Only categories that appear in this list can be candidates for having
    # sub categories in the merged dataset
    intersect_sub_cat_keys = set(categories[0].init_sub_categories.keys()).intersection(*[cat.init_sub_categories.keys()
                                                                                          for cat in categories[1:]])
    intersect_init_sub_cat = dict()
    for key in intersect_sub_cat_keys:
        # select all sub categories from all datasets for a given key
        sub_cat_per_key = [cat.init_sub_categories[key] for cat in categories]
        # select only sub categories that appear in all datasets
        intersect_sub_cat_per_key = set(sub_cat_per_key[0].keys()).intersection(*[sub_cats.keys()
                                                                                   for sub_cats in sub_cat_per_key[1:]])
        # form a set of possible sub category values. To get a list of all values from all dataset, take the union
        intersect_init_sub_cat_values = dict()
        for sub_cat_key in intersect_sub_cat_per_key:
            val = set()
            for cat in categories:
                val.update(cat.init_sub_categories[key][sub_cat_key])
            intersect_init_sub_cat_values[sub_cat_key]=list(val)
        intersect_init_sub_cat[key]=intersect_init_sub_cat_values

    # Next, build the DatasetCategories instance.
    categories_update = list(set().union(*[cat.get_categories(as_dict=False) for cat in categories]))
    categories_filtered =  list(set().union(*[cat.get_categories(as_dict=False,filtered=True) for cat in categories]))
    merged_categories = DatasetCategories(init_categories=init_categories,init_sub_categories=intersect_init_sub_cat)
    merged_categories._categories_update = categories_update
    setattr(merged_categories,"_categories_filter_update",categories_filtered)
    return merged_categories
