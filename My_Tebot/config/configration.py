#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging.config
import os
import shutil
from typing import Dict, List
import yaml


class Config(object):
    def __init__(self) -> None:
        with open(fr"E:\WeChatFerry_proj\Telerobot\My_Tebot\config\config.yaml", "r", encoding="utf-8") as f:
            self.data = yaml.safe_load(f)
    @property
    def telegram(self):
        return self.data.get("telegram", {})
    @property
    def deepseek(self):
        return self.data.get("deepseek", {})
