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

from timetablepages.ZUSI_timetablegraph_main import main
import os

def main_entry():
    mainfile_dir = os.path.dirname(os.path.realpath(__file__))
    pythonfile_name = os.path.basename(os.path.realpath(__file__))
    pythonfile_pathame = os.path.join(os.path.dirname(mainfile_dir),pythonfile_name)
    execfile_pathame = os.path.splitext(pythonfile_pathame)[0]+".exe"
    main(mainfile_dir,execfile_pathame)

if __name__ == "__main__":
    mainfile_dir = os.path.dirname(os.path.realpath(__file__))
    pythonfile_name = os.path.basename(os.path.realpath(__file__))
    pythonfile_pathame = os.path.join(os.path.dirname(mainfile_dir),pythonfile_name)
    execfile_pathame = os.path.splitext(pythonfile_pathame)[0]+".exe"
    main(mainfile_dir,execfile_pathame)

