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
import os

from dtk.ui.window import Window
from dtk.ui.utils import get_parent_dir
from dtk.ui.label import Label
from dtk.ui.draw import draw_vlinear
from dtk.ui.entry import TextEntry, InputEntry
from dtk.ui.titlebar import Titlebar
from dtk.ui.button import CheckButton, Button
from dtk.ui.combo import ComboBox


from widget.ui import (set_widget_gravity, set_widget_left, set_widget_center)
from widget.skin import app_theme

def get_banner_image():
    return os.path.join(get_parent_dir(__file__, 3), "data", "banner", "default.png")

class Login(Window):
    def __init__(self):
        Window.__init__(self, enable_resize=True)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_default_size(290, 512)
        titlebar = Titlebar(["min", "max", "close"], app_name="Baidu Hi for Linux")
        titlebar.min_button.connect("clicked", lambda w: self.min_window())
        titlebar.max_button.connect("clicked", lambda w: self.toggle_max_window())
        titlebar.close_button.connect("clicked", lambda w: gtk.main_quit())
        self.add_move_event(titlebar.drag_box)
        self.add_toggle_event(titlebar.drag_box)
        
        banner_image = gtk.image_new_from_file(get_banner_image())
        banner_box = set_widget_gravity(banner_image, (0,0,0,0), (10, 0, 0, 0))
        user_box, self.user_entry = self.create_combo_entry("帐号:")
        passwd_box, self.passwd_entry = self.create_combo_entry("密码:")
        self.remember_passwd = CheckButton("记住密码")
        self.automatic_login = CheckButton("自动登录")
        self.status_box, self.status_combo_box = self.create_combo_widget("状态:", 
                                                     [(key, None) for key in "在线 忙碌 离开 隐身".split()],
                                                     0)
        
        check_box = gtk.HBox(spacing=10)
        check_box.pack_start(self.remember_passwd, False, False)
        check_box.pack_start(self.automatic_login, False, False)
        
        body_table = gtk.Table(5, 1)
        body_table.set_row_spacings(10)
        body_table.attach(banner_box, 0, 1, 0, 1, xoptions=gtk.FILL, yoptions=gtk.FILL)
        body_table.attach(user_box, 0, 1, 1, 2, xoptions=gtk.FILL, yoptions=gtk.FILL, xpadding=8)
        body_table.attach(passwd_box, 0, 1, 2, 3, xoptions=gtk.FILL, yoptions=gtk.FILL, xpadding=8)
        # body_table.attach(self.status_box, 0, 1, 3, 4, xoptions=gtk.FILL, yoptions=gtk.FILL, xpadding=8)        
        body_table.attach(check_box, 0, 1, 4, 5, xoptions=gtk.FILL, yoptions=gtk.FILL)
        
        body_box_align = set_widget_gravity(set_widget_center(body_table), 
                                            (1, 1, 0.5, 0.5),
                                            (0, 0, 30, 30))
        
        self.login_button = Button("登录")
        self.login_button.set_size_request(95, 30)
        login_button_align = set_widget_gravity(set_widget_center(self.login_button),
                                                (1, 1, 0.5, 0.5),
                                                (30, 30, 0, 0))
        
        main_box = gtk.VBox()        
        main_box.connect("expose-event", self.draw_border_mask)
        main_box.pack_start(body_box_align, False, True)
        main_box.pack_start(login_button_align, False, True)
        
        self.window_frame.pack_start(titlebar, False, True)
        self.window_frame.pack_start(main_box)
        
        
    def create_combo_entry(self, label_content, entry_content=""):    
        vbox = gtk.VBox()
        vbox.set_spacing(5)
        label = Label(label_content)
        text_entry = TextEntry(entry_content)
        text_entry.set_size(198, 26)
        entry_box = set_widget_center(text_entry)
        vbox.pack_start(label, False, False)
        vbox.pack_start(entry_box, False, False)
        return vbox, text_entry
    
    def draw_border_mask(self, widget, event):    
        cr = widget.window.cairo_create()
        rect = widget.allocation
        draw_vlinear(cr, rect.x + 8, rect.y + 6, rect.width - 16, rect.height - 16,
                     app_theme.get_shadow_color("linearBackground").get_color_info(),
                     4)
        
    def create_combo_widget(self, label_content, items, select_index=0):
        label = Label(label_content)
        combo_box = ComboBox(items, select_index=select_index)
        hbox = gtk.HBox(spacing=5)
        hbox.pack_start(label, False, False)
        hbox.pack_start(combo_box, False, False)
        return hbox, combo_box
