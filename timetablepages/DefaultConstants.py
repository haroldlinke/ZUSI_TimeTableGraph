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

PROG_VERSION ="V02.03 02.03.2021"
LARGE_FONT= ("Verdana", 12)
VERY_LARGE_FONT = ("Verdana", 14)
NORMAL_FONT = ("Verdana", 10)
SMALL_FONT= ("Verdana", 8)
Very_SMALL_FONT= ("Verdana", 6)
STD_FONT = ("SANS_SERIF",10)
LARGE_STD_FONT = ("SANS_SERIF",14)

SIZEFACTOR = 1 # 720/1280

# filenames
# all filenames are relativ to the location of the main program pyProg_generator_MobaLedLib.py
MAIN_PROG_NAME = "TimeTable"

LOG_FILENAME = 'logfile.log'
PARAM_FILENAME = MAIN_PROG_NAME + '_param.json'
CONFIG_FILENAME = MAIN_PROG_NAME + '_config.json'
MACRODEF_FILENAME = MAIN_PROG_NAME + '_macrodef.json'
MACROPARAMDEF_FILENAME = MAIN_PROG_NAME + '_macroparamdef.json'

DEFAULT_CONFIG = {
                    "Bfp_width": 2000,
                    "Bfp_height": 1000,
                    "Bfp_filename": "",
                    "Bfp_trainfilename": "",
                    "pos_x": 100,
                    "pos_y": 100,
                    "startpage": 1,
                    "startpagename" : "StartPage",
                    "StationChooser": ""
                }

def get_shortcut(activity,type,action):
    return shortCutDict[activity][type][action]

shortCutDict =  { "MouseButton":
                     {"move_from"        : '<Shift-ButtonPress-1>',
                      "move_to"          : '<Shift-B1-Motion>',
                      "Activate_Min"     : "<Button-1>",
                      "Activate_Sec"     : "<Alt-1>",
                      "Motion_Min"       : "<B1-Motion>",
                      "Motion_Sec"       : "<Alt-B1-Motion>"                      
                      },
                     "MouseWheel" :
                     {"Zoom" : "<Control-MouseWheel>",
                      "onAltMouseWheel"  : "<Alt-MouseWheel>",
                      "onMouseWheel"     : "<MouseWheel>",
                      "onShiftMouseWheel":"<Shift-MouseWheel>"                      
                      },
                     "Key":
                     {"onRestoreZoom"     : "<Home>", 
                      "onMoveCanvasUp"    : "<Up>",
                      "onMoveCanvasDown"  : "<Down>",
                      "onMoveCanvasLeft"  : "<Left>", 
                      "onMoveCanvasRight" : "<Right>",
                      "onZoomIn"          : "<Control-Down>",
                      "onZoomOut"         : "<Control-Up>",
                      "onRefreshCanvas"   : "<F5>",
                      "onTimeDecMinute"   : "-",
                      "onTimeIncMinute"   : "+",
                      "onPreviousStation" : "4",
                      "onNextStation"     : "6",
                      "onTimeDec10Sec"    : "<Shift-Key-8>",
                      "onTimeInc10Sec"    : "<Shift-Key-2>",
                      "onTimeDecSec"      : "<Alt-Key-8>",
                      "onTimeIncSec"      : "<Alt-Key-2>"                                 
                     }
                   }


