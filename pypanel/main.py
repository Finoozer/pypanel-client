import json
import pathlib
import pickle
import re
import secrets
import threading
import uuid
import webbrowser
from datetime import date
from datetime import datetime as datetime
from datetime import timedelta as timedelta
from os import listdir, makedirs, path, rename
from time import sleep
from uuid import uuid4

import geocoder
import pytz
import requests
from dearpygui.core import *
from dearpygui.simple import *
from pyautogui import size

from .resources import get_resource_path
BASE_DIR = pathlib.Path(__file__).resolve().parent
DATA_DIR = get_resource_path('data')
__version__ = 'v0.1.5'

# TODO: Fix scrollbars


class ProfileMan:
    opened_apps = []

    default_dat = {
        "ID": "DEFAULT",
        "name": "DEFAULT",
        "apps": []
    }
    def_user_conf = {
        "last_profile": "DEFAULT"
    }

    CONFIG_PATH = path.expanduser('~/Documents/PyPanel')
    PROFILES_PATH = path.expanduser('~/Documents/PyPanel/profiles')
    TEMP_PATH = path.expanduser('~/Documents/PyPanel/tmp')
    DEFAULTS_PATH = path.expanduser('~/Documents/PyPanel/profiles/DEFAULT.dat')
    USER_PATH = path.expanduser('~/Documents/PyPanel/config.json')

    def __init__(self, user):
        self.user = user
        self.profile_data = None
        self.data_access()
        with open(file=self.USER_PATH) as config:
            self.user_conf = json.load(config)
        self.load_user_conf()
        self.auto_update()

    def data_access(self):
        # Create main PyPanel config folder
        if not path.exists(self.CONFIG_PATH):
            try:
                makedirs(self.CONFIG_PATH)
            except OSError:
                print('Could not create config folder')
        # Create folder for profiles
        if not path.exists(self.PROFILES_PATH):
            try:
                makedirs(self.PROFILES_PATH)
            except OSError:
                print('Could not create profiles folder')
        # Create main PyPanel config folder
        if not path.exists(self.TEMP_PATH):
            try:
                makedirs(self.TEMP_PATH)
            except OSError:
                print('Could not create config folder')
        # Create file with default config
        if not path.exists(self.DEFAULTS_PATH):
            try:
                with open(file=self.DEFAULTS_PATH, mode='wb') as def_conf:
                    pickle.dump(self.default_dat, def_conf, pickle.HIGHEST_PROTOCOL)
            except OSError:
                print('Could not create defaults file')
        # Create file for user config
        if not path.exists(self.USER_PATH):
            try:
                with open(file=self.USER_PATH, mode='w') as user_conf:
                    json.dump(self.def_user_conf, user_conf)
            except OSError:
                print('Could not create config file')

    @staticmethod
    def download_update(link):
        webbrowser.open(url=link)
        stop_dearpygui()

    def auto_update(self, diag=False):
        try:
            remote_ver = requests.get(url='https://api.github.com/repos/Finoozer/PyPanel/releases/latest',
                                      timeout=3).json()
            if 'message' not in remote_ver:
                if remote_ver['tag_name'] != __version__:
                    if does_item_exist('w_update_pypanel'):
                        delete_item('w_update_pypanel')
                    with window(name='w_update_pypanel', label='Update Available!', autosize=True):
                        add_input_text(name='##change_log', default_value=remote_ver['body'], multiline=True,
                                       readonly=True, width=500)
                        add_dummy(height=10)
                        with managed_columns(name='update_btns', columns=3, border=False):
                            add_dummy()
                            add_text(name='Update to ' + remote_ver['tag_name'] + ' ?')
                            add_dummy()
                            add_button(name='btn_skip_update', label='Skip',
                                       callback=lambda: delete_item('w_update_pypanel'))
                            set_item_color(item='btn_skip_update', style=mvGuiCol_Button, color=[255, 25, 25, 100])
                            add_dummy()
                            add_button(name='btn_update', label='Update',
                                       callback=lambda: self.download_update(remote_ver['assets'][0]
                                                                             ['browser_download_url']))
                            set_item_color(item='btn_update', style=mvGuiCol_Button, color=[25, 255, 25, 100])
                if remote_ver['tag_name'] == __version__ and diag is True:
                    if does_item_exist('w_no_updates'):
                        delete_item('w_no_updates')
                    with window(name='w_no_updates', label='No Updates Available', autosize=True):
                        add_dummy()
                        add_text(name='There are no updates available.')
                        add_dummy()

        except TimeoutError:
            if does_item_exist('w_timeout'):
                delete_item('w_timeout')
            with window(name='w_timeout', label='Timeout', autosize=True):
                add_dummy()
                add_text(name='You are offline', color=[255, 25, 25, 200])
                add_dummy()
                add_text(name='Most of the PyPanel functionality')
                add_text(name='is dependent on internet connection.')
                add_dummy()
                with managed_columns(name='timeout_btns', columns=2):
                    add_button(name='btn_cancel_off', label='Cancel', callback=lambda: delete_item('w_timeout'))
                    set_item_color(item='btn_cancel_off', style=mvGuiCol_Button, color=[255, 25, 25, 100])
                    add_button(name='btn_retry', label='Retry', callback=self.auto_update)
                    set_item_color(item='btn_retry', style=mvGuiCol_Button, color=[25, 255, 25, 100])

    def load_user_conf(self):
        self.load_profile(self.user_conf['last_profile'])

    def update_user_conf(self):
        with open(file=self.USER_PATH, mode='w') as config:
            json.dump(self.user_conf, config)

    def load_profile(self, prof: str):
        try:
            [x.close_window() for x in self.opened_apps if x.is_open]
            self.opened_apps.clear()
            prof_path = self.PROFILES_PATH + '/' + prof + '.dat'
            with open(file=prof_path, mode='rb') as load:
                self.profile_data = pickle.load(load)
            self.user_conf['last_profile'] = prof
            self.update_user_conf()
        except OSError:
            if does_item_exist(item='pu_error'):
                delete_item(item='pu_error')
            with window(name='pu_error', label='Error', autosize=True):
                add_text(name='An error occurred when trying to load profile',
                         parent='pu_error', color=[255, 25, 25, 200])
            self.load_profile('DEFAULT')

        for x in self.profile_data['apps']:
            sub_app = globals()[x['name']](**x)
            self.opened_apps.append(sub_app)
            sub_app.open_window()

    def save_profile(self):
        if self.profile_data['name'] != 'DEFAULT':
            self.profile_data['apps'] = [app.save() for app in self.opened_apps]
            prof_path = self.PROFILES_PATH + '/' + self.profile_data['ID'] + '.dat'
            with open(file=prof_path, mode='wb') as out:
                pickle.dump(self.profile_data, out, pickle.HIGHEST_PROTOCOL)
            self.user_conf['last_profile'] = self.profile_data['ID']
            self.update_user_conf()
        else:
            self.create_profile_diag()

    def create_profile_diag(self):
        if does_item_exist(item='w_add_profile'):
            delete_item(item='w_add_profile')
        with window(name='w_add_profile', label='Add Profile', autosize=True):
            add_text(name='Profile name:')
            add_input_text(name='##prof_name', default_value='New Profile')
            add_button(name='btn_add_prof', label='Add',
                       callback=self.create_profile, callback_data=lambda: get_value(name='##prof_name'))

    def create_profile(self, sender, data: str):
        if 2 < len(data) < 50:
            data = re.sub(r'[^A-Za-z0-9 ]+', '', data)
            id_ = str(uuid.uuid4())
            prof_path = self.PROFILES_PATH + '/' + id_ + '.dat'
            self.user_conf['last_profile'] = id_
            self.update_user_conf()
            [x.close_window() for x in self.opened_apps if x.is_open]
            self.opened_apps.clear()
            self.profile_data = {'ID': id_, 'name': data, 'apps': []}
            with open(file=prof_path, mode='wb') as out:
                pickle.dump(self.profile_data, out, pickle.HIGHEST_PROTOCOL)
            delete_item(item='w_add_profile')
            self.list_profiles()
        else:
            add_dummy(parent='w_add_profile')
            add_text(name='Profile name has to be between 3 and 50 chars long!',
                     parent='w_add_profile', color=[255, 25, 25, 255])
            add_dummy(parent='w_add_profile')

    def profile_man(self):
        # TODO: Center profile_man window
        if not does_item_exist(item='profile_man'):
            with window(name='profile_man', label='Profile Manager'):
                with menu_bar(name='mb_profile_man', parent='profile_man'):
                    add_button(name='profile_man_load', label='Load', callback=self.switch_profile,
                               callback_data=lambda: get_table_selections(table='profile_man_table'))
                    set_item_color(item='profile_man_load', style=mvGuiCol_Button, color=[25, 25, 255, 100])
                    add_dummy()
                    add_button(name='profile_man_add', label='Add', callback=self.create_profile_diag)
                    set_item_color(item='profile_man_add', style=mvGuiCol_Button, color=[25, 255, 25, 100])
                    add_dummy()
                    add_button(name='profile_man_rename', label='Rename', callback=self.rename_profile_diag,
                               callback_data=lambda: get_table_selections(table='profile_man_table'))
                    set_item_color(item='profile_man_rename', style=mvGuiCol_Button, color=[255, 69, 0, 100])
                    add_dummy()
                    add_button(name='profile_man_remove', label='Remove', callback=self.remove_profile,
                               callback_data=lambda: get_table_selections(table='profile_man_table'))
                    set_item_color(item='profile_man_remove', style=mvGuiCol_Button, color=[255, 25, 25, 100])

            add_table(name='profile_man_table', parent='profile_man', headers=['Name', 'Active', 'ID'])
            self.list_profiles()
        else:
            show_item(item='profile_man')
            self.list_profiles()

    def list_profiles(self):
        profiles = []
        if does_item_exist(item='profile_man_table'):
            clear_table(table='profile_man_table')
        for x in listdir(self.PROFILES_PATH):
            if re.match(r'.+\.dat', x):
                prof_path = self.PROFILES_PATH + '/' + x
                with open(file=prof_path, mode='rb') as prof:
                    data = pickle.load(prof)
                profiles.append([data['name'], data['ID']])
        if does_item_exist(item='profile_man_table'):
            for x in sorted(profiles):
                if x[1] == self.user_conf['last_profile']:
                    add_row(table='profile_man_table', row=[x[0], 'Yes', x[1]])
                else:
                    add_row(table='profile_man_table', row=[x[0], 'No', x[1]])

    def open_app(self, app):
        if not any(isinstance(x, app) for x in self.opened_apps):
            x = app()
            self.opened_apps.append(x)
            x.open_window()
        else:
            next(x.open_window() for x in self.opened_apps if isinstance(x, app))

    def list_apps(self):
        # Update here to include new SubApps
        add_menu_item(name='rust_sub', parent='m_apps', label='RustApp', callback=lambda: self.open_app(
            RustApp))
        add_menu_item(name='clock_sub', parent='m_apps', label='ClockApp', callback=lambda: self.open_app(
            ClockApp))
        add_menu_item(name='weather_sub', parent='m_apps', label='WeatherApp', callback=lambda: self.open_app(
            WeatherApp))
        add_menu_item(name='passgen_sub', parent='m_apps', label='PassGenApp', callback=lambda: self.open_app(
            PassGenApp))

    def remove_profile(self, sender, data):
        data = set(x[0] for x in data)
        for x in data:
            counter = 0
            id_ = get_table_item(table='profile_man_table', row=x-counter, column=2)
            if id_ == 'DEFAULT':
                if does_item_exist(item='pu_error'):
                    delete_item(item='pu_error')
                with window(name='pu_error', label='Error', autosize=True):
                    add_dummy()
                    add_text(name='Cannot delete DEFAULT profile!', color=[255, 25, 25, 255])
                    add_dummy()
            elif id_ == self.user_conf['last_profile']:
                self.load_profile(prof='DEFAULT')
                prof_path = self.PROFILES_PATH + '/' + id_
                rename(prof_path + '.dat', prof_path + '.bak')
                counter += 1
            else:
                prof_path = self.PROFILES_PATH + '/' + id_
                rename(prof_path + '.dat', prof_path + '.bak')
                counter += 1
        self.list_profiles()

    def switch_profile(self, sender, data):
        id_ = get_table_item(table='profile_man_table', row=data[0][0], column=2)
        if id_ != self.user_conf['last_profile']:
            delete_item(item='profile_man')
            self.load_profile(id_)

    def rename_profile_diag(self, sender, data):
        id_ = get_table_item(table='profile_man_table', row=data[0][0], column=2)
        if does_item_exist(item='w_rename_profile'):
            delete_item(item='w_rename_profile')
        with window(name='w_rename_profile', label='Rename Profile', autosize=True):
            add_text(name='New profile name:')
            add_input_text(name='##new_name', default_value='New Profile')
            add_button(name='btn_rename_prof', label='Rename',
                       callback=lambda: self.rename_profile(get_value(name='##new_name'), id_))

    def rename_profile(self, new_name, id_):
        # TODO: Should not be able to rename default
        if 2 < len(new_name) < 50:
            new_name = re.sub(r'[^A-Za-z0-9 ]+', '', new_name)
            prof_path = self.PROFILES_PATH + '/' + id_ + '.dat'
            with open(file=prof_path, mode='rb') as prof:
                data = pickle.load(prof)
            data['name'] = new_name
            with open(file=prof_path, mode='wb') as out:
                pickle.dump(data, out, pickle.HIGHEST_PROTOCOL)
            delete_item(item='w_rename_profile')
            self.list_profiles()
        else:
            add_dummy(parent='w_rename_profile')
            add_text(name='Profile name has to be between 3 and 50 chars long!',
                     parent='w_rename_profile', color=[255, 25, 25, 255])
            add_text(name='Current length: ' + str(len(new_name)))
            add_dummy(parent='w_rename_profile')

    def save_quit(self):
        self.save_profile()
        sleep(2)
        stop_dearpygui()

    def options(self):
        if does_item_exist(item='w_options'):
            delete_item(item='w_options')
        with window(name='w_options', label='Options'):
            add_separator()
            with managed_columns(name='row1', columns=2):
                add_text(name='Font')
                add_combo(name='##cfont', items=['1', 'two', 'III'], default_value='Choose:')
            add_separator()
            with managed_columns(name='row2', columns=2):
                add_text(name='User Config')
                add_button(name='##open_user_conf', label='Open', callback=lambda: webbrowser.open(self.USER_PATH))
                set_item_color(item='##open_user_conf', style=mvGuiCol_Button, color=[25, 25, 255, 100])
            add_separator()
            with managed_columns(name='row3', columns=2):
                add_text(name='Reset defaults')
                add_button(name='##set_defaults', label='RESET', callback=self.reset_conf)
                set_item_color(item='##set_defaults', style=mvGuiCol_Button, color=[255, 25, 25, 100])
            add_separator()
            add_dummy()

    def reset_conf(self):
        if does_item_exist(item='w_reset_conf'):
            delete_item(item='w_reset_conf')
        with window(name='w_reset_conf', label='Reset User Config', autosize=True):
            add_dummy()
            add_text(name='Are you sure you want to reset user config?')
            add_dummy()
            add_text(name='This action cannot be undone!', color=[255, 25, 25, 255])
            add_dummy()
            add_button(name='btn_yes_reset', label='Yes', callback=lambda: reset_conf_(self))
            set_item_color(item='btn_yes_reset', style=mvGuiCol_Button, color=[25, 255, 25, 100])
            add_same_line()
            add_button(name='btn_no_reset', label='No', callback=lambda: delete_item('w_reset_conf'))
            set_item_color(item='btn_no_reset', style=mvGuiCol_Button, color=[255, 25, 25, 100])
            add_dummy()

        def reset_conf_(that):
            print('Reset')
            that.user_conf = that.def_user_conf
            that.update_user_conf()
            that.load_user_conf()
            delete_item(item='w_reset_conf')


class SubApps:
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    def __init__(self, name, is_open, autosize, x_pos, y_pos, height, width):
        self.name = name
        self.is_open = is_open
        self.autosize = autosize
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.height = height
        self.width = width

    @staticmethod
    def delit(s: str):
        if does_item_exist(item=s):
            delete_item(item=s)

    def close_window(self):
        if self.autosize is False:
            self.height = get_item_height(self.name)
            self.width = get_item_width(self.name)
        self.x_pos, self.y_pos = get_window_pos(self.name)
        self.is_open = False
        self.delit(self.name)

    def save(self):
        if self.is_open:
            self.x_pos, self.y_pos = get_window_pos(self.name)
            self.height = get_item_height(self.name)
            self.width = get_item_width(self.name)
        return {'name': self.name, 'x_pos': self.x_pos, 'y_pos': self.y_pos, 'height': self.height, 'width': self.width}


class RustApp(SubApps):

    def __init__(self, is_open=False, autosize=False, x_pos=200, y_pos=200, height=200, width=200, name='RustApp',
                 time=10, ser_list=None, table=None):
        super().__init__(name, is_open, autosize, x_pos, y_pos, height, width)
        if ser_list is None:
            ser_list = []
        if table is None:
            table = str(uuid4())[:-10:-1]
        self.time = time
        self.label = 'Rust Server Info'
        self.ser_list = ser_list
        self.cb = None
        self.table = table

    def open_window(self):
        if not does_item_exist(item=self.name):
            self.is_open = True
            with window(name=self.name, label=self.label, x_pos=self.x_pos, y_pos=self.y_pos, height=self.height,
                        width=self.width, on_close=self.close_window):
                add_button(name='btn_add_server', label='Add', callback=self.open_diag)
                set_item_color(item='btn_add_server', style=mvGuiCol_Button, color=[25, 255, 25, 100])
                add_same_line()
                add_button(name='btn_rem_server', label='Remove', callback=self.remove_server,
                           callback_data=lambda: get_table_selections(table=self.table))
                set_item_color(item='btn_rem_server', style=mvGuiCol_Button, color=[255, 25, 25, 100])
                add_same_line()
                add_text(name='Refresh time: sec')
                add_same_line()
                add_input_int(name='##rtime', min_value=10, max_value=36000, step=5, width=100, default_value=20)
                set_value(name='##rtime', value=self.time)
                add_table(name=self.table, headers=['Server', 'Online', 'Max', 'Queue', 'ID'])
                if len(self.ser_list) > 0 and self.cb is None:
                    self.long_callback()
                elif len(self.ser_list) > 0 and self.cb is not None:
                    self.refresh()

    def open_diag(self):
        self.delit('diag_add_server')
        with window(name='diag_add_server', label='Add Rust Server',
                    autosize=True, on_close=lambda: delete_item(item='diag_add_server')):
            add_text('Server ID: ')
            add_input_text(name='server_id', label='')
            add_button(name='btn_server_id', label='Add Server', callback=self.add_server,
                       callback_data=lambda: get_value('server_id'))
            set_item_color(item='btn_server_id', style=mvGuiCol_Button, color=[25, 255, 25, 100])

    def add_server(self, sender, data):
        # TODO: User should also be able to enter whole URL
        ser_num = data
        try:
            bn_api = 'https://api.battlemetrics.com/servers/'
            req_url = '?include=orgDescription&fields[server]=id,name,address,ip,port,portQuery,players,maxPlayers,' \
                      'rank,status,details,queryStatus&fields[session]=start,stop,firstTime,name&fields' \
                      '[orgDescription]=public,approvedAt'
            url = bn_api + str(ser_num) + req_url
            obj = requests.get(url).json()
            server_name = obj['data']['attributes']['name']
            curr_players = obj['data']['attributes']['players']
            max_players = obj['data']['attributes']['maxPlayers']
            queued_players = obj['data']['attributes']['details']['rust_queued_players']

            if len(self.ser_list) > 0:
                for x in range(len(self.ser_list)):
                    if self.ser_list[x][4] == ser_num:
                        self.ser_list.pop(x)
                        break
            self.ser_list.append([server_name, curr_players, max_players, queued_players, ser_num])
            self.delit('diag_add_server')
            if self.cb is None:
                self.long_callback()
            self.refresh()

        except KeyError:
            return add_text(parent='diag_add_server', name=f'Battlemetrics is unavailable, try again later.',
                            color=[255, 25, 25, 255])

    def remove_server(self, sender, row):
        counter = 0
        row = set(x[0] for x in row)
        for x in row:
            self.ser_list.pop(x - counter)
            counter += 1
        self.refresh()

    def refresh(self):
        clear_table(table=self.table)
        for x in sorted(self.ser_list):
            add_row(table=self.table, row=[*x])

    def reload(self):
        while True:
            if does_item_exist(item=self.table) and not get_table_selections(table=self.table) \
                    and not does_item_exist(item='diag_add_server'):
                print('Reloaded')
                for x in range(len(self.ser_list)):
                    self.add_server(sender=None, data=self.ser_list[x][4])
                    self.refresh()
                self.refresh()
                if type(get_value('##rtime')) is int:
                    self.time = get_value('##rtime')
                sleep(self.time)

    def long_callback(self):
        self.cb = threading.Thread(name='rust_table',
                                   target=self.reload,
                                   daemon=True)
        self.cb.start()

    def save(self):
        x = super().save()
        self.time = get_value('##rtime')
        x.update({'time': self.time, 'ser_list': self.ser_list, 'table': self.table})
        return x


class ClockApp(SubApps):

    def __init__(self, is_open=False, autosize=False, x_pos=200, y_pos=200, height=200, width=200, name='ClockApp',
                 saved_zones=None):
        super().__init__(name, is_open, autosize, x_pos, y_pos, height, width)
        if saved_zones is None:
            saved_zones = []
        self.saved_zones = saved_zones
        self.cb = None
        self.cb2 = None
        self.time = None
        self.label = 'Clock'
        self.table = 'clock_table'
        self.time_pointer = 'time'
        self.date_pointer = 'date'
        self.weekday_pointer = 'weekday'
        self.zones = [*pytz.common_timezones]
        # TODO: PYTZ contains unavailable zones

    def get_local_time(self):
        while True:
            set_value(name=self.time_pointer, value='Time: {}'.format(str(datetime.now().time())[:-7]))
            set_value(name=self.date_pointer, value='Date: {}'.format(str(date.today())))
            set_value(name=self.weekday_pointer, value='Weekday: ' + self.weekdays[date.today().weekday()])
            sleep(1)

    def open_window(self):
        if not does_item_exist(item=self.name):
            self.is_open = True
            with window(name=self.name, label=self.label, on_close=self.close_window, x_pos=self.x_pos,
                        y_pos=self.y_pos, height=self.height, width=self.width):
                with menu_bar(name='mb_clock', parent=self.name):
                    add_button(name='clock_add', label='Add', callback=self.open_diag)
                    set_item_color(item='clock_add', style=mvGuiCol_Button, color=[25, 255, 25, 100])
                    add_button(name='clock_remove', label='Remove', callback=self.remove_zone,
                               callback_data=lambda: get_table_selections(table=self.table))
                    set_item_color(item='clock_remove', style=mvGuiCol_Button, color=[255, 25, 25, 100])
                with managed_columns(name='local_time', columns=2):
                    add_text(name='##big_local_time', source=self.time_pointer, wrap=-1)
                    add_text(name='##date', source=self.date_pointer)
                    add_dummy()
                    add_text(name='##weekday', source=self.weekday_pointer)
                add_table(name=self.table, parent=self.name, headers=['Location', 'Date', 'Time'])
                if self.cb is None:
                    self.get_time_cb()
                if len(self.saved_zones) > 0 and self.cb2 is None:
                    self.ref_table_cb()
                elif len(self.saved_zones) > 0 and self.cb2 is not None:
                    self.refresh_table()

    def reload_table(self):
        while True:
            if does_item_exist(item=self.table) and not get_table_selections(table=self.table) \
                    and not does_item_exist(item='diag_add_zone'):
                for zone in self.saved_zones:
                    temp = datetime.now(pytz.timezone(zone[0]))
                    zone[1], zone[2] = str(temp.date()), str(temp.time())[:-10]
                clear_table(table=self.table)
                for zone in sorted(self.saved_zones):
                    add_row(table=self.table, row=[*zone])
                sleep(5)

    def open_diag(self):
        # TODO: Make window modal
        self.delit('diag_add_zone')
        with window(name='diag_add_zone', label='Add New Clock',
                    autosize=True, on_close=lambda: delete_item(item='diag_add_zone')):
            add_dummy()
            add_text(name='Search Location: ')
            add_input_text(name='##search_box', hint='Berlin', no_spaces=True, callback=self.auto_complete,
                           callback_data=lambda: get_value(name='##search_box'))
            add_dummy()
            add_listbox(name='listbox', label='', items=self.zones, num_items=3)
            add_dummy()
            add_button(name='zone_add', label='Add Zone', callback=self.add_zone,
                       callback_data=lambda: get_value(name='listbox'))
            set_item_color(item='zone_add', style=mvGuiCol_Button, color=[25, 255, 25, 100])

    def auto_complete(self, sender, entry):
        if len(entry) > 1:
            self.zones = list(filter(lambda x: entry.lower() in x.lower(), [*pytz.common_timezones]))
            configure_item('listbox', items=self.zones)
        else:
            self.zones = [*pytz.common_timezones]
            configure_item('listbox', items=self.zones)

    def add_zone(self, sender, zone):
        self.saved_zones.append([self.zones[zone], None, None])
        if self.cb2 is None:
            self.ref_table_cb()
        delete_item(item='diag_add_zone')
        self.zones = [*pytz.common_timezones]
        self.refresh_table()

    def remove_zone(self, sender, rows):
        counter = 0
        rows = set(x[0] for x in rows)
        for x in rows:
            self.saved_zones.pop(x - counter)
            counter += 1
        self.refresh_table()

    def refresh_table(self):
        clear_table(table=self.table)
        for zone in sorted(self.saved_zones):
            add_row(table=self.table, row=[*zone])

    def get_time_cb(self):
        self.cb = threading.Thread(name='local_time',
                                   target=self.get_local_time,
                                   daemon=True)
        self.cb.start()

    def ref_table_cb(self):
        self.cb2 = threading.Thread(name='ref_table',
                                    target=self.reload_table,
                                    daemon=True)
        self.cb2.start()

    def save(self):
        x = super().save()
        x.update({'saved_zones': self.saved_zones})
        return x


class WeatherApp(SubApps):
    prec_type = {'snow': 'Snowing', 'rain': 'Raining', 'frzr': 'Freezing Rain', 'icep': 'Ice Pellets', 'none': '\\'}
    prec_am = {0: 'None', 1: '0 mm/hr', 2: '1 mm/hr', 3: '4 mm/hr', 4: '10 mm/hr', 5: '16 mm/hr', 6: '30 mm/hr',
               7: '50 mm/hr', 8: '75 mm/hr', 9: 'Over 75 mm/hr'}

    # TODO: Add 'Sunny' or 'Cloudy' based on json

    def __init__(self, is_open=False, autosize=False, x_pos=200, y_pos=200, height=200, width=200, name='WeatherApp'):
        super().__init__(name, is_open, autosize, x_pos, y_pos, height, width)
        self.location = geocoder.ip('me').latlng
        self.city = geocoder.komoot(self.location, method='reverse').city
        self.table = 'weather_table'
        self.label = 'Weather Info'
        self.req_at = 'None'
        self.cb = None

    def open_window(self):
        if not does_item_exist(item=self.name):
            self.is_open = True
            with window(name=self.name, label=self.label, x_pos=self.x_pos, y_pos=self.y_pos, height=self.height,
                        width=self.width, on_close=self.close_window):
                with managed_columns(name='weather_info_cols', columns=2):
                    # TODO: Add current temp, sunny/cloudy - make 3 columns
                    add_text(name='Location: ' + self.city, tip='Estimate (based on your IP)')
                    add_button(name='btn_man_ref', label='Refresh', tip='Manual Refresh', callback=self.get_weather)
                    set_item_color(item='btn_man_ref', style=mvGuiCol_Button, color=[25, 255, 25, 100])
                    add_text(name='Requested At: ', source=self.req_at)
                    # TODO: Add fixed height to table
                add_table(name=self.table, headers=['Day', 'Hour', 'Temp', 'Prec. Type', 'Prec. Amount'])
                if self.cb is None:
                    self.ref_table()

    def get_weather(self):
        # TODO: Add loading
        url = 'http://www.7timer.info/bin/api.pl?lon=' + str(self.location[1]) + \
              '&lat=' + str(self.location[0]) + '&product=civil&output=json'
        obj = requests.get(url=url).json()
        clear_table(self.table)
        time_now = datetime.now()
        set_value(name=self.req_at, value=f'Requested At: {str(time_now.time())[:-7]}')
        for data in obj['dataseries'][:16]:
            future = time_now + timedelta(hours=data["timepoint"])
            add_row(table=self.table, row=[f'{self.weekdays[future.weekday()]}', f'{future.hour:0>2}:00',
                                           f'{data["temp2m"]:>2} °C', f'{self.prec_type[data["prec_type"]]}',
                                           f'{self.prec_am[data["prec_amount"]]}'])

    def update_weather(self):
        while True:
            if does_item_exist(item=self.table):
                self.get_weather()
                sleep(9000)

    def ref_table(self):
        self.cb = threading.Thread(name='update_weather',
                                   target=self.update_weather,
                                   daemon=True)
        self.cb.start()


class PassGenApp(SubApps):
    wl = DATA_DIR / 'wordlist.txt'

    def __init__(self, is_open=False, autosize=True, x_pos=200, y_pos=200, height=200, width=200, name='PassGenApp'):
        super().__init__(name, is_open, autosize, x_pos, y_pos, height, width)
        self.label = 'Password Generator'
        self.wordlist = open(file=self.wl).read().splitlines()

    def open_window(self):
        if not does_item_exist(item=self.name):
            self.is_open = True
            with window(name=self.name, label=self.label, autosize=self.autosize, x_pos=self.x_pos, y_pos=self.y_pos,
                        on_close=self.close_window):
                add_dummy()
                add_text(name='Number of passwords: ')
                add_input_int(name='##n_of_pwds', min_value=1, max_value=50, default_value=10)
                add_dummy()
                add_text(name='Number of words to join: ')
                add_input_int(name='##n_of_wrds', min_value=3, max_value=10, default_value=5)
                add_dummy()
                add_text(name='Join with: ')
                add_combo(name='##cjoiner', items=['-', '_', 'space', '+', '.', ';', '/', ','], default_value='-')
                add_dummy()
                add_separator()
                add_dummy()
                add_text(name='Include capital letter?')
                add_checkbox(name='##check_letter', default_value=True)
                add_dummy()
                add_text(name='Include number?')
                add_checkbox(name='##check_num', default_value=True)
                add_dummy()
                add_dummy()
                add_dummy()
                add_button(name='test_btn', label='Generate', callback=self.generate_pwd)

    def generate_pwd(self):
        num_of_pwds = get_value(name='##n_of_pwds')
        num_of_wrds = get_value(name='##n_of_wrds')
        joiner = get_value(name='##cjoiner')
        if joiner == 'space':
            joiner = ' '
        inc_letter = get_value(name='##check_letter')
        inc_num = get_value(name='##check_num')
        if does_item_exist(item='##pwds_field'):
            delete_item(item='##pwds_field')
        pwds = []
        for _ in range(num_of_pwds):
            pwd = []
            for _ in range(num_of_wrds):
                pwd.append(secrets.choice(self.wordlist))
            if inc_letter:
                pwd[0] = pwd[0].capitalize()
            if inc_num:
                pwd.append(str(secrets.randbelow(10)))
            pwds.append(joiner.join(pwd))
        pwds = '\n'.join(pwds)
        if does_item_exist('w_gen_pwds'):
            delete_item('w_gen_pwds')
        with window(name='w_gen_pwds', label='Generated Passwords', autosize=True, x_pos=100, y_pos=100):
            add_input_text(name='##it_pwds', label='', default_value=pwds, readonly=True, multiline=True,
                           width=int(50 + num_of_wrds * 42), height=int(20 + num_of_pwds * 12))


def py_panel():
    main_prof = ProfileMan(user='Main')

    with window(name="main_window"):
        with menu_bar('_menu_bar'):
            with menu(name='m_file', label='File'):
                add_separator()
                add_menu_item(name='mi_save_quit', label='Save Quit', callback=main_prof.save_quit)
            with menu(name='m_apps', label='Apps'):
                main_prof.list_apps()
            add_menu_item(name='mi_options', parent='_menu_bar', label='Options', callback=main_prof.options)
            add_menu_item(name='mi_profiles', parent='_menu_bar',
                          label='Profiles', callback=main_prof.profile_man)
            with menu(name='m_help', label='Help'):
                add_menu_item(name='mi_get_started', label='Getting Started', callback=None)
                add_separator()
                add_menu_item(name='mi_updates', label='Check For Updates...',
                              callback=lambda: main_prof.auto_update(diag=True))
                add_separator()
                with menu(name='m_devtools', label='Diagnostic Tools'):
                    add_menu_item(name='mi_logger', label='Logger', callback=show_logger)
                    add_menu_item(name='mi_debug', label='Debug', callback=show_debug)
                    add_menu_item(name='mi_metrics', label='Metrics', callback=show_metrics)
                add_separator()
                add_menu_item(name='mi_about', label='About...', callback=None)
            add_dummy()
            add_button(name='btn_save_prof', label='Save Profile', callback=main_prof.save_profile)
            set_item_color(item='btn_save_prof', style=mvGuiCol_Button, color=[124, 252, 0, 100])

    # Center app on screen
    screen_width, screen_height = size()
    set_main_window_size(width=int(screen_width / 2), height=int(screen_height / 2))
    set_main_window_pos(x=int(screen_width / 4), y=int(screen_height / 4))

    set_main_window_title(title='PyPanel')
    start_dearpygui(primary_window='main_window')


if __name__ == '__main__':
    py_panel()
