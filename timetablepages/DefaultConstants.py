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

PROG_VERSION ="V00.07 01.02.2021"
LARGE_FONT= ("Verdana", 12)
VERY_LARGE_FONT = ("Verdana", 14)
NORMAL_FONT = ("Verdana", 10)
SMALL_FONT= ("Verdana", 8)
Very_SMALL_FONT= ("Verdana", 6)

STD_FONT = ("SANS_SERIF",10)

MAC_Version = False #True

COLORCOR_MAX = 255

SIZEFACTOR = 1 # 720/1280

# colorwheel view
DELTA_H = 270
INVERT_WHEEL = True

# filenames
# all filenames are relativ to the location of the main program pyProg_generator_MobaLedLib.py
MAIN_PROG_NAME = "TimeTable"

LOG_FILENAME = 'logfile.log'
PARAM_FILENAME = MAIN_PROG_NAME + '_param.json'
CONFIG_FILENAME = MAIN_PROG_NAME + '_config.json'
MACRODEF_FILENAME = MAIN_PROG_NAME + '_macrodef.json'
MACROPARAMDEF_FILENAME = MAIN_PROG_NAME + '_macroparamdef.json'
DISCONNECT_FILENAME = MAIN_PROG_NAME + '_disconnect.txt'
CLOSE_FILENAME = MAIN_PROG_NAME + '_close.txt'
TEMP_LEDEFFECTTABLE_FILENAME = "temp_ledeffect_table.json"

DEFAULT_CONFIG = {
                    "Bfp_width": 2000,
                    "Bfp_height": 1000,
                    "Bfp_filename": "",
                    "Bfp_trainfilename": "",
                    "pos_x": 100,
                    "pos_y": 100,
                    "startpage": 1,
                    "startpagename" : "StartPage",
                }

DEFAULT_PARAM = {}

CONFIG2PARAMKEYS = {
                    "old_color"   :"color",
                    "lastLed"     :"Lednum",
                    "lastLedCount":"LedCount", 
                    "serportname" :"comport",
                    "palette"     :"coltab", 
                    }

TOOLTIPLIST = {
                   "Alte Farbe": "Alte Farbe",
                   "Aktuelle Farbe": "Aktuelle Farbe",
                   "ColorWheel":"Farbton und Sättigung auswählen durch Mausklick"
                   }


