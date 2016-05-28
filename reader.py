#!/usr/bin/env python3

import logging
logging.basicConfig(filename='test.log',level=logging.DEBUG)
import json
import urwid
#from urwid.command_map import *

#class HidablePile(urwid.Pile):
#    def __init__(self, widget_list, focus_item=None, hidden=False):
#        super(HidablePile, self).__init__(widget_list, focus_item=None)
#        self.hidden = hidden
#        self.hidden_contents = []
#        if hidden:
#            self.hide()
#
#    def hide(self):
#        if not self.hidden:
#            self.hidden = True
#            for i in range(0, len(self.contents)):
#                self.hidden_contents.append(self.contents.pop())
#            self._invalidate()
#
#    def show(self):
#        if self.hidden:
#            self.hidden = False
#            for i in range(0, len(self.hidden_contents)):
#                self.contents.append(self.hidden_contents.pop())
#            self._invalidate()
#
#    #def keypress(self, size, key):
#    #    x, y = self.get_cursor_coords(size)
#    #    if self.hidden:
#    #        if key == 'down':
#    #            if y > 0:
#    #                key = super(HidablePile, self).keypress(size, key)
#    #            else:
#    #                logging.info('HidablePile: ' + key)
#    #
#    #            return key
#    #    else:
#    #        return super(HidablePile, self).keypress(size, key)

class JsonBox(urwid.Text):
    def __init__(self, markup):
        #urwid.Text(markup, align='left', wrap='space', layout=None)
        super(JsonBox, self).__init__(markup)

    def keypress(self, size, key):
        #logging.info('JsonBox: ' + key)
        #return key
        logging.info('JsonBox: ' + key)
        return super(JsonBox, self).keypress(size, key)

def walk_json(data, parent=None, depth=0, print_key=None):
    """
    Return a nested list of Padding + Piles/Texts representing the json
    """
    logging.info(type(data))
    this_row = urwid.Pile([])
    parent.contents.append((this_row, ('pack', None)))

    if type(data) in [dict, list]:
        begin_char = '{' if type(data) is dict else '['
        end_char = '}' if type(data) is dict else ']'

        this_row.contents.append(
            (
                urwid.Padding(
                    JsonBox('%s: %s'%(print_key, begin_char) if print_key else begin_char),
                    left=5*depth
                ),
                ('pack', None)
            )
        )

        if type(data) is dict:
            for key in sorted(data.keys()):
                walk_json(data[key], this_row, depth+1, key)
        else:
            for value in data:
                walk_json(value, this_row, depth+1)

        this_row.contents.append(
            (
                urwid.Padding(
                    JsonBox(end_char),
                    left=5*depth
                ),
                ('pack', None)
            )
        )

    else:
        if data is None:
            data = 'null'
        this_row.contents.append(
            (
                urwid.Padding(
                    JsonBox('%s: %s'%(print_key, str(data)) if print_key else str(data)),
                    left=5*depth
                ),
                ('pack', None)
            )
        )
    #if depth > 0:
    #    this_row.hide()
    return this_row


header_buttons = [
    ('fixed', 13, urwid.Button("(F1) Help")),
    ('fixed', 13, urwid.Button("(F2) Load")),
    ('fixed', 15, urwid.Button("(F3) Export")),
    ('fixed', 15, urwid.Button("(F4) Filter")),
    ('fixed', 13, urwid.Button("(F5) Exit")),
]

_navColumns = urwid.Columns(header_buttons, dividechars=3, focus_column=None, min_width=1, box_columns=None)

navColumns = urwid.AttrMap(_navColumns, 'header')


class JsonObject(urwid.Pile):
    def __init__(self, json_object, preview_keys=['_t', 'severity', 'event_name']):
        super(JsonObject, self).__init__([])
        self.json = json_object

        preview_text = "{ ... }"
        if type(self.json) is dict:
            preview_text = "{ "
            for key in preview_keys:
                if key in self.json:
                    preview_text+="{}: {}, ".format(key, self.json[key])
            preview_text += '... }'
        
        self.hidden_item = urwid.Pile([urwid.Text(preview_text)])
        self.json_item = walk_json(json_object, parent=urwid.Pile([]))

        self.is_hidden = True

        self.contents.append((self.hidden_item, ('weight', 1)))

    def selectable(self):
        return True

    def rebuild(self):
        pass

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
        logging.info('JTR: ' + key)
        if key == ' ':
            self.toggleHidden()
        elif key == 'right':
            self.setHidden(False)
        elif key == 'left':
            self.setHidden(True)
        else:
            return super(JsonObject, self).keypress(size, key)



class JsonFileDisplay(urwid.ListBox):
    def __init__(self, json_file):
        self.file = open(json_file, 'r')
        self.current_line = 0
        self.num_lines = 100

        body = []
        for i in range(0, self.num_lines):
            body.append(
                urwid.AttrMap(
                    JsonObject(self.next_line()),
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
        logging.info('JsonListBox: ' + key)
        return super(JsonFileDisplay, self).keypress(size, key)
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


mainFrame = urwid.Frame(JsonFileDisplay('./query_api_server.log.20160527T012105'), header=navColumns, footer=None, focus_part='body')


palette = [
    ('I say', 'default,bold', 'default'),
    ('header', 'black', 'light green'),
    ('row_odd', 'white', 'dark gray'),
    
    ('json_row', 'white', ''),
    ('json_row_h', 'black', 'dark cyan')
    #('json_row_h', 'light gray', 'dark cyan', 'standout','#ff8', '#806')
]

screen = urwid.raw_display.Screen()
screen.set_terminal_properties(colors=256)
screen.register_palette(palette)

loop = urwid.MainLoop(mainFrame, palette)
loop.run()
