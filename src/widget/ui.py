#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 smallevilbeast
#
# Author:     smallevilbeast <houshao55@gmail.com>
# Maintainer: smallevilbeast <houshao55@gmail.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import gtk

from dtk.ui.utils import alpha_color_hex_to_cairo
from dtk.ui.line import draw_vlinear
from dtk.ui.draw import draw_text
from dtk.ui.line import HSeparator
from widget.skin import app_theme

def set_widget_gravity(widget, gravity=(0, 0, 0, 0), paddings=(0, 0, 0, 0)):
    align = gtk.Alignment()
    align.set(*gravity)
    align.set_padding(*paddings)
    align.add(widget)
    return align

def create_right_align():    
    align = gtk.Alignment()
    align.set(0, 0, 0, 1)
    return align
    
def create_left_align():
    align = gtk.Alignment()
    align.set(0, 0, 1, 0)
    return align
    
def create_upper_align():
    align = gtk.Alignment()
    align.set(1, 0, 0, 0)
    return align

def create_bottom_align():
    align = gtk.Alignment()
    align.set(0, 1, 0, 0)
    return align


def set_widget_center(widget):
    hbox = gtk.HBox()
    hbox.pack_start(create_right_align(), False, True)
    hbox.pack_start(widget, False, False)
    hbox.pack_start(create_left_align(), False, True)
    return hbox

def set_widget_left(widget):
    hbox = gtk.HBox()
    hbox.pack_start(widget, False, False)
    hbox.pack_start(create_left_align(), False, True)
    return hbox
    
def container_remove_all(container):
    ''' Removee all child widgets for container. '''
    container.foreach(lambda widget: container.remove(widget))

def switch_tab(notebook_box, tab_box):
    '''Switch tab 1.'''
    container_remove_all(notebook_box)
    notebook_box.add(tab_box)
    notebook_box.show_all()

def draw_alpha_mask(cr, x, y, width, height, color_name, radius):
    if not isinstance(color_name, tuple):
        color_info = app_theme.get_alpha_color(color_name).get_color_info()
    else:    
        color_info = color_name
    cr.set_source_rgba(*alpha_color_hex_to_cairo(color_info))
    cr.rectangle(x, y, width, height)
    cr.fill()
