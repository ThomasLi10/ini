# -*- coding: utf-8 -*-
"""
# Author: lixiang
# Created Time : Sun 22 Mar 2020 09:00:39 AM CST
# File Name: setup.py
# Description:
"""

from distutils.core import setup
from Cython.Build import cythonize

py_list = [
        'ini.py',
]

kwargs={'build_dir':'./.tmp/',
        'compiler_directives':{'language_level':'3'},
        }
setup(ext_modules = cythonize(py_list,**kwargs))

