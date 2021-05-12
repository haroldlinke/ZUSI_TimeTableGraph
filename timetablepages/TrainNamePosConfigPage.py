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


from timetablepages.ConfigPageTemplate import ConfigPagetemplate

# ----------------------------------------------------------------
# Class ConfigurationPage
# ----------------------------------------------------------------
class TrainNamePosConfigPage(ConfigPagetemplate):

    def __init__(self, parent, controller):
        
        self.tabClassName = "TrainNamePosConfigPage"
        super().__init__(parent, controller, self.tabClassName) 
        
        return
    
    def button2_command(self):
        print("Alle Tabelleneinträge entfernen")
        
        paramconfig_dict = self.controller.MacroParamDef.data.get("TrainNamePosProp",{})
        mp_repeat  = paramconfig_dict.get("Repeat","")
        repeat_var = paramconfig_dict.get("RepeatVar","")
        if repeat_var != "":
            repeat_var_value  = self.controller.getConfigData(repeat_var)
            if repeat_var_value != None and repeat_var_value != "":
                mp_repeat = repeat_var_value         
        for i in range(int(mp_repeat)):
            #self.controller.setConfigData_multiple("TrainNamePos_Stops","TrainNamePosProp",i,"")
            #self.controller.setConfigData_multiple("TrainNamePos_Names","TrainNamePosProp",i,"")
            
            mp_macro = "TrainNamePosConfigPage"+"." + "TrainNamePosProp" + "." + str(i)
            self.controller.set_macroparam_val(mp_macro, "TrainNamePos_Stops", "")
            self.controller.set_macroparam_val(mp_macro, "TrainNamePos_Names", "")
            
    def ButtonPlus(self,macrokey=""):
        print("Button PLus")
        
    def ButtonMinus(self,macrokey=""):
        print("Button Minus")        
