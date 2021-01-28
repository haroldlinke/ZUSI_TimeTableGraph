#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#         TimetableGraph
#
# * Version: 0.01
# * Author: Harold Linke
# * Date: January 12th, 2021
# * Copyright: Harold Linke 2021
# *
# *
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
        # type:
        """ Config Constructor Method (__init__)

        Arguments:
            default_config
            filename

        Raises:
            None
        """
        if filedir == "":
            filedir = os.path.dirname(os.path.realpath(__file__))
            
        filepath1 = os.path.join(filedir, filename)
        
        self.filepath = os.path.normpath(filepath1)

        try:
            jsondata={}
            file_not_found=True
            with open(self.filepath, "r", encoding='utf8') as read_file:
                file_not_found=False
                jsondata = json.load(read_file)
        except ValueError as err:
            logging.error ("ERROR: JSON Error in Config File %s",self.filepath)
            logging.error(err)
        except:
            if file_not_found:
                logging.warning ("Warning: Config File %s not found",self.filepath)
            else:
                logging.error ("ERROR: JSON Error in Config File %s",self.filepath)
                logging.error(jsondata)
                jsondata = {}
            
        try:
            self.data = default_config.copy()
            if self.data == {}:
                self.data.update(jsondata)
            else:
                if True: #all(elem in self.data.keys() for elem in jsondata.keys()):
                    self.data.update(jsondata)
                else:
                    print("Default:", self.data.keys())
                    print(self.filepath,"-",jsondata.keys())
                    logging.error ("ERROR: JSON Error in Config File %s - wrong key in config-file",self.filepath)
                    logging.error(jsondata)
                    jsondata = {}                

        except:
            logging.error ("Error in Config File %s",self.filepath)
            logging.error(self.data)
            self.data = default_config.copy()
        
        create_sorted=False
        if create_sorted:
            sorted_dict = dict(sorted(self.data.items()))
            with open(self.filepath+"sort", 'w', encoding='utf8') as outfile:
                json.dump(sorted_dict, outfile, ensure_ascii=False, indent=4)            

    def save(self):

        # Write JSON file
        with open(self.filepath, 'w', encoding='utf8') as outfile:
            json.dump(self.data, outfile, ensure_ascii=False, indent=4)