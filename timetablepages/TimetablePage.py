# -*- coding: utf-8 -*-
#
#         MobaLedCheckColors: Color checker for WS2812 and WS2811 based MobaLedLib
#
#         SerialMonitorPage
#
# * Version: 1.00
# * Author: Harold Linke
# * Date: December 25th, 2019
# * Copyright: Harold Linke 2019
# *
# *
# * MobaLedCheckColors on Github: https://github.com/haroldlinke/MobaLedCheckColors
# *
# *
# * History of Change
# * V1.00 25.12.2019 - Harold Linke - first release
# *
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

import tkinter as tk
from tkinter import ttk,messagebox
#from tkcolorpicker.functions import tk, ttk, round2, create_checkered_image, \
#    overlay, hsv_to_rgb, hexa_to_rgb, rgb_to_hexa, col2hue, rgb_to_hsv, convert_K_to_RGB
#from tkcolorpicker.alphabar import AlphaBar
#from tkcolorpicker.gradientbar import GradientBar
#from tkcolorpicker.lightgradientbar import LightGradientBar
#from tkcolorpicker.colorsquare import ColorSquare
#from tkcolorpicker.colorwheel import ColorWheel
#from tkcolorpicker.spinbox import Spinbox
#from tkcolorpicker.limitvar import LimitVar
from timetablepages.configfile import ConfigFile
from locale import getdefaultlocale
from scrolledFrame.ScrolledFrame import VerticalScrolledFrame,HorizontalScrolledFrame,ScrolledFrame

#import re
#import math
import os
import sys
import threading
import queue
import time
import logging
#import concurrent.futures
#import random
#import webbrowser
from datetime import datetime
#import json
import timetablepages.TimetablegraphCanvas

VERSION ="V01.17 - 25.12.2019"
LARGE_FONT= ("Verdana", 12)
VERY_LARGE_FONT = ("Verdana", 14)
SMALL_FONT= ("Verdana", 8)


ThreadEvent = None
            
class TimeTablePage(tk.Frame):
    def __init__(self, parent, controller):
        self.tabClassName = "Bildfahrplan"
        tk.Frame.__init__(self,parent)
        self.controller = controller
        macrodata = self.controller.MacroDef.data.get(self.tabClassName,{})
        self.tabname = macrodata.get("MTabName",self.tabClassName)
        self.title = macrodata.get("Title",self.tabClassName)
        self.canvas_height = self.controller.canvas_height
        self.canvas_width = self.controller.canvas_width
        self.fpl_filename = ""
        self.xml_filename = ""
        
        button1_text = macrodata.get("Button_1",self.tabClassName)
        button2_text = macrodata.get("Button_2",self.tabClassName)        

        self.grid_columnconfigure(0,weight=1)
        self.grid_rowconfigure(0,weight=1)
        
        self.frame=ttk.Frame(self,relief="ridge", borderwidth=1)
        self.frame.grid_columnconfigure(0,weight=1)
        self.frame.grid_rowconfigure(0,weight=1)
        self.frame.grid(row=0,column=0,sticky="nesw")
        
        #self.scroll_main_frame = ScrolledFrame(self.frame)
        #self.scroll_main_frame.grid_columnconfigure(0,weight=1)
        #self.scroll_main_frame.grid_rowconfigure(0,weight=1)
        #self.scroll_main_frame.grid(row=0,column=0,sticky="nesw")
        
        #self.main_frame = ttk.Frame(self.scroll_main_frame.interior, relief="flat", borderwidth=1)
        #self.main_frame = self.scroll_main_frame.interior
        #self.main_frame.grid_columnconfigure(0,weight=1)
        #self.main_frame.grid_rowconfigure(2,weight=1)
        #self.main_frame.grid(row=0,column=0,sticky="nesw")
        
        #title_frame = ttk.Frame(self.main_frame, relief="ridge", borderwidth=2)

        #label = ttk.Label(title_frame, text=self.title, font=LARGE_FONT)
        #label.pack(padx=5,pady=(5,5))
        
        #config_frame = self.controller.create_macroparam_frame(self.main_frame,self.tabClassName, maxcolumns=1,startrow =1,style="CONFIGPage")        
        
        #button_frame = ttk.Frame(self.main_frame)

        #self.send_button = ttk.Button(button_frame, text=button1_text,width=30, command=self.send)
        #self.send_button.pack(side="left", padx=4, pady=(4, 1))
        #self.stop_button = ttk.Button(button_frame, text=button2_text,width=30, command=self.stop)
        #self.stop_button.pack(side="left", padx=4, pady=(4, 1))
        #text_frame = tk.Frame(self.main_frame, padx=10, pady= 10)
        
           
        #canvas_widget = tk.Canvas(self.main_frame, bg='#FFFFFF',width=4000,height=2000) #width=2000,height=1000)
        #canvas_widget.grid(row=3,column=0,rowspan=2,padx=10,pady=10,sticky="nesw")
        frame = ttk.Frame(self.frame)
        frame.grid(row=0,column=0,sticky="nesw")
        frame.grid_columnconfigure(0,weight=1)
        frame.grid_rowconfigure(0,weight=1)        
        self.canvas=tk.Canvas(frame,width=self.canvas_width,height=self.canvas_height,scrollregion=(0,0,self.canvas_width,self.canvas_height),bg="white")
        hbar=tk.Scrollbar(frame,orient=tk.HORIZONTAL)
        hbar.pack(side=tk.BOTTOM,fill=tk.X)
        hbar.config(command=self.canvas.xview)
        vbar=tk.Scrollbar(frame,orient=tk.VERTICAL)
        vbar.pack(side=tk.RIGHT,fill=tk.Y)
        vbar.config(command=self.canvas.yview)
        self.canvas.config(width=self.canvas_width,height=self.canvas_height)
        self.canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.pack(side=tk.LEFT,expand=True,fill=tk.BOTH)
        self.timetable_main = timetablepages.TimetablegraphCanvas.Timetable_main(self.controller, self.canvas)
        self.controller.timetable_main = self.timetable_main

    def save_as_png(self, fileName):
        # save postscipt image 
        self.canvas.update()
        self.canvas.postscript(file = fileName + '.eps',colormode='color',width=self.canvas_width,height=self.canvas_height) 
        # use PIL to convert to PNG 
        img = Image.open(fileName + '.eps')
        try:

            img.save(fileName + '.png', 'png')
        except: 
            print("Error while generating png-file- Ghostscript not found")
            pass
        
    def create_train_type_to_color_dict(self):
        self.train_type_to_color_dict = {}
        config_traintype_to_color_dict = self.getConfigData("Bfp_TrainTypeColors")
        
        for i,value_dict in config_traintype_to_color_dict.items():
            print(repr(value_dict))
            traintype = value_dict.get("Bfp_TrainType","")
            traintypecolor = value_dict.get("Bfp_TrainTypeColor","black")
            if traintype != "":
                self.train_type_to_color_dict[traintype]=traintypecolor
        

    def tabselected(self):
        logging.debug("Tabselected: %s",self.tabname)
        #self.controller.currentTabClass = self.tabClassName
        logging.info(self.tabname)
        self.controller.set_statusmessage("Bildfahrplanerstellung gestartet - bitte etwas Geduld")
        self.controller.update()
        self.canvas_width = self.getConfigData("Bfp_width")
        self.canvas_height = self.getConfigData("Bfp_height")
        fpl_filename = self.getConfigData("Bfp_filename")
        xml_filename = self.getConfigData("Bfp_trainfilename")
        starthour = self.getConfigData("Bfp_start")
        duration = self.getConfigData("Bfp_duration")
        self.create_train_type_to_color_dict()
        self.timetable_main.set_zuggattung_to_color(self.train_type_to_color_dict)
        
        if fpl_filename == "":
            self.controller.set_statusmessage("Kein ZUSI Fahrplan eingestellt. Bitte auf der Seite <Bahnhof-Einstellungen> auswählen")
            return
        if xml_filename == "":
            self.controller.set_statusmessage("Kein ZUSI Buchfahrplann eingestellt. Bitte auf der Seite <Bahnhof-Einstellungen> auswählen")
            return
        if starthour == "":
            self.controller.set_statusmessage("Keine Startzeit für den Bildfahrplan eingestellt. Bitte auf der Seite <Bahnhof-Einstellungen> einstellen")
            return
        if duration == "":
            self.controller.set_statusmessage("Kein Zeitraum für den Bildfahrplan eingestellt. Bitte auf der Seite <Bahnhof-Einstellungen> einstellen")
            return        
        
        self.timetable_main.create_zusi_zug_liste(fpl_filename)
        
        if (fpl_filename != self.fpl_filename) or (self.xml_filename != xml_filename) or (self.starthour != starthour) or (self.duration != duration):
            self.xml_filename = xml_filename
            self.fpl_filename = fpl_filename
            self.starthour = starthour
            self.duration = duration
            self.timetable_main.redo_fpl_and_canvas(self.canvas_width,self.canvas_height,fpl_filename=fpl_filename,xml_filename=xml_filename,starthour=starthour,duration=duration)
        else:
            old_height =self.canvas.winfo_reqheight()
            old_width = self.canvas.winfo_reqwidth()
            
            #if (old_height-4 != self.canvas_height) or (old_width-4 != self.canvas_width):
            self.timetable_main.resize_canvas(self.canvas_width,self.canvas_height,starthour,duration)
    
    def tabunselected(self):
        logging.debug("Tabunselected: %s",self.tabname)
        pass 
    
    def _update_value(self,paramkey):
        logging.info("SerialMonitorPage - update_value: %s",paramkey)
        message = self.controller.get_macroparam_val(self.tabClassName, "SerialMonitorInput")+"\r\n" #self.input.get() +"\r\n"

    def getConfigData(self, key):
        return self.controller.getConfigData(key)
    
    def readConfigData(self):
        self.controller.readConfigData()
        
    def setConfigData(self,key, value):
        self.controller.setConfigData(key, value)

    def setParamData(self,key, value):
        self.controller.setParamData(key, value)

    def MenuUndo(self,_event=None):
        pass
    
    def MenuRedo(self,_event=None):
        pass