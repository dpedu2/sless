#!/usr/bin/env python3

import logging
logging.basicConfig(filename='test.log',level=logging.DEBUG)
import json
import urwid


class JsonBox(urwid.Edit):
    """
    An abused urwid.Edit widget. Inputs are blocked so it behaves as a urwid.Text that we can focus upon.
    """
    def __init__(self, markup):
        super(JsonBox, self).__init__(markup)

    def keypress(self, size, key):
        #logging.info('JsonBox: ' + key)
        return key


class JsonObject(urwid.Pile):
    """
    A pile that can be collapsed to a single row aka "hidden". these are nested for sub-objects
    """
    def __init__(self, json_object, preview_keys=['_t', 'severity', 'event_name'], print_key=None, hidden=False):
        super(JsonObject, self).__init__([])
        self.json = json_object
        self.print_key = print_key

        preview_text = "{ ... }"
        if type(self.json) is dict:
            preview_text = "{ "
            for key in preview_keys:
                if key in self.json:
                    preview_text+="{}: {}, ".format(key, self.json[key])
            preview_text += '... }'
        elif type(self.json) is list:
            preview_text = "[ ... ]"

        if print_key:
            preview_text = '{}: {}'.format(print_key, preview_text)

        self.hidden_item = urwid.Padding(urwid.Pile([JsonBox(preview_text)]), left=5)

        #self.json_item = walk_json(json_object, parent=urwid.Pile([]))
        widgets = []
        if type(self.json) is dict:
            widgets.append(urwid.AttrMap(
                JsonBox( (print_key+": {") if print_key else '{'),
                'json_row',
                'json_row_h'
            ))

        elif type(self.json) is list:
            widgets.append(urwid.AttrMap(
                JsonBox( (print_key+": [") if print_key else '['),
                'json_row',
                'json_row_h'
            ))


        if type(self.json) in [list, dict]:
            if type(self.json) is list:
                for item in self.json:
                    widgets.append(JsonObject(item))
            elif type(self.json) is dict:
                for key in sorted(self.json.keys()):
                    widgets.append(JsonObject(self.json[key], hidden=type(self.json[key]) in [list, dict], print_key=key))

        else: # plain value
            if type(self.json) == type(None):
                str_value = 'null'
            elif type(self.json) not in [int, float]:
                str_value = '"{}"'.format(self.json)
            else:
                str_value = self.json
            widgets.append(JsonBox(
                '{}: {},'.format(print_key, str_value) if print_key else '{},'.format(str(str_value))
            ))





        if type(self.json) is dict:
            widgets.append(urwid.AttrMap(
                JsonBox('}'),
                'json_row',
                'json_row_h'
            ))
        elif type(self.json) is list:
            widgets.append(urwid.AttrMap(
                JsonBox("]"),
                'json_row',
                'json_row_h'
            ))
        self.json_item = urwid.Padding(urwid.Pile(widgets), left=5)

        self.is_hidden = hidden

        self.contents.append(((self.hidden_item if hidden else self.json_item), ('weight', 1)))

    def selectable(self):
        return True

    def can_hide(self):
        return type(self.json) in [list,dict]

    def toggleHidden(self):
        self.contents.clear()
        self.contents.append((self.json_item if self.is_hidden else self.hidden_item, ('weight', 1)))
        self.is_hidden = not self.is_hidden

    def setHidden(self, hidden):
        if hidden:
            if self.is_hidden:
                return
            self.toggleHidden()
        else:
            if not self.is_hidden:
                return
            self.toggleHidden()

    def keypress(self, size, key):
        if not self.is_hidden:
            key = super(JsonObject, self).keypress(size, key)

        logging.info('JsonObject('+ str(self.print_key) +'): ' + str(key))
        if key == ' ':
            if self.can_hide():
                self.toggleHidden()
            return None
        elif key == 'right':
            if self.can_hide():
                self.setHidden(False)
            return None
        elif key == 'left':
            if self.can_hide():
                self.setHidden(True)
            return None

        return key



class JsonFileDisplay(urwid.ListBox):
    def __init__(self, json_file):
        self.file = open(json_file, 'r')
        self.current_line = 0
        self.num_lines = 100

        body = []
        for i in range(0, self.num_lines):
            body.append(
                urwid.AttrMap(
                    JsonObject(self.next_line(), hidden=True),
                #    'row_odd' if self.current_line % 2 == 0 else 'row_even'
                     'json_row',
                     'json_row_h'
                )
            )

        super(JsonFileDisplay, self).__init__(urwid.SimpleFocusListWalker(body))


    def next_line(self):
        self.current_line += 1
        return json.loads(self.file.readline())

    def keypress(self, size, key):
        result = super(JsonFileDisplay, self).keypress(size, key)
        logging.info('JsonFileDisplay: ' + key + '->' + str(result))
        return result
#        key = super(JsonListBox, self).keypress(size, key)
#        if key != 'enter':
#            return key
#        name = self.focus[0].edit_text
#        if not name:
#            raise urwid.ExitMainLoop()
#        # replace or add response
#        self.focus.contents[1:] = [(answer(name), self.focus.options())]
#        pos = self.focus_position
#        # add a new question
#        self.body.insert(pos + 1, question())
#        self.focus_position = pos + 1
#
#        if len(self.body) > 20:
#            self.body.pop(0)
#            logging.info("popped")

header_buttons = [
    ('fixed', 13, urwid.Button("(F1) Help")),
    ('fixed', 13, urwid.Button("(F2) Load")),
    ('fixed', 15, urwid.Button("(F3) Export")),
    ('fixed', 15, urwid.Button("(F4) Filter")),
    ('fixed', 13, urwid.Button("(F5) Exit")),
]

_navColumns = urwid.Columns(header_buttons, dividechars=3, focus_column=None, min_width=1, box_columns=None)

navColumns = urwid.AttrMap(_navColumns, 'header')

mainFrame = urwid.Frame(JsonFileDisplay('./query_api_server.log.20160527T012105'), header=navColumns, footer=None, focus_part='body')


palette = [
    ('I say', 'default,bold', 'default'),
    ('header', 'black', 'light green'),
    ('row_odd', 'white', 'dark gray'),

    ('json_row', 'dark gray', 'black'),
    ('json_row_h', 'white', 'black')
    #('json_row_h', 'light gray', 'dark blue', 'standout','#ff8', '#806')
    #('json_row_h', 'white', 'dark gray', '','#f0f', '#00f')
]

screen = urwid.raw_display.Screen()
screen.set_terminal_properties(colors=256)
screen.register_palette(palette)

loop = urwid.MainLoop(mainFrame, palette)
loop.run()
