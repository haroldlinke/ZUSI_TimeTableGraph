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

import tkinter as tk
from tkinter import ttk
#from timetablepages.configfile import ConfigFile
#from scrolledFrame.ScrolledFrame import VerticalScrolledFrame,HorizontalScrolledFrame,ScrolledFrame

#import re
#import math
import os
#import sys
#import threading
#import queue
#import time
import logging
#import concurrent.futures
#import random
#import webbrowser
#from datetime import datetime
#import json
import timetablepages.TimetablegraphCanvas
from PIL import Image, EpsImagePlugin

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
        self.grid_columnconfigure(0,weight=1)
        self.grid_rowconfigure(0,weight=1)
        self.frame=ttk.Frame(self,relief="ridge", borderwidth=1)
        self.frame.grid_columnconfigure(0,weight=1)
        self.frame.grid_rowconfigure(0,weight=1)
        self.frame.grid(row=0,column=0,sticky="nesw")
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
        self.scalefactorunit = 0.75
        self.canvas_bindings()
        self.controller.timetable_main = self.timetable_main
        
    def move_from(self, event):
        ''' Remember previous coordinates for scrolling with the mouse '''
        self.canvas.scan_mark(event.x, event.y)

    def move_to(self, event):
        ''' Drag (move) canvas to the new position '''
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        
    def onCtrlMouseWheel(self, event):
        scale = 1.0
        if event.delta == -120:
            scale *= self.scalefactorunit
        if event.delta == 120:
            scale /= self.scalefactorunit
        self.resize(event, scale)
        #x = self.canvas.canvasx(event.x)
        #y = self.canvas.canvasy(event.y)
        #self.canvas.scale('all', x, y, scale, scale)
        #self.canvas.configure(scrollregion=self.canvas.bbox('all'))
    
    def onAltMouseWheel(self, event):
        pass
    
    def onMouseWheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def onArrowUp(self, event):
        if event.keysym == "Up":
            self.canvas.yview_scroll(-1, "units")
        else:
            self.canvas.yview_scroll(-1, "pages")
    
    def onArrowDown(self, event):
        if event.keysym == "Down":
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(1, "pages")
    
    def onCTRLArrowDown(self, event):
        scale = self.scalefactorunit
        self.resize(event, scale)
        #x = self.canvas.canvasx(event.x)
        #y = self.canvas.canvasy(event.y)
        #self.canvas.scale('all', x, y, scale, scale)
        #self.canvas.configure(scrollregion=self.canvas.bbox('all'))        
    
    def onCTRLArrowUp(self, event):
        scale = 1.0/self.scalefactorunit
        self.resize(event, scale)
        #x = self.canvas.canvasx(event.x)
        #y = self.canvas.canvasy(event.y)
        #self.canvas.scale('all', x, y, scale, scale)
        #self.canvas.configure(scrollregion=self.canvas.bbox('all'))        
    
    def onArrowLeft(self, event):
        self.canvas.xview_scroll(-1, "units")
    
    def onArrowRight(self, event):
        #print(event.keysym)
        self.canvas.xview_scroll(1, "units")
    
    def onPrior(self, event):
        self.canvas.xview_scroll(1, "pages")
    
    def onNext(self, event):
        #print(event.keysym)
        self.canvas.xview_scroll(-1, "pages")
    
    def onShiftMouseWheel(self, event):
        self.canvas.xview_scroll(int(-1*(event.delta/120)), "units")
    
    def fit_canvas(self, event):
        #print(event.keysym)
        pass
        
    def resize(self, event, scale):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.canvas.scale('all', x, y, scale, scale)
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))           
        
    def canvas_bindings(self):
        self.canvas.bind('<ButtonPress-1>', self.move_from)
        self.canvas.bind('<B1-Motion>',     self.move_to)
        self.canvas.bind("<Control-MouseWheel>", self.onCtrlMouseWheel)
        self.canvas.bind("<Alt-MouseWheel>", self.onAltMouseWheel)
        self.canvas.bind("<MouseWheel>", self.onMouseWheel)
        self.canvas.bind("<Shift-MouseWheel>", self.onShiftMouseWheel)
        self.bind("f", self.fit_canvas)
        self.bind("<Home>", self.fit_canvas)
        self.frame.bind("<Up>", self.onArrowUp)
        self.frame.bind("<Down>", self.onArrowDown)
        self.frame.bind("<Left>", self.onArrowLeft)
        self.frame.bind("<Right>", self.onArrowRight)
        self.frame.bind("<Control-Up>", self.onCTRLArrowUp)
        self.frame.bind("<Control-Down>", self.onCTRLArrowDown)        
        self.frame.bind("<Prior>", self.onArrowUp)
        self.frame.bind("<Next>", self.onArrowDown)
        self.frame.bind("<Shift-Prior>", self.onPrior)
        self.frame.bind("<Shift-Next>", self.onNext) 
     

    def save_as_pdf(self, fileName):
        # save postscipt image 
        self.canvas.update()
        self.canvas.postscript(file = fileName + 'tmp.eps',colormode='color',width=self.canvas_width,height=self.canvas_height) 
        EpsImagePlugin.gs_windows_binary =  self.controller.ghostscript_path  #r"D:\data\doc\GitHub\ZUSI_TimeTableGraph\gs9.53.3\bin\gswin32c.exe"  #r'C:\Program Files (x86)\gs\gs9.53.3\bin\gswin32c'
        img = Image.open(fileName + 'tmp.eps')
        img.load(scale=8)
        size = img.size
        try:
            #img.save(fileName + '.png', 'png')
            img.save(fileName,"pdf",resolution=300)
        except BaseException as e:
            print("Error while generating pdf-file\n %s",e)
            pass
        
    def save_as_eps(self, fileName):
        # save postscipt image 
        self.canvas.update()
        self.canvas.postscript(file = fileName,colormode='color',width=self.canvas_width,height=self.canvas_height)
        
    def save_as_image(self, fileName):
        # save postscipt image 
        self.canvas.update()
        tmp_filename = fileName + '.tmp.eps'
        self.canvas.postscript(file = tmp_filename,colormode='color',width=self.canvas_width,height=self.canvas_height) 
        EpsImagePlugin.gs_windows_binary =  self.controller.ghostscript_path  #r"D:\data\doc\GitHub\ZUSI_TimeTableGraph\gs9.53.3\bin\gswin32c.exe"  #r'C:\Program Files (x86)\gs\gs9.53.3\bin\gswin32c'
        img = Image.open(tmp_filename)
        img.load(scale=8)
        size = img.size
        try:
            img.save(fileName)
        except BaseException as e:
            print("Error while generating png-file\n %s",e)
            pass    
        
    def create_train_type_to_color_dict(self):
        self.train_type_prop_dict = {}
        self.train_type_to_width_dict = {}
        config_traintype_prop_dict = self.getConfigData("Bfp_TrainTypeProp")
        config_traintype_prop_default_dict = self.getConfigData("Bfp_TrainTypePropDefault")
        config_traintype_prop_default_dict["0"]["Bfp_TrainType"]="*"
        if config_traintype_prop_dict == None:
            config_traintype_prop_dict = config_traintype_prop_default_dict
        else:
            config_traintype_prop_dict[999]=config_traintype_prop_default_dict["0"]
        for i,value_dict in config_traintype_prop_dict.items():
            print(repr(value_dict))
            traintype = value_dict.get("Bfp_TrainType","")
            #traintypecolor = value_dict.get("Bfp_TrainTypeColor","black")
            #traintypewidth = value_dict.get("Bfp_TrainTypeWidth","4")
            if traintype != "":
                traintype=traintype.replace(" ","")
                traintypelist = traintype.split(",")
                for traintype in traintypelist:
                    self.train_type_prop_dict[traintype]=value_dict

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
        self.timetable_main.set_traintype_prop(self.train_type_prop_dict)

        
        if fpl_filename == "":
            self.controller.set_statusmessage("Kein ZUSI Fahrplan eingestellt. Bitte auf der Seite <Bahnhof-Einstellungen> auswählen")
            return
        if xml_filename == "":
            self.controller.set_statusmessage("Kein ZUSI Buchfahrplann eingestellt. Bitte auf der Seite <Bahnhof-Einstellungen> auswählen")
            return
        if starthour == "" or starthour==None:
            self.controller.set_statusmessage("Keine Startzeit für den Bildfahrplan eingestellt. Bitte auf der Seite <Bahnhof-Einstellungen> einstellen")
            return
        if duration == "" or duration==None:
            self.controller.set_statusmessage("Kein Zeitraum für den Bildfahrplan eingestellt. Bitte auf der Seite <Bahnhof-Einstellungen> einstellen")
            return        
        
        self.timetable_main.create_zusi_zug_liste(fpl_filename)
        
        if True: # (fpl_filename != self.fpl_filename) or (self.xml_filename != xml_filename) or (self.starthour != starthour) or (self.duration != duration):
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