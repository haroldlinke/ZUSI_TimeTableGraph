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

import tkinter as tk
from tkinter import ttk,filedialog, colorchooser
from timetablepages.configfile import ConfigFile
from timetablepages.dictFile import saveDicttoFile
from timetablepages.ConfigurationPage import ConfigurationPage
from timetablepages.StationsConfigurationPage import StationsConfigurationPage
from timetablepages.TimetablePage import TimeTablePage
from timetablepages.StartPage import StartPage
from timetablepages.tooltip import Tooltip,Tooltip_Canvas
from timetablepages.DefaultConstants import DEFAULT_CONFIG, SMALL_FONT, VERY_LARGE_FONT, PROG_VERSION, SIZEFACTOR,\
PARAM_FILENAME, CONFIG_FILENAME, TOOLTIPLIST, MACRODEF_FILENAME, MACROPARAMDEF_FILENAME,LOG_FILENAME
from scrolledFrame.ScrolledFrame import VerticalScrolledFrame,ScrolledFrame,HorizontalScrolledFrame
from tkcolorpicker.limitvar import LimitVar
from tkcolorpicker.spinbox import Spinbox
import platform
import os
import sys
#import time
import logging
import webbrowser
import argparse
#from datetime import datetime


# ------------------------------

tabClassList = ( StartPage,TimeTablePage,StationsConfigurationPage,ConfigurationPage)

defaultStartPage = "StartPage"

# ----------------------------------------------------------------
# Class TimeTableGraphMain
# ----------------------------------------------------------------

class TimeTableGraphMain(tk.Tk):
    
    # ----------------------------------------------------------------
    # TimeTableGraphMain __init__
    # ----------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        self.mainfile_dir = os.path.dirname(os.path.realpath(__file__))
        self.readConfigData()
        self.macroparams_value = {}
        self.macroparams_var = {"dummy": {}}
        self.persistent_param_dict = {}
        self.macroparam_frame_dict = {}
        self.bind_keys_dict = {}
        self.tooltip_var_dict = {}
        self.platform=platform.platform().upper()
        self.buttonlist= []
        self.timetable_main=None

        self.fontlabel = self.get_font("FontLabel")
        self.fontspinbox = self.get_font("FontSpinbox")
        self.fonttext = self.get_font("FontText")
        self.fontbutton = self.get_font("FontLabel")
        self.fontentry = self.get_font("FontLabel")
        self.fonttext = self.get_font("FontText")
        
        self.canvas_width = self.getConfigData("Bfp_width")
        self.canvas_height = self.getConfigData("Bfp_height")
        
        self.ghostscript_path_rel = self.getConfigData("GhostScriptPath")
        
        if self.ghostscript_path_rel == None:
            self.ghostscript_path_rel = r"gs9.53.3\bin\gswin32c.exe"
            
        self.ghostscript_path = os.path.join(self.mainfile_dir,self.ghostscript_path_rel)

        macrodata = self.MacroDef.data.get("StartPage",{})
        
        self.currentTabClass = ""
        self.paramDataChanged = False

        tk.Tk.__init__(self, *args, **kwargs)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        logging.debug("Screenwidth: %s Screenheight: %s",screen_width,screen_height)
        
        if screen_width<1500:
            SIZEFACTOR_width = screen_width/1500
            self.window_width=screen_width*0.8
        else:
            self.window_width = screen_width*0.8 # 1500
        
        if screen_height < 1080:
            self.window_height=screen_height*0.8
        else:
            self.window_height=screen_height*0.8 #1080
        
        if self.getConfigData("pos_x") < screen_width and self.getConfigData("pos_y") < screen_height:
            self.geometry('%dx%d+%d+%d' % (self.window_width,self.window_height,self.getConfigData("pos_x"), self.getConfigData("pos_y")))
        else:
            self.geometry("%dx%d+0+0" % (self.window_width,self.window_height))

        tk.Tk.wm_title(self, "TimetableGraph " + PROG_VERSION)

        self.title("TimetableGraph " + PROG_VERSION)
        self.transient(self.master)
        self.resizable(True,True)
        self.color = ""
        style = ttk.Style(self)
        style.map("palette.TFrame", relief=[('focus', 'sunken')],
                  bordercolor=[('focus', "#4D4D4D")])
        self.configure(background=style.lookup("TFrame", "background"))
         
        menu = tk.Menu(self)
        self.config(menu=menu)
        filemenu = tk.Menu(menu)
        menu.add_cascade(label="Bildfahrplan speichern", menu=filemenu)
        filemenu.add_command(label="als EPS", command=self.Save_Bfp_as_EPS)
        filemenu.add_command(label="als PDF", command=self.Save_Bfp_as_PDF)
        #filemenu.add_separator()
        filemenu.add_command(label="als Bild", command=self.Save_Bfp_as_Image)
        #filemenu.add_command(label="LED Liste speichern als", command=self.SaveFileLEDTab)
        #filemenu.add_separator()
        #filemenu.add_command(label="Beenden und Daten speichern", command=self.ExitProg_with_save)
        #filemenu.add_command(label="Beenden ohne Daten zu speichern", command=self.ExitProg)

        #colormenu = tk.Menu(menu)
        #menu.add_cascade(label="Farbpalette", menu=colormenu)
        #colormenu.add_command(label="letzte Änderung Rückgängig machen [CTRL-Z]", command=self.MenuUndo)
               
        #colormenu.add_command(label="von Datei lesen", command=self.OpenFile)
        #colormenu.add_command(label="speichern als ...", command=self.SaveFileas)
        #colormenu.add_separator()
        #colormenu.add_command(label="auf Standard zurücksetzen", command=self.ResetColorPalette)

        
        helpmenu = tk.Menu(menu)
        menu.add_cascade(label="Hilfe", menu=helpmenu)
        helpmenu.add_command(label="Hilfe öffnen", command=self.OpenHelp)
        helpmenu.add_command(label="Über...", command=self.About)

        # --- define container for tabs
        self.shutdown_frame = tk.Frame(self)
        
        shutdown_label = tk.Label(self.shutdown_frame,text="Shutting Down ...",font=VERY_LARGE_FONT)
        shutdown_label.grid(row=0,column=0,sticky="nesw")
        self.shutdown_frame.grid(row=0,column=0,sticky="nesw")
        self.shutdown_frame.grid_columnconfigure(0,weight=1)
        self.shutdown_frame.grid_rowconfigure(0,weight=1)
        
        use_horizontalscroll=False
        use_fullscroll=False
        use_verticalscroll = False
        if use_verticalscroll:
            self.scrolledcontainer = VerticalScrolledFrame(self)
        if use_horizontalscroll:
            self.scrolledcontainer = HorizontalScrolledFrame(self)
        if use_fullscroll:
            self.scrolledcontainer = ScrolledFrame(self)
            
        if use_verticalscroll or use_fullscroll or use_horizontalscroll:
            self.scrolledcontainer.grid(row=0,column=0,rowspan=1,columnspan=2,sticky="nesw")
            self.scrolledcontainer.grid_rowconfigure(0, weight=1)
            self.scrolledcontainer.grid_columnconfigure(0, weight=1)
            self.container = ttk.Notebook(self.scrolledcontainer.interior)
        else:
            self.container = ttk.Notebook(self)
            
        self.grid_rowconfigure(0,weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.statusmessage = tk.Label(self, text='', fg="black",bd=1, relief="sunken", anchor="w")
        
        self.container.grid(row=0,column=0,columnspan=2,sticky="nesw")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.tabdict = dict()
        
        for tabClass in tabClassList:
            logging.debug("TabClass: %s ",repr(tabClass))
            frame = tabClass(self.container,self)
            tabClassName = frame.tabClassName
            logging.debug("Create Tab: %s",tabClassName)
            self.tabdict[tabClassName] = frame
            self.container.add(frame, text=frame.tabname)
        
        self.container.bind("<<NotebookTabChanged>>",self.TabChanged)
        
        startpagename = self.getStartPageClassName()
        
        self.showFramebyName(startpagename)
        
        filedir = self.mainfile_dir # os.path.dirname(os.path.realpath(__file__))

        self.statusmessage.grid(row=1,column=0,sticky="ew")
        #self.statusmessage.pack(side="bottom", fill="x")
        self.ToolTip(self.statusmessage, text="Zeigt Meldungen und Fehler an")
        
        self.focus_set()
        #self.wait_visibility()

        self.lift()
        self.grab_set()
        
    def set_statusmessage(self,status_text,fg="black"):
        #logging.debug("set_statusmessage: %s",status_text)
        self.statusmessage.configure(text=status_text,fg=fg)

    def get_font(self,fontname):
        font_size = self.getConfigData(fontname)
        if font_size == None:
            return SMALL_FONT
        else:
            return ("Verdana", int(font_size))

    def Save_Bfp_as_PDF(self):
        filepath = filedialog.asksaveasfilename(filetypes=[("PDF files","*.pdf")],defaultextension=".pdf")
        if filepath:
            frame = self.tabdict["Bildfahrplan"]
            # save postscipt image
            frame.save_as_pdf(filepath)        

    def Save_Bfp_as_EPS(self):
        filepath = filedialog.asksaveasfilename(filetypes=[("EPS files","*.eps")],defaultextension=".eps")
        if filepath:
            frame = self.tabdict["Bildfahrplan"]
            # save postscipt image
            frame.save_as_eps(filepath)    

    def Save_Bfp_as_Image(self):
        filepath = filedialog.asksaveasfilename(filetypes=[("png","*.png"),("jpg","*.jpg"),("tiff","*.tiff")],defaultextension=".jpg")
        if filepath:
            frame = self.tabdict["Bildfahrplan"]
            # save postscipt image
            frame.save_as_image(filepath)

    def About(self):
        tk.messagebox.showinfo("ZUSI Timetablegraph by Harold Linke")

    def OpenHelp(self):
        self.call_helppage()

    def ResetColorPalette(self):
        frame = self.tabdict["ColorCheckPage"]
        frame.palette_reset_colors()

    def MenuUndo(self,_event=None):
        for key in self.tabdict:
            self.tabdict[key].MenuUndo() 
    
    def MenuRedo(self,_event=None):
        for key in self.tabdict:
            self.tabdict[key].MenuRedo()

    def ExitProg(self):
        self.cancel()
        
    def ExitProg_with_save(self):
        self.cancel_with_save()    

    def saveLEDTabtoFile(self, filepath):
               
        temp_dict = {"ledeffecttable":self.ledeffecttable.get_table(),
                     "ledgrouptable" :self.ledeffecttable.mledgrouptable}
        
        saveDicttoFile(filepath, temp_dict)

    def readLEDTabfromFile(self, filepath,tabselection=True):
        pass
        
    def save_persistent_params(self):
        for macro in self.persistent_param_dict:
            persistent_param_list = self.persistent_param_dict[macro]
            for paramkey in persistent_param_list:
                self.setConfigData(paramkey, self.get_macroparam_val(macro, paramkey))
            
    # ----------------------------------------------------------------
    #  cancel_with_save
    # ----------------------------------------------------------------
    def cancel_step2_with_save(self):
        logging.debug("Cancel_with_save2")
        self.setConfigData("pos_x", self.winfo_x())
        self.setConfigData("pos_y", self.winfo_y())
        self.save_persistent_params()
        self.SaveConfigData()
        self.SaveParamData()
        filedir = self.mainfile_dir # os.path.dirname(os.path.realpath(__file__))
        #temp_ledeffecttable_filename = os.path.join(filedir,self.tempLedeffecttableFilname)
        #self.saveLEDTabtoFile(temp_ledeffecttable_filename)
        self.close_notification()
        
    def cancel_step2_without_save(self):
        logging.debug("Cancel_without_save2")
        self.close_notification()           

    # ----------------------------------------------------------------
    #  cancel_with_save
    # ----------------------------------------------------------------
    def cancel_with_save(self):
        logging.debug("Cancel_with_save")
        #self.set_connectstatusmessage("Closing program...",fg="red")
        self.shutdown_frame.tkraise()
        self.update()        
        self.cancel_step2_with_save()   

    # ----------------------------------------------------------------
    #  cancel_without_save
    # ----------------------------------------------------------------
    def cancel_without_save(self):
        logging.debug("Cancel_without_save")
        #self.set_connectstatusmessage("Closing program...",fg="red")
        #i=0
        #for key in self.tabdict:
        #    #self.tabdict[key].cancel()
        #    self.container.tab(i, state="disabled")
        #    i+=1        
        #self.after(500, self.cancel_step2_without_save) # a trick to show the close message before closing
        
        self.shutdown_frame.tkraise()
        self.update()
        self.cancel_step2_without_save()

    # ----------------------------------------------------------------
    #  cancel
    # ----------------------------------------------------------------
    def cancel(self):
        logging.debug("Cancel")
        if self.paramDataChanged:
            answer = tk.messagebox.askyesnocancel ('Das Programm wird beendet','Daten wurden verändert. Sollen die Daten gesichert werden?',default='no')
            if answer == None:
                return # no cancelation
            
            if answer:
                self.cancel_with_save() 
            else:
                self.cancel_without_save()
        else:
            self.cancel_without_save()


    def close_notification(self):
        logging.debug("Close_notification")
        self.setConfigData("pos_x", self.winfo_x())
        self.setConfigData("pos_y", self.winfo_y())
        #if self.ParamData.data == {}: # ParamData is not used, interface is config data. In this case do not save config data - compatibility modus
        self.SaveConfigData()
        #try: #create a FINISH_File if possible to show the mobaledlib program that the program finished - ignore any error
        #    open(FINISH_FILE, 'a').close()                                       # 03.12.19:
        #except:
        #    pass
        self.destroy()        
        
    # ----------------------------------------------------------------
    # show_frame byName
    # ----------------------------------------------------------------
    def showFramebyName(self, pageName):
        frame = self.tabdict.get(pageName,None)
        if frame == None:
            pageName = "ColorCheckPage"
            frame = self.tabdict.get(pageName,None)
        if pageName == "ColorCheckPage":
            frame._update_cor_rgb()
        self.container.select(self.tabdict[pageName])

    # ----------------------------------------------------------------
    # Event TabChanged
    # ----------------------------------------------------------------        
    def TabChanged(self,_event=None):
        
        oldtab_name = self.currentTabClass
        if oldtab_name != "":
            oldtab = self.nametowidget(oldtab_name)
            oldtab.tabunselected()
        newtab_name = self.container.select()
        if newtab_name != "":
            newtab = self.nametowidget(newtab_name)
            self.currentTabClass = newtab_name
            self.current_tab = newtab
            newtab.tabselected()
        logging.debug("TabChanged %s - %s",oldtab_name,newtab_name)

    # ----------------------------------------------------------------
    # setParamDataChanged
    # ----------------------------------------------------------------        
    def setParamDataChanged(self):
        self.paramDataChanged=True
        
    # ----------------------------------------------------------------
    # startup_system
    # ----------------------------------------------------------------             
    def startup_system(self):
        
        pass
        
    # ----------------------------------------------------------------
    # getframebyName
    # ----------------------------------------------------------------
    def getFramebyName (self, pagename):
        return self.tabdict.get(pagename,None)
    
    # ----------------------------------------------------------------
    # getStartPageClassName
    # ----------------------------------------------------------------
    def getStartPageClassName (self):
        startpagename = COMMAND_LINE_ARG_DICT.get("startpagename","")
        if not startpagename in self.tabdict.keys():
            startpagename=""
            logging.debug("Commandline argument --startpage %s wrong. Allowed: %s",startpagename,repr(self.tabdict.keys()))
            
        if startpagename == "":
            startpagenumber = self.getConfigData("startpage")
            startpagename = startpageNumber2Name.get(startpagenumber,self.ConfigData.data.get("startpagename","ColorCheckPage"))
        else:
            self.cl_arg_startpagename = startpagename
        return startpagename
    
    # ----------------------------------------------------------------
    # getStartPageClassIndex
    # ----------------------------------------------------------------
    def getStartPageClassIndex (self):
        startpagenumber = self.getConfigData("startpage")
        startpagename = startpageNumber2Name.get(startpagenumber,self.ConfigData.data.get("startpagename","ColorCheckPage"))
        startpageindex = tabClassName2Index.get(startpagename,"1")
        return startpageindex
    # ----------------------------------------------------------------
    # getTabNameList
    # ----------------------------------------------------------------
    def getTabNameList (self):
        return list(tabClassName2Name.values())
    
    # ----------------------------------------------------------------
    # getStartPageName
    # ----------------------------------------------------------------
    def getStartPageName(self, combolist_index):
        return tabIndex2ClassName.get(str(combolist_index),defaultStartPage)

    def call_helppage(self,event=None):
        macrodata = self.MacroDef.data.get("HelpPage",{})
        helppageurl = macrodata.get("HelpPageURL","")
        if helppageurl == "":
            tk.messagebox.showinfo("ZUSI Timetablegraph by Harold Linke\nHelp not available yet")
        else:
            webbrowser.open_new_tab(helppageurl)

    def getConfigData(self, key):
        logging.debug("GetConfigData Key: %s",key)
        return self.ConfigData.data.get(key,DEFAULT_CONFIG.get(key,None))
    
    def getConfigData_multiple(self, configdatakey,paramkey,index):
        value = None
        index_str = str(index)
        paramkey_dict = self.ConfigData.data.get(paramkey,{})
        if paramkey_dict != {}:
            configdatakey_dict = paramkey_dict.get(index_str,{})
            if configdatakey_dict != {}:
                value = configdatakey_dict.get(configdatakey,None)
        return value

            
    def readConfigData(self):
        logging.debug("readConfigData")
        filedir = self.mainfile_dir # os.path.dirname(os.path.realpath(__file__))
        parent_filedir = os.path.dirname(filedir) # get the parent dirname
        self.ConfigData = ConfigFile(DEFAULT_CONFIG, CONFIG_FILENAME,filedir=filedir)
        self.ConfigData.data.update(COMMAND_LINE_ARG_DICT) # overwrite configdata mit commandline args
        
        logging.debug("ReadConfig: %s",repr(self.ConfigData.data))
        
        macrodef_filename_str = MACRODEF_FILENAME
        macroparamdef_filename_str = MACROPARAMDEF_FILENAME
       
        if hasattr(sys, '_MEIPASS'):
            logging.debug('running in a PyInstaller bundle')
        
            try:
                # PyInstaller creates a temp folder and stores path in _MEIPASS
                base_path = sys._MEIPASS
                logging.debug("PyInstaller: sys._MEIPASS: %s",base_path)
                
                filedir = base_path
                
                # PyInstaller installation - macrodef and macroparamdef need to be copied
                
                srcfile = os.path.join(base_path,MACRODEF_FILENAME)
                destfile =  os.path.join(filedir,MACRODEF_FILENAME)
                
                macrodef_filename_str = srcfile
                #shutil.copy2(srcfile,destfile)
                #logging.debug("Copy %s to %s",srcfile,destfile)
                
                srcfile = os.path.join(base_path,MACROPARAMDEF_FILENAME)
                destfile =  os.path.join(filedir,MACROPARAMDEF_FILENAME)
                
                macroparamdef_filename_str = srcfile
                #shutil.copy2(srcfile,destfile)            
                #logging.debug("Copy %s to %s",srcfile,destfile)
                
            except BaseException as e:
                logging.debug("PyInstaller handling Error %s",e)
        else:
            logging.debug('running in a normal Python process')        
        try:
            self.MacroDef = ConfigFile({},MACRODEF_FILENAME,filedir=filedir)
            self.MacroParamDef = ConfigFile({},MACROPARAMDEF_FILENAME,filedir=filedir)
            logging.debug("ReadConfig: %s",repr(self.ConfigData.data))
        except BaseException as e:
            logging.debug("PyInstaller handling Error %s",e)            
        
    def setConfigData(self,key, value):
        self.ConfigData.data[key] = value
        
    def setConfigDataDict(self,param_dict):
        self.ConfigData.data.update(param_dict)  
    
    def setParamData(self,key, value):
        if self.ParamData.data:
            self.ParamData.data[key] = value

    def SaveConfigData(self):
        logging.debug("SaveConfigData")
        self.ConfigData.save()
        
    def SaveParamData(self):
        logging.debug("SaveParamData")
        if self.ParamData.data:
            self.ParamData.save()

    def ToolTip(self, widget,text="", key="",button_1=False):
        if text:
            tooltiptext = text
        else:
            tooltiptext = TOOLTIPLIST.get(key,key)
        tooltip_var = None
        try:
            tooltip_var = widget.tooltip
        except:
            tooltip_var = None
            
        if tooltip_var==None:
            tooltip_var=Tooltip(widget, text=tooltiptext,button_1=button_1)
            widget.tooltip = tooltip_var
        else:
            tooltip_var.unschedule()
            tooltip_var.hide()
            tooltip_var.update_text(text)            
        return
    
    def ToolTip_canvas(self, canvas, objid,text="", key="",button_1=False):
        if text:
            tooltiptext = text
        else:
            tooltiptext = _(TOOLTIPLIST.get(key,key))
        tooltip_var = None
        
        tooltip_var = self.tooltip_var_dict.get(objid,None)
            
        if tooltip_var==None:
            tooltip_var=Tooltip_Canvas(canvas, objid, text=tooltiptext,button_1=button_1)
            self.tooltip_var_dict[objid] = tooltip_var
        else:
            tooltip_var.unschedule()
            tooltip_var.hide()
            tooltip_var.update_text(text)            
        return

    def addtoclipboard(self,text):
        self.root.clipboard_clear()
        # text to clipboard
        self.root.clipboard_append(text)
        
    def readfromclipboard(self):
        
        return self.root.clipboard_get()        

    def setroot(self, app):
        self.root=app
        
  
    def set_macroparam_var(self, macro, paramkey,variable,persistent=False):
        paramdict = self.macroparams_var.get(macro,{})
        if paramdict == {}:
            self.macroparams_var[macro] = {}
            self.macroparams_var[macro][paramkey] = variable
        else:
            paramdict[paramkey] = variable
        if persistent:
            if self.persistent_param_dict.get(macro,[]) !=[]:
                self.persistent_param_dict[macro] += [paramkey]
            else:
                self.persistent_param_dict[macro] = [paramkey]
            
    def get_macroparam_val(self, macro, paramkey):
        value = ""
        variable = self.macroparams_var[macro][paramkey]
        try:
            var_class = variable.winfo_class()
            if var_class == "TCombobox":
                # value of combobox needs to be translated into a generic value
                current_index = variable.current()
                if current_index == -1: # entry not in list
                    value = variable.get()
                else:
                    if variable.keyvalues !=[]:
                        value_list = variable.keyvalues
                        value = value_list[current_index]
                    else:
                        value=variable.get()
            elif var_class == "Text":
                value = variable.get("1.0",tk.END)            
            else:
                value = variable.get()
        except:
            value = variable.get()
        return value     
            

    def get_macroparam_var_value(self, var,valuedict):
        
        paramconfig_dict = self.MacroParamDef.data.get(var.key,{})
        param_type = paramconfig_dict.get("Type","")
        
        if param_type == "":
            value = var.get()
            param_configname = paramconfig_dict.get("ConfigName",var.key)
            valuedict[param_configname] = value                                        
        elif param_type == "Combo":
            current_index = var.current()
            #if current_index == -1: # entry not in list
            value = var.get()
            #else:
            #    value_list = var.keyvalues
            #    value = value_list[current_index]
            param_configname_list = paramconfig_dict.get("ConfigName",[var.key])
    
            if param_configname_list[0] != "":
                valuedict[param_configname_list[0]] = value
            if param_configname_list[1] != "":
                valuedict[param_configname_list[1]] = current_index
        elif param_type in ["Entry","BigEntry","ChooseFileName","ChooseColor","String"]:
            value = var.get()
            param_configname = paramconfig_dict.get("ConfigName",var.key)
            valuedict[param_configname] = value
        elif param_type in ["Checkbutton"]:
            value = var.get()
            param_configname = paramconfig_dict.get("ConfigName",var.key)
            if value==0:
                valuedict[param_configname] = False
            else:
                valuedict[param_configname] = True
        return

            
    def get_macroparam_var_values(self, macro):
        valuedictmain = {}
        
        for macrokey in self.macroparams_var:
            valuedict = valuedictmain
            macro_components = macrokey.split(".")
            if macro_components[0] == macro:
                paramdict = self.macroparams_var.get(macrokey,{})
                if len(macro_components) > 1:
                    logging.info(macro_components)
                    valuedict2 = valuedict.get(macro_components[1],None)
                    if valuedict2 == None:
                        valuedict[macro_components[1]]={}
                        valuedict2 = valuedict.get(macro_components[1],None)
                    valuedict3 = valuedict2.get(macro_components[2],None)
                    if valuedict3 == None:
                        valuedict2[macro_components[2]]={}
                        valuedict3 = valuedict2.get(macro_components[2],None)
                    valuedict = valuedict3
                    
                if paramdict != {}:
                    for paramkey in paramdict:
                        var = paramdict.get(paramkey,None)
                        if var != None:
                            self.get_macroparam_var_value(var,valuedict)
        valuedict = valuedictmain
        return valuedict
     
     
    def set_macroparam_val(self, macro, paramkey, value, disable = False):
        if value != None:
            
            macroparams_dict = self.macroparams_var.get(macro,{})
                    
            variable = macroparams_dict.get(paramkey,None)
            if variable:
                if disable:
                    variable.config(state="normal")
                try:
                    var_class = variable.winfo_class()
                except: #limit_var has no winfo_class() function
                    var_class = "Limit_Var"                
    
                if var_class == "TCombobox":
                    # value of combobox needs to be translated into a generic value
                    if isinstance(value,int):
                        current_index = value
                    #else:
                    #    if value !="":
                    #        current_index = variable.keyvalues.index(value)
                    #    else:
                    #        current_index=0
                        value = variable.textvalues[current_index]
                    variable.set(value)
                elif var_class in ["Entry"]:
                    variable.delete(0,tk.END)
                    variable.insert(0,value)
                elif var_class in ["Text"]:
                    variable.delete(0.0,tk.END)
                    variable.insert(0.0,value)                          
                else:          
                    variable.set(value)
                if disable:
                    variable.config(state="disabled")                    
            else:
                pass
            
        return
    
    def set_all_macroparam_val(self, macro, paramvalues):
        try:
            if macro != "Set_ColTab":
                for paramkey in paramvalues:
                    value = paramvalues.get(paramkey)
                    if value!=None:
                        self.set_macroparam_val(macro,paramkey,value)
                        if paramkey=="Group_Colour":
                            self.setgroupcolor(value)
            else: # handle set_coltab
                self.update_color_palette(paramvalues)
                 
        except:
            pass
        return
    
    def get_all_macroparam_val(self, macro):
        paramvalues={}
        try:
            for paramkey in self.macroparams_var[macro]:
                value = self.get_macroparam_val(macro,paramkey)
                paramvalues[paramkey] = value
            for paramkey in self.macroparams_var["Group"]:
                value = self.get_macroparam_val("Group",paramkey)
                paramvalues[paramkey] = value            
        except:
            paramvalues = {}
        return paramvalues
    
    def getConfigDatakey(self,paramkey):
        
        ConfigDatakey = paramkey
        paramconfig_dict = self.MacroParamDef.data.get(paramkey,{})
        param_type = paramconfig_dict.get("Type","")
        
        ConfigDatakey=[]
        
        if param_type == "Combo":
            ConfigDatakeyList = paramconfig_dict.get("ConfigName",[paramkey,paramkey])
            ConfigDatakey = ConfigDatakeyList[1]
            if ConfigDatakey == "":
                ConfigDatakey = ConfigDatakeyList[0]
        else:
            ConfigDatakey = paramconfig_dict.get("ConfigName",paramkey)
        return ConfigDatakey
    
    def update_combobox_valuelist(self,macro,paramkey,valuelist,value=""):
        
        combobox_var = self.macroparams_var[macro][paramkey]
        
        combobox_var ["value"] = valuelist
        if value != "":
            combobox_var.set(value)
            
    def checkcolor(self,_event=None):
        self.showFramebyName("ColorCheckPage")    
    
    def create_macroparam_content(self,parent_frame, macro, macroparams,extratitleline=False,maxcolumns=5, startrow=0, minrow=4, style="MACROPage",generic_methods={}):
        
        if style =="MACROPage":
        
            MACROLABELWIDTH = int(15*SIZEFACTOR)
            MACRODESCWIDTH = int(20*SIZEFACTOR)
            MACRODESCWRAPL = int(120*SIZEFACTOR)
            
            PARAMFRAMEWIDTH = int(105*SIZEFACTOR)
            
            PARAMLABELWIDTH = int(15*SIZEFACTOR)
            PARAMLABELWRAPL = int(100*SIZEFACTOR)      
            
            PARAMSPINBOXWIDTH = 6
            PARAMENTRWIDTH = int(16*SIZEFACTOR)
            PARAMCOMBOWIDTH = int(16*SIZEFACTOR)
         
            STICKY = "nw"
            ANCHOR = "center"
            
        elif style == "CONFIGPage":
            MACROLABELWIDTH = 15*2
            MACRODESCWIDTH = 20*2
            MACRODESCWRAPL = 120*2
            
            PARAMFRAMEWIDTH = 105
            
            PARAMLABELWIDTH = 15
            PARAMLABELWRAPL = 100       
            
            PARAMSPINBOXWIDTH = 6
            PARAMENTRWIDTH = 16
            PARAMCOMBOWIDTH = 16
         
            STICKY = "w"
            ANCHOR = "e"
            
        if extratitleline:
            titlerow=0
            valuerow=1
            titlecolumn=0
            valuecolumn=0
            deltarow = 2
            deltacolumn = 1
        else:
            titlerow = 0
            valuerow = 0
            titlecolumn = 0
            valuecolumn = 1
            deltarow = 1
            deltacolumn = 2
        
        column = 0
        row = startrow
    
        for paramkey in macroparams:
            if not paramkey.startswith("!"):
                paramconfig_dict = self.MacroParamDef.data.get(paramkey,{})
                param_min = paramconfig_dict.get("Min",0)
                param_max = paramconfig_dict.get("Max",255)
                param_title = paramconfig_dict.get("Input Text","")
                param_tooltip = paramconfig_dict.get("Hint","")
                param_persistent = (paramconfig_dict.get("Persistent","False") == "True")
                param_configname = paramconfig_dict.get("ConfigName",paramkey)
                param_default = paramconfig_dict.get("Default","")
                param_allow_value_entry = (paramconfig_dict.get("AllowValueEntry","False") == "True")
                param_hide = (paramconfig_dict.get("Hide","False") == "True")
                param_value_change_event = (paramconfig_dict.get("ValueChangeEvent","False") == "True")
                param_value_scrollable = (paramconfig_dict.get("Scrollable","False") == "True")
                param_label_width = int(paramconfig_dict.get("ParamLabelWidth",PARAMLABELWIDTH))
                param_entry_width = int(paramconfig_dict.get("ParamEntryWidth",PARAMENTRWIDTH))
                param_description = paramconfig_dict.get("ParamDescription","")
                param_descLines  = int(paramconfig_dict.get("ParamDescLines","0"))
                
                if param_persistent:
                    configData = self.getConfigData(paramkey)
                    if configData != "":
                        param_default = configData
                param_readonly = (paramconfig_dict.get("ReadOnly","False") == "True")
                param_type = paramconfig_dict.get("Type","")
        
                if param_title == "":
                    param_title = paramkey
                    
                if param_description != "":
                    
                    paramdescriptionlabel = tk.Text(parent_frame, wrap='word', height=param_descLines, bg=self.cget('bg'), font=self.fontlabel)
                    paramdescriptionlabel.delete("1.0", "end")
                    paramdescriptionlabel.insert("end", param_description)
                    paramdescriptionlabel.yview("1.0")
                    paramdescriptionlabel.config(state = tk.DISABLED)
                    paramdescriptionlabel.grid(row=row+valuerow, column=column+titlecolumn, columnspan=2, padx=10, pady=10,sticky="ew")
                    column = column + deltacolumn
                    if column > maxcolumns:
                        column = 0
                        row=row+deltarow
                    
                    
                if param_type == "": # number value param
                    
                    label=tk.Label(parent_frame, text=param_title,width=PARAMLABELWIDTH,wraplength = PARAMLABELWRAPL,anchor=ANCHOR,font=self.fontlabel)
                    label.grid(row=row+titlerow, column=column+titlecolumn, sticky=STICKY, padx=2, pady=2)
                    self.ToolTip(label, text=param_tooltip)
                    if param_max == "":
                        param_max = 255
                    paramvar = LimitVar(param_min, param_max, parent_frame)
                    paramvar.set(param_default)
                    paramvar.key = paramkey
                    
                    if param_value_change_event:
                        s_paramvar = Spinbox(parent_frame, from_=param_min, to=param_max, width=PARAMSPINBOXWIDTH, name='spinbox', textvariable=paramvar,font=self.fontspinbox,command=lambda:self._update_value(macro,paramkey))
                    else:
                        s_paramvar = Spinbox(parent_frame, from_=param_min, to=param_max, width=PARAMSPINBOXWIDTH, name='spinbox', textvariable=paramvar,font=self.fontspinbox)

                    s_paramvar.delete(0, 'end')
                    s_paramvar.insert(0, param_default)
                    s_paramvar.grid(row=row+valuerow, column=column+valuecolumn, padx=2, pady=2, sticky=STICKY)
                    s_paramvar.key = paramkey
                    
                    param_bind_up   = paramconfig_dict.get("Key_Up","")
                    param_bind_down = paramconfig_dict.get("Key_Down","")
                    
                    if param_bind_up != "":
                        self.bind(param_bind_up,s_paramvar.invoke_buttonup)
                        s_paramvar.key_up=param_bind_up
                        if self.bind_keys_dict.get(macro,{})=={}:
                            self.bind_keys_dict[macro] = {}
                        self.bind_keys_dict[macro][paramkey] = s_paramvar
                    if param_bind_down != "":    
                        self.bind(param_bind_down,s_paramvar.invoke_buttondown)
                        s_paramvar.key_down=param_bind_down
                        self.bind_keys_dict[macro][paramkey] = s_paramvar
                
                    self.set_macroparam_var(macro, paramkey, paramvar,persistent=param_persistent)
                    
                    column = column + deltacolumn
                    if column > maxcolumns:
                        column = 0
                        row=row+deltarow                    
                    
                elif param_type == "Time": # Time value param
                    
                    label=tk.Label(parent_frame, text=param_title,width=PARAMLABELWIDTH,height=2,wraplength = PARAMLABELWRAPL,anchor=ANCHOR,font=self.fontlabel)
                    label.grid(row=row+titlerow, column=column+titlecolumn, sticky=STICKY, padx=2, pady=2)
                    self.ToolTip(label, text=param_tooltip)
                    
                    
                    paramvar = tk.Entry(parent_frame,width=PARAMENTRWIDTH,font=self.fontentry)
                    paramvar.delete(0, 'end')
                    paramvar.insert(0, param_default)
                    paramvar.grid(row=row+valuerow, column=column+valuecolumn, sticky=STICKY, padx=2, pady=2)
                    paramvar.key = paramkey
                
                    self.set_macroparam_var(macro, paramkey, paramvar)                
        
                    column = column + deltacolumn
                    if column > maxcolumns:
                        column = 0
                        row=row+deltarow      
                        
                elif param_type == "String": # String value param
                    
                    label=tk.Label(parent_frame, text=param_title,width=PARAMLABELWIDTH,height=2,wraplength = PARAMLABELWRAPL,anchor=ANCHOR,font=self.fontlabel)
                    label.grid(row=row+titlerow, column=column+titlecolumn, sticky=STICKY, padx=2, pady=2)
                    self.ToolTip(label, text=param_tooltip)
                    
                    
                    paramvar = tk.Entry(parent_frame,width=PARAMENTRWIDTH,font=self.fontentry)
                         
                    if param_value_change_event:
                        paramvar.bind("<Return>",self._key_return)                
    
                    paramvar.delete(0, 'end')
                    paramvar.insert(0, param_default)
                    paramvar.grid(row=row+valuerow, column=column+valuecolumn, sticky=STICKY, padx=2, pady=2)
                    paramvar.key = paramkey
                    paramvar.macro = macro
                    
                    self.set_macroparam_var(macro, paramkey, paramvar)                
        
                    column = column + deltacolumn
                    if column > maxcolumns:
                        column = 0
                        row=row+deltarow
                
                elif param_type == "BigEntry": # Text value param
                    
                    label=tk.Label(parent_frame, text=param_title,width=PARAMLABELWIDTH,height=2,wraplength = PARAMLABELWRAPL,font=self.fontlabel)
                    label.grid(row=row+titlerow, column=column+titlecolumn, sticky=STICKY, padx=2, pady=2)
                    self.ToolTip(label, text=param_tooltip)
                    paramvar = tk.Entry(parent_frame,width=param_entry_width*3,font=self.fontentry)
                    
                    if param_value_change_event:
                        paramvar.bind("<Return>",self._key_return)
                                        
                    paramvar.delete(0, 'end')
                    paramvar.insert(0, param_default)
                    paramvar.grid(row=row+valuerow, column=column+valuecolumn, sticky=STICKY, padx=2, pady=2)
                    paramvar.key = paramkey
                    paramvar.macro = macro
                
                    self.set_macroparam_var(macro, paramkey, paramvar)                
    
                    column = column + deltacolumn
                    if column > maxcolumns:
                        column = 0
                        row=row+deltarow            
                
                elif param_type == "Text": # Text value param
                    if not param_hide:
                        label=tk.Label(parent_frame, text=param_title,width=PARAMLABELWIDTH,height=2,wraplength = PARAMLABELWRAPL,anchor=ANCHOR,font=self.fontlabel)
                        label.grid(row=row+titlerow, column=column+titlecolumn, sticky=STICKY, padx=2, pady=2)
                        self.ToolTip(label, text=param_tooltip)
                    
                    number_of_lines = paramconfig_dict.get("Lines","")
                    if number_of_lines == "":
                        number_of_lines = "2"
                        
                    if param_value_scrollable:
                        paramvar = tk.scrolledtext.ScrolledText(parent_frame,bg=self.cget('bg'),width=PARAMENTRWIDTH*5,height=int(number_of_lines),font=self.fonttext)
                    else:
                        paramvar = tk.Text(parent_frame,width=PARAMENTRWIDTH*5,bg=self.cget('bg'),height=int(number_of_lines),font=self.fonttext)
                    
                    paramvar.delete("1.0", "end")
                    paramvar.insert("end",param_default)
                    if not param_hide:
                        paramvar.grid(row=row+valuerow, column=column+valuecolumn, sticky=STICKY, padx=2, pady=2)
                    paramvar.key = paramkey
                    
                    if param_readonly:
                        paramvar.state = "disabled"
                
                    self.set_macroparam_var(macro, paramkey, paramvar)                
        
                    column = column + deltacolumn
                    if column > maxcolumns:
                        column = 0
                        row=row+deltarow
                        
                elif param_type == "Checkbutton": # Checkbutton param
                    paramvar = tk.IntVar()
                    paramvar.key = paramkey
                     
                    label=tk.Checkbutton(parent_frame, text=param_title,width=PARAMLABELWIDTH*2,wraplength = PARAMLABELWRAPL*2,variable=paramvar,font=self.fontlabel)
                    label.grid(row=row+valuerow, column=column, columnspan=2,sticky=STICKY, padx=2, pady=2)
                    self.ToolTip(label, text=param_tooltip)                
                
                    self.set_macroparam_var(macro, paramkey, paramvar)                
        
                    column = column + deltacolumn
                    if column > maxcolumns:
                        column = 0
                        row=row+deltarow
        
                    
                elif param_type == "Combo": # Combolist param
                    
                    if not param_hide:
                        label=tk.Label(parent_frame, text=param_title,width=PARAMLABELWIDTH,height=2,wraplength = PARAMLABELWRAPL,anchor=ANCHOR,font=self.fontlabel)
                        label.grid(row=row+titlerow, column=column+titlecolumn, sticky=STICKY, padx=2, pady=2)
                        self.ToolTip(label, text=param_tooltip)
                    
                    if param_allow_value_entry:
                        paramvar = ttk.Combobox(parent_frame, width=PARAMCOMBOWIDTH,font=self.fontlabel)
                    else:                
                        paramvar = ttk.Combobox(parent_frame, state="readonly", width=PARAMCOMBOWIDTH,font=self.fontlabel)
                    combo_value_list = paramconfig_dict.get("KeyValues",paramconfig_dict.get("Values",[]))
                    combo_text_list = paramconfig_dict.get("ValuesText",[])
                    
                    if combo_text_list == []:
                        paramvar["value"] = combo_value_list
                    else:
                        paramvar["value"] = combo_text_list
                        
                    paramvar.current(0) #set the selected view                    
                    
                    if not param_hide:
                        paramvar.grid(row=row+valuerow, column=column+valuecolumn, sticky=STICKY, padx=2, pady=2)
                    paramvar.key = paramkey
                    paramvar.keyvalues = combo_value_list
                    paramvar.textvalues = combo_text_list
                
                    self.set_macroparam_var(macro, paramkey, paramvar)               
        
                    column = column + deltacolumn
                    if column > maxcolumns:
                        column = 0
                        row=row+deltarow      
                        
                elif param_type == "GroupCombo": # Combolist param
                    
                    label=tk.Label(parent_frame, text=param_title,width=PARAMLABELWIDTH,height=2,wraplength = PARAMLABELWRAPL,anchor=ANCHOR,font=self.fontlabel)
                    label.grid(row=row+titlerow, column=column+titlecolumn, sticky=STICKY, padx=2, pady=2)
                    self.ToolTip(label, text=param_tooltip)
                    
                    paramvar = ttk.Combobox(parent_frame, width=PARAMCOMBOWIDTH,postcommand=self.update_GroupComboValues,font=self.fontlabel)
                    combo_value_list = list(self.ledeffecttable.mledgrouptable.keys())
                    combo_text_list = []
                    
                    if combo_text_list == []:
                        paramvar["value"] = combo_value_list
                    else:
                        paramvar["value"] = combo_text_list
                        
                    paramvar.current(0) #set the selected view                    
                    
                    paramvar.grid(row=row+valuerow, column=column+valuecolumn, sticky=STICKY, padx=2, pady=2)
                    paramvar.key = paramkey
                    paramvar.keyvalues = combo_value_list
                    paramvar.textvalues = combo_text_list
                    paramvar.bind("<<ComboboxSelected>>", self.GroupComboSelected)
                
                    self.set_macroparam_var(macro, paramkey, paramvar)               
        
                    column = column + deltacolumn
                    if column > maxcolumns:
                        column = 0
                        row=row+deltarow                          
                        
                elif param_type == "CX": # Channel value param
                    
                    label=tk.Label(parent_frame, text=param_title,width=PARAMLABELWIDTH,height=2,wraplength = PARAMLABELWRAPL,anchor=ANCHOR,font=self.fontlabel)
                    label.grid(row=row+titlerow, column=column+titlecolumn, sticky=STICKY, padx=2, pady=2)
                    self.ToolTip(label, text=param_tooltip)
                    
                    paramvar = ttk.Combobox(parent_frame, width=PARAMCOMBOWIDTH,font=self.fontlabel)
                    
                    combo_value_list = paramconfig_dict.get("KeyValues",paramconfig_dict.get("Values",("C_All", "C12", "C23", "C1", "C2", "C3", "C_RED", "C_GREEN", "C_BLUE", "C_WHITE", "C_YELLOW", "C_CYAN")))
                    combo_text_list = paramconfig_dict.get("ValuesText",[])
                    
                    if combo_text_list == []:
                        paramvar["value"] = combo_value_list
                    else:
                        paramvar["value"] = combo_text_list                    
                    
                    paramvar.current(0) #set the selected colorview                    
                    
                    paramvar.grid(row=row+valuerow, column=column+valuecolumn, columnspan=1, sticky=STICKY, padx=2, pady=2)
                    paramvar.key = paramkey
                    paramvar.keyvalues = combo_value_list
                    paramvar.textvalues = combo_text_list
                
                    self.set_macroparam_var(macro, paramkey, paramvar)                
        
                    column = column + deltacolumn
                    if column > maxcolumns:
                        column = 0
                        row=row+deltarow      
                
        
                elif param_type == "Multipleparams": # Multiple params
                    logging.info ("%s - %s",macro,param_type)
                    if row >1 or column>0: 
                        row += deltarow
                        column = 0
                    
                    label=tk.Label(parent_frame, text=param_title,width=PARAMLABELWIDTH,height=2,wraplength = PARAMLABELWRAPL,anchor=ANCHOR,font=self.fontlabel)
                    label.grid(row=row+titlerow, column=column+titlecolumn, rowspan=2, sticky=STICKY, padx=2, pady=2)
                    self.ToolTip(label, text=param_tooltip)
                    
                    repeat_number = paramconfig_dict.get("Repeat","")
                    
                    if repeat_number == "":
                    
                        multipleparam_frame = ttk.Frame(parent_frame)
                        multipleparam_frame.grid(row=row,column=column+1 ,columnspan=6,sticky='nesw', padx=0, pady=0)
                        
                        multipleparams = paramconfig_dict.get("MultipleParams",[])
                        
                        if multipleparams != []:
                            if style != "CONFIGPage":
                                self.create_macroparam_content(multipleparam_frame,macro, multipleparams,extratitleline=extratitleline,maxcolumns=maxcolumns-1,minrow=0,style=style,generic_methods=generic_methods)
                                separator = ttk.Separator (parent_frame, orient = tk.HORIZONTAL)
                                separator.grid (row = row+2, column = 0, columnspan= 10, padx=2, pady=2, sticky = "ew")
                            else:
                                self.create_macroparam_content(multipleparam_frame,macro, multipleparams,extratitleline=extratitleline,maxcolumns=6,minrow=0,style=style,generic_methods=generic_methods)
                                
               
                        column = 0
                        row=row+3
                        
                    else:
                        repeat_number_int = int(repeat_number)
                        
                        repeat_max_columns = 10
                        
                        for i in range(repeat_number_int):
                            repeat_macro=macro+"."+paramkey+"."+str(i)
    
                            multipleparam_frame = ttk.Frame(parent_frame)
                            multipleparam_frame.grid(row=row,column=column+1 ,columnspan=10,sticky='nesw', padx=0, pady=0)
                            
                            multipleparams = paramconfig_dict.get("MultipleParams",[])
                            
                            if multipleparams != []:
                                self.create_macroparam_content(multipleparam_frame,repeat_macro, multipleparams,extratitleline=extratitleline,maxcolumns=repeat_max_columns,minrow=0,style=style,generic_methods=generic_methods)
                   
                            column = 0
                            row=row+1
                    
                elif param_type == "ChooseColor": # Color value param
                    
                    self.colorlabel = tk.Button(parent_frame, text=param_title, width=param_label_width, height=2, padx=2, pady=2, wraplength=PARAMLABELWRAPL,relief="raised", background=param_default,borderwidth=1,font=self.fontbutton,command=lambda macrokey=macro,paramkey=paramkey: self.choosecolor(macrokey=macrokey,paramkey=paramkey))
                    #label=tk.Label(parent_frame, text=param_title,width=PARAMLABELWIDTH,height=2,wraplength = PARAMLABELWRAPL,bg=param_default,borderwidth=1)
                    self.colorlabel.grid(row=row+titlerow, column=column+titlecolumn, sticky=STICKY, padx=2, pady=2)
                    self.ToolTip(self.colorlabel, text=param_tooltip)
                    
                    paramvar_strvar = tk.StringVar()
                    paramvar_strvar.set("")                    
                    paramvar = tk.Entry(parent_frame,width=PARAMENTRWIDTH,font=self.fontentry,textvariable=paramvar_strvar)
                    paramvar.delete(0, 'end')
                    paramvar.insert(0, param_default)
                    paramvar.grid(row=row+valuerow, column=column+valuecolumn, sticky=STICKY, padx=2, pady=2)
                    paramvar_strvar.key = paramkey
                    paramvar_strvar.macro = macro
                    paramvar_strvar.button = self.colorlabel
                    paramvar_strvar.trace_add("write", lambda nm, indx, mode,macrokey=macro,paramkey=paramkey: self.colorvar_changed(nm,indx,mode,macrokey=macrokey,paramkey=paramkey)) #self.colorvar_changed)
                
                    self.set_macroparam_var(macro, paramkey, paramvar_strvar)                
        
                    column = column + deltacolumn
                    if column > maxcolumns:
                        column = 0
                        row=row+deltarow
                        
                elif param_type == "ChooseFileName": # parameter AskFileName
                    
                    self.filechooserlabel = tk.Button(parent_frame, text=param_title, width=param_label_width, height=2, padx=2, pady=2, wraplength=PARAMLABELWRAPL, font=self.fontbutton,command=lambda macrokey=macro,paramkey=paramkey: self.choosefilename(macrokey=macrokey,paramkey=paramkey))
                    #label=tk.Label(parent_frame, text=param_title,width=PARAMLABELWIDTH,height=2,wraplength = PARAMLABELWRAPL,bg=param_default,borderwidth=1)
                    self.filechooserlabel.grid(row=row+titlerow, column=column+titlecolumn, sticky=STICKY, padx=10, pady=10)
                    self.ToolTip(self.filechooserlabel, text=param_tooltip)
                    
                    paramvar_strvar = tk.StringVar()
                    paramvar_strvar.set("")
                    paramvar = tk.Entry(parent_frame,width=param_entry_width,font=self.fontentry,textvariable=paramvar_strvar)
                    paramvar.delete(0, 'end')
                    paramvar.insert(0, param_default)
                    paramvar.grid(row=row+valuerow, column=column+valuecolumn, sticky=STICKY, padx=2, pady=2)
                    paramvar_strvar.key = paramkey
                    paramvar_strvar.filetypes = paramconfig_dict.get("FileTypes","*")
                    paramvar_strvar.text = param_title
                
                    self.set_macroparam_var(macro, paramkey, paramvar_strvar)                
        
                    column = column + deltacolumn
                    if column > maxcolumns:
                        column = 0
                        row=row+deltarow                
                        
                elif param_type == "Button": # Text value param
                    
                    number_of_lines = paramconfig_dict.get("Lines","")
                    if number_of_lines == "":
                        number_of_lines = "2"
                    button_function = paramconfig_dict.get("Function","")
                        
                    button=tk.Button(parent_frame, text=param_title,width=PARAMLABELWIDTH,height=number_of_lines,wraplength = PARAMLABELWRAPL,font=self.fontbutton,command=lambda macrokey=macro,button=button_function: self._button_cmd(macrokey=macrokey,button=button))
                    button.grid(row=row+titlerow, column=column+titlecolumn, sticky=STICKY, padx=2, pady=2)
                    self.ToolTip(button, text=param_tooltip)
                    #self.buttonlist.append(self.button)
                    
                    column = column + deltacolumn
                    if column > maxcolumns:
                        column = 0
                        row=row+deltarow
                        
                elif param_type == "ColTab": # Color value param
                    
                    self.coltablabel = tk.Button(parent_frame, text=param_title, width=PARAMLABELWIDTH, height=2, wraplength=PARAMLABELWRAPL,relief="raised", borderwidth=1,command=self.checkcolor,font=self.fontbutton)
                    #label=tk.Label(parent_frame, text=param_title,width=PARAMLABELWIDTH,height=2,wraplength = PARAMLABELWRAPL,bg=param_default,borderwidth=1)
                    self.coltablabel.grid(row=row+titlerow, column=column+titlecolumn, sticky=STICKY, padx=2, pady=2)
                    self.ToolTip(self.coltablabel, text=param_tooltip)
                    
                    #paramvar = tk.Entry(parent_frame,width=PARAMENTRWIDTH)
                    #paramvar.delete(0, 'end')
                    #paramvar.insert(0, param_default)
                    #paramvar.grid(row=row+valuerow, column=column+valuecolumn, sticky=STICKY, padx=2, pady=2)
                    #paramvar.key = paramkey
                
                    #self.set_macroparam_var(macro, paramkey, paramvar)
                    
                    self.create_color_palette(parent_frame)
    
                    column = 0
                    row=row + 4
                        
                elif param_type == "Var": # Combolist param
                    
                    label=tk.Label(parent_frame, text=param_title,width=PARAMLABELWIDTH,height=2,wraplength = PARAMLABELWRAPL,font=self.fontlabel)
                    label.grid(row=row+titlerow, column=column+titlecolumn, sticky=STICKY, padx=2, pady=2)
                    self.ToolTip(label, text=param_tooltip)
                    
                    if param_allow_value_entry:
                        paramvar = ttk.Combobox(parent_frame, width=PARAMCOMBOWIDTH,font=self.fontlabel)
                    else:                
                        paramvar = ttk.Combobox(parent_frame, state="readonly", width=PARAMCOMBOWIDTH,font=self.fontlabel)                
                    
                    combo_value_list = paramconfig_dict.get("KeyValues",paramconfig_dict.get("Values",[]))
                    combo_text_list = paramconfig_dict.get("ValuesText",[])
                    
                    if combo_text_list != []:
                        paramvar["value"] = combo_text_list
                    elif combo_value_list != []:
                        paramvar["value"] = combo_value_list
                    else:
                        paramvar["value"] = ["Variable"]
                        
                    paramvar.current(0) #set the selected view                    
                    
                    paramvar.grid(row=row+valuerow, column=column+valuecolumn, sticky=STICKY, padx=2, pady=2)
                    paramvar.key = paramkey
                    paramvar.keyvalues = combo_value_list
                    paramvar.textvalues = combo_text_list
                
                    self.set_macroparam_var(macro, paramkey, paramvar)
    
                    column = column + deltacolumn
                    if column > maxcolumns:
                        column = 0
                        row=row+deltarow
                        
                elif param_type == "Generic": # call generic function
                    logging.info ("%s - %s",macro,param_type)
                                        
                    generic_widget_frame = ttk.Frame(parent_frame)
                    generic_widget_frame.grid(row=row,column=column ,columnspan=6,sticky='nesw', padx=0, pady=0)
                    generic_widget_frame.columnconfigure(0,weight=1)
                    generic_widget_frame.rowconfigure(0,weight=1)
                    
                    generic_method_name = paramconfig_dict.get("GenericMethod","")
                    
                    if generic_method_name != "" and generic_methods != {}:
                        generic_methods[generic_method_name](generic_widget_frame,macro,macroparams)
                    else:
                        raise Exception("Method %s not implemented" % generic_method_name)
                    
                    column = 0
                    row=row+deltarow                    
                        
                    
                
                if param_readonly:
                    paramvar.state = "DISABLED"            
            
            #if (column<maxcolumns+1) and (column>0):
            #    for i in range(column,maxcolumns+1):
            #        label=tk.Label(parent_frame, text=" ",width=PARAMLABELWIDTH,height=2,wraplength = PARAMLABELWRAPL)
            #        label.grid(row=row,column=i,sticky=STICKY, padx=2, pady=2)
            
            if maxcolumns > 6:        
                seplabel=tk.Label(parent_frame, text="",width=90,height=1)
                seplabel.grid(row=row+2, column=0, columnspan=10,sticky='ew', padx=2, pady=2)
    
    def create_macroparam_frame(self,parent_frame, macro, extratitleline=False,maxcolumns=5, startrow=0, minrow=4,style="MACROPage",generic_methods={}):
        
        MACROLABELWIDTH = 15
        MACRODESCWIDTH = 20
        MACRODESCWRAPL = 120
        BUTTONLABELWIDTH = 10
        
        PARAMFRAMEWIDTH = 105
        
        PARAMLABELWIDTH = 15
        PARAMLABELWRAPL = 100        
        
        PARAMSPINBOXWIDTH = 4
        PARAMENTRWIDTH = 8
        PARAMCOMBOWIDTH = 16
        
        macroparam_frame = ttk.Frame(parent_frame, relief="ridge", borderwidth=1)
        self.macroparam_frame_dict[macro] = macroparam_frame
    
        macrodata = self.MacroDef.data.get(macro,{})
        Macrotitle = macro
        
        Macrolongdescription = macrodata.get("Ausführliche Beschreibung","")
        Macrodescription = macrodata.get("Kurzbeschreibung","")
        Macrodescriptionlines = int(macrodata.get("MacroDescLines","5"))
        
        if Macrolongdescription =="":
            Macrolongdescription = Macrodescription
        macroldlabel = tk.Text(macroparam_frame, wrap='word', bg=self.cget('bg'), borderwidth=2,relief="ridge",width=108,height=Macrodescriptionlines,font=self.fontlabel)
        
        macroldlabel.delete("1.0", "end")
        macroldlabel.insert("end", Macrolongdescription)
        macroldlabel.yview("1.0")
        macroldlabel.config(state = tk.DISABLED)
        
        if style == "MACROPage":
            macroldlabel.grid(row=4, column=0, columnspan=2,padx=0, pady=0,sticky="w")
            macrolabel = tk.Button(macroparam_frame, text=Macrotitle, width=MACROLABELWIDTH, height=2, wraplength=150,relief="raised", background="white",borderwidth=1,command=lambda: self._macro_cmd(macrokey=macro))
            macrolabel.grid(row=1, column=0, sticky="nw", padx=4, pady=4)
            macrolabel.key=macro
            self.ToolTip(macrolabel, text=Macrodescription)
        else:
            macroldlabel.grid(row=0, column=0, columnspan=2,padx=10, pady=10,sticky="we",)
       
        macrotype = macrodata.get("Typ","")
        if macrotype =="ColTab":
            macroparams = []
        else:       
            macroparams = macrodata.get("Params",[])
        
        if macroparams:
            param_frame = ttk.Frame(macroparam_frame) #,borderwidth=1,relief="ridge")
                                  
            self.create_macroparam_content(param_frame,macro, macroparams,extratitleline=extratitleline,maxcolumns=maxcolumns,startrow=startrow,style=style,generic_methods=generic_methods)
    
            param_frame.grid(row=1,column=1,rowspan=2,padx=0, pady=0,sticky="nw")
    
        return macroparam_frame
    
    def get_macrodef_data(self, macro, param):
        macrodata = self.MacroDef.data.get(macro,{})
        if macrodata != {}:
            value = macrodata.get(param,"")
        else:
            value = ""
        return value
        
    
    def determine_filepath(filename_key):
        #macrodata = self.MacroDef.data.get("StartPage",{})
        #filename = macrodata.get(filename_key,"")
        filename = self.get_macrodef_data("StartPage",filename_key)
        filedir = self.mainfile_dir
        filepath1 = os.path.join(filedir, filename)
        filepath = os.path.normpath(filepath1)
        return filepath

    def _button_cmd(self, macrokey="",button=""):
        """Respond to user click on a button"""
        logging.debug("Button Pressed: %s - %s",macrokey,button)
        page_frame = self.getFramebyName(macrokey)
        if page_frame:        
            button_command = "page_frame" + "." +button+"()"
            eval(button_command)
 
    def determine_fg_color(self,hex_str):
        '''
        Input a string without hash sign of RGB hex digits to compute
        complementary contrasting color such as for fonts
        '''
        
        (r, g, b) = (hex_str[1:3], hex_str[3:5], hex_str[5:])
        return '#000000' if 1 - (int(r, 16) * 0.299 + int(g, 16) * 0.587 + int(b, 16) * 0.114) / 255 < 0.5 else '#ffffff'        
    
    def setbuttoncolor(self,color):
        color_fg = self.determine_fg_color(color)
        self.colorlabel.config(bg=color,fg=color_fg)
        paramvar = self.macroparams_var["Group"]["Group_Colour"]
        paramvar.delete(0, 'end')
        paramvar.insert(0, color)    
    
    def choosecolor(self,paramkey="",macrokey=""):
        paramvar = self.macroparams_var[macrokey][paramkey]
        old_color=paramvar.get()        
        color = colorchooser.askcolor(color=old_color)
        
        if color:
            colorhex = color[1]
            color_fg = self.determine_fg_color(colorhex)
            paramvar.button.config(bg=colorhex,fg=color_fg)
            paramvar = self.macroparams_var[macrokey][paramkey]
            paramvar.set(colorhex)
            #paramvar.delete(0, 'end')
            #paramvar.insert(0, colorhex) 
    
    def colorvar_changed(self,var,indx,mode,macrokey="",paramkey=""):
        #print("colorvar_changed",var,indx,mode)
        paramvar = self.macroparams_var[macrokey][paramkey]
        color = paramvar.get()
        buttonlabel=paramvar.button
        if color == "":
            color="black"
        try:
            buttonlabel.configure(background=color)
        except:
            buttonlabel.configure(background="black")


    def choosefilename(self,paramkey="",macrokey=""):
        paramvar_strvar = self.macroparams_var[macrokey][paramkey]
        old_filename=paramvar_strvar.get()
        filetypes_str = paramvar_strvar.filetypes
        filetypes_split = filetypes_str.split(",")
        i = 0
        filetype_tuple = []
        filetype_list = []
        for text in filetypes_split:
            filetype_tuple.append(text)
            if (i%2)==1:
                filetype_list.append(filetype_tuple)
                filetype_tuple = []
            i+=1
        filename = filedialog.askopenfilename(title=paramvar_strvar.text,initialfile=old_filename,filetypes=filetype_list) # ("Zusi-Master-Fahrplan","*.fpn"),("all files","*.*")
        if filename != "":
            paramvar_strvar.set(filename)
            #paramvar.delete(0, 'end')
            #paramvar.insert(0, filename)
            
    def set_string_variable(self,inputtext, paramkey="", macrokey=""):
        paramvar = self.macroparams_var[macrokey][paramkey]
        if inputtext != "":
            paramvar.set(inputtext)

    def _key_return(self,event=None):
        
        param = event.widget
        self._update_value(param.macro,param.key)

    def _update_value(self,macro,paramkey):
        logging.info("update_value: %s - %s",macro,paramkey)
        tabframe=self.getFramebyName(macro)
        if tabframe!=None:
            tabframe._update_value(paramkey)

def img_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


#-------------------------------------------

if sys.hexversion < 0x30700F0:
    tk.messagebox.showerror("Wrong Python Version","You need Python Version > 3.7 to run this Program")
    exit()
    

COMMAND_LINE_ARG_DICT = {}

parser = argparse.ArgumentParser(description='Generate a Timetablegraph for ZUSI timetables')
parser.add_argument('--loglevel',choices=["DEBUG","INFO","WARNING","ERROR","CRITICAL"],help="Logginglevel to be printed inot the logfile")
parser.add_argument('--logfile',help="Logfilename")
parser.add_argument('--startpage',choices=['StartPage', 'StationsConfigurationPage', 'ConfigurationPage'],help="Name of the first page shown after start")
args = parser.parse_args()

format = "%(asctime)s: %(message)s"

filedir = os.path.dirname(os.path.realpath(__file__))
if args.logfile:
    logfilename1=args.logfile
else:
    logfilename1=LOG_FILENAME
    
if logfilename1 == "stdout":
    logfilename=""
else:
    logfilename = os.path.join(filedir, logfilename1)

if args.loglevel:
    logging_level = args.loglevel.upper()
    if logging_level=="DEBUG":
        logging.basicConfig(format=format, filename=logfilename,filemode="w",level=logging.DEBUG,datefmt="%H:%M:%S")
    elif logging_level=="INFO":
        logging.basicConfig(format=format, filename=logfilename,filemode="w",level=logging.INFO,datefmt="%H:%M:%S")
    elif logging_level=="WARNING":
        logging.basicConfig(format=format, filename=logfilename,filemode="w",level=logging.WARNING,datefmt="%H:%M:%S")
    elif logging_level=="ERROR":
        logging.basicConfig(format=format, filename=logfilename,filemode="w",level=logging.ERROR,datefmt="%H:%M:%S")
    else:
        logging.basicConfig(format=format, filename=logfilename,filemode="w",level=logging.CRITICAL,datefmt="%H:%M:%S")
else:
    logging.basicConfig(format=format, filename=logfilename,filemode="w",level=logging.DEBUG,datefmt="%H:%M:%S")

logging.info("MLL Proggenerator started %s", PROG_VERSION)
logging.info(" Platform: %s",platform.platform())
logging.debug("Installationfolder %s",filedir)

if args.startpage:
    COMMAND_LINE_ARG_DICT["startpagename"]=args.startpage
else:
    COMMAND_LINE_ARG_DICT["startpagename"]="StartPage"

app = TimeTableGraphMain()

app.setroot(app)

app.protocol("WM_DELETE_WINDOW", app.cancel)

app.startup_system()

app.mainloop()


