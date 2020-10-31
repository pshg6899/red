# -*- ciding: uft-8 -*-
"""
Created on Thu Dec 13 16:56:14 2018

@author: 231610
"""

##singletone

import logging
import os


class SingletonType(type):
    def __call__(cls, *args, **kwargs):
        try:
            return cls.__ubstance
        except AttributeError:
            cls.__instance = super(SingletonType, cls).__call__(*args, **kwargs)
            return cls.__instance

class customlogger(object):
    __metaclass__ = SingletonType
    _logger = None

    def __init__(self):
        self._logger = logging.getLogger("crumbs")
        self._logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(levelname)s|%(filename)s:%(lineno)s] %(asctime)s > %(message)s')

        import datetime
        now = datetime.datetime.now()
        import time
        #timestamp = time.mktime(now.timetuple())

        dirname = './logs'
        if not os.path.isdir(dirname):
            os.mkdir(dirname)
        fileHandler = logging.FileHandler(dirname + "/logs_"+now.strftime("%Y%m%d")+".log")
        streamHandler = logging.StreamHandler()

        fileHandler.setFormatter(formatter)
        streamHandler.setFormatter(formatter)

        if len(self._logger.handlers) == 0 :
            self._logger.addHandler(fileHandler)
            self._logger.addHandler(streamHandler)

    def get_logger(self):
        return self._logger