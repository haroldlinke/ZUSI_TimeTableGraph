# -*- coding: utf-8 -*-
#
#         MobaLedCheckColors: Color checker for WS2812 and WS2811 based MobaLedLib
#
#         DefaultData
#
# * Version: 2.25
# * Author: Harold Linke
# * Date: January 04th, 2020
# * Copyright: Harold Linke 2020
# *
# *
# * MobaLedCheckColors on Github: https://github.com/haroldlinke/MobaLedCheckColors
# *
# *
# * History of Change
# * V1.00 25.12.2019 - Harold Linke - first release
# * V2.00 11-04-2020 - Harold Linke - update with pyPrgramGenerator
# *
# * MobaLedCheckColors supports the MobaLedLib by Hardi Stengelin
# * https://github.com/Hardi-St/MobaLedLib
# *
# * MobaLedCheckColors is free software: you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation, either version 3 of the License, or
# * (at your option) any later version.
# *
# * MobaLedCheckColors is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program.  If not, see <http://www.gnu.org/licenses/>.
# *
# * MobaLedCheckColors is based on tkColorPicker by Juliette Monsel
# * https://sourceforge.net/projects/tkcolorpicker/
# *
# * tkcolorpicker - Alternative to colorchooser for Tkinter.
# * Copyright 2017 Juliette Monsel <j_4321@protonmail.com>
# *
# * tkcolorpicker is free software: you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation, either version 3 of the License, or
# * (at your option) any later version.
# *
# * tkcolorpicker is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program.  If not, see <http://www.gnu.org/licenses/>.
# *
# * The code for changing pages was derived from: http://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter
# * License: http://creativecommons.org/licenses/by-sa/3.0/
# ***************************************************************************

PROG_VERSION ="V00.10 24.01.2021"
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
CONFIG_FILENAME = '..\\' + MAIN_PROG_NAME + '_config.json'
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
                   

BLINKFRQ     = 2 # Blinkfrequenz in Hz

ARDUINO_WAITTIME = 0.02  # Wartezeit zwischen 2 Kommandos in Sekunden 
ARDUINO_LONG_WAITTIME = 0.5





