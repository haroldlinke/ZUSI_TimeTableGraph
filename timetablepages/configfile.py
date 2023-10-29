#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ********************************************************************
# *        TimetableGraph
# *
# * provides a timetable graph for ZUSI schedules
# * Informatzion about ZUSI can be found here: https://www.zusi.de/
# *
# *
# * Version: 0.08
# * Author: Harold Linke
# * Date: February 5th, 2021
# * 
# * Copyright (C) 2021  Harold Linke
# *
# * Soucre code and Programm can be downloaded from GitHub
# * https://github.com/haroldlinke/ZUSI_TimeTableGraph
# *
# *
# * This program is free software: you can redistribute it and/or modify
# * it under the terms of the GNU Affero General Public License as
# * published by the Free Software Foundation, either version 3 of the
# * License, or (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU Affero General Public License for more details.
# *
# * You should have received a copy of the GNU Affero General Public License
# * along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ***************************************************************************


import os
import json
import logging

# ----------------------------------------------------------------
# Class ConfigFile
# ----------------------------------------------------------------
class ConfigFile():
    """ Configuration File """

    def __init__(self,default_config, filename,filedir=""):
        
        """ Config Constructor Method (__init__)

        Arguments:
            default_config
            filename

        Raises:
            None
        """
        self.default_config = default_config
        self.filepath = self.determine_filename(filename,filedir)
        self.readConfigData(self.filepath)
        
    def determine_filename(self, filename, filedir):
        if filedir == "":
            filedir = os.path.dirname(os.path.realpath(__file__))
        filepath1 = os.path.join(filedir, filename)
        return os.path.normpath(filepath1)        
            
    def readConfigData(self, filenamepath):
        try:
            jsondata={}
            file_not_found=True
            with open(filenamepath, "r", encoding='utf8') as read_file:
                file_not_found=False
                jsondata = json.load(read_file)
                logging.info ("Config File %s read",filenamepath)
        except ValueError as err:
            logging.error ("ERROR: JSON Error in Config File %s",filenamepath)
            logging.error(err)
        except:
            if file_not_found:
                logging.warning ("Warning: Config File %s not found",filenamepath)
            else:
                logging.error ("ERROR: JSON Error in Config File %s",filenamepath)
                logging.error(jsondata)
                jsondata = {}
        try:
            self.data = self.default_config
            self.data.update(jsondata)

        except:
            logging.error ("Error in Config File %s",filenamepath)
            logging.error(self.data)
            self.data={}        

    def save(self,filepathname=""):
        # Write JSON file
        if filepathname == "":
            filepathname = self.filepath
        with open(filepathname, 'w', encoding='utf8') as outfile:
            json.dump(self.data, outfile, ensure_ascii=False, indent=4)
            logging.info ("Config File %s saved",filepathname)

        