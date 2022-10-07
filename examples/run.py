# -*- coding: utf-8 -*-
"""
Author       : lixiang @ firebolt
Created Time : 2022-09-06 16:52:41
Description  : Release version of ini package testing
"""
import ini
print(ini.__file__)

from ini import Ini
from main import main

main(Ini)
