#!/usr/bin/env python3

#import logging
#logging.basicConfig(filename='test.log',level=logging.DEBUG)
import urwid
from sless.lazyjson import LazyJsonReader
from threading import Thread
from time import sleep


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
    def __init__(self, json_object, preview_keys=['_t', 'severity', 'event_name', '__time__'], print_key=None, hidden=False, meta=None):
        """
        :param json_object: object to display
        :param preview_keys: keys to show when object is collasped
        :param print_key: when nesting, print a key before this object
        :param hidden: true if object is collapsed by default
        :param meta: arbitrary data to store in this object
        """
        super(JsonObject, self).__init__([])
        self.meta = meta
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

        #logging.info('JsonObject('+ str(self.print_key) +'): ' + str(key))
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

    #def mouse_event(self, size, event, button, col, row, focus):
    #    logging.info("Mouse {} on {}".format(event, id(self)))
    #    return super(JsonObject, self).mouse_event(size, event, button, col, row, focus)


class AsyncLineLoader(Thread):
    def __init__(self, parent):
        super(AsyncLineLoader, self).__init__()
        self.parent = parent
        self.enabled = True
        self.start()

    def run(self):
        """
        Monitors when we need to read more items from disk and add to the top or bottom
        """
        while self.enabled:
            sleep(0.1)
            self.parent.insert_items()



class LazyFocusListWalker(urwid.SimpleFocusListWalker):
    """
    Similar to SimpleFocusListWalker but lazy-loads contents
    """
    def __init__(self, initial_content, file_display):
        """
        :param initial_content: Initial set of content to show
        :param file_display: parent JsonFileDisplay object
        """

        #self.above = above if above else len(initial_content)
        #self.below = above if above else len(initial_content)

        self.parent = file_display
        self.async_loader = AsyncLineLoader(self)

        self.last_add = True # True = added to top
                             # False = added to bottom

        super(LazyFocusListWalker, self).__init__(initial_content)

    #def next_position(self, position):
    #    logging.info("LazyFocusListWalker.next_position: {}".format(position))
    #    return super(LazyFocusListWalker, self).next_position(position)

    #def prev_position(self, position):
    #    logging.info("LazyFocusListWalker.prev_position: {}".format(position))
    #    return super(LazyFocusListWalker, self).prev_position(position)

    def insert_items(self):
        load_more_thresh = 20

        count_above = self.focus
        count_below = len(self)-self.focus
        #logging.info("Total: {}, reader @ {}".format(len(self), self.parent.reader.line))
        # Add to bottom if needed

        if count_below + load_more_thresh < self.parent.num_lines:
            while count_below < self.parent.num_lines:
                #logging.info("add to bottom")
                # Seek to last item
                self.parent.reader._seek_to(*self[-1]._original_widget.meta)
                # Read next
                next_item = self.parent.reader.read_next()
                self.last_add = False
                reader_position = self.parent.reader._get_position()
                # Add next item to self
                if next_item is not None:
                    self.append(
                        self.parent.build_item(
                            next_item,
                            reader_position
                        )
                    )
                    count_below = len(self)-self.focus
                else:
                    break

        # Add to top if needed
        if self[0]._original_widget.meta[0] > 1 and count_above + load_more_thresh < self.parent.num_lines:
            num_added = 0
            while self[0]._original_widget.meta[0] > 1 and count_above < self.parent.num_lines:
                # Seek to first item
                seek_line, seek_pos = self[0]._original_widget.meta
                self.parent.reader._seek_to(seek_line, seek_pos)
                # Read prev
                if not self.last_add:
                    self.parent.reader.read_prev()
                    # If the last read from the json was a next_line() we need to burn a line as the
                    # prev item returned will be the same as the prior read_next()
                next_item = self.parent.reader.read_prev()
                self.last_add = True
                reader_position = self.parent.reader._get_position()
                # Add next item to self
                #logging.info(self.parent.reader.line)
                if next_item is not None:
                    #logging.info("did add to top")
                    #logging.info(self[0]._original_widget.meta)
                    #import pdb ; pdb.set_trace()
                    self.insert(
                        0,
                        self.parent.build_item(
                            next_item,
                            reader_position
                        )
                    )
                    num_added += 1
                    #position += 1
                    count_above = self.focus
                else:
                    break
            #self.focus += num_added

    def set_focus(self, position):
        #logging.info("LazyFocusListWalker.set_focus: {}".format(position))
        #self.focus = position
        # seems we can insert/remove items here without upsetting the listbox
        # ensure that at least $TERMINAL_HEIGHT items are loaded above and below the select item
        # also, decrement self.focus the same number of items removed from the beginning
        #self.insert(0, urwid.Text('hello'))


        count_above = position
        count_below = len(self)-position
        #logging.info("Buffers - below: {}, above: {}".format(count_below, count_above))

        # Trim from bottom if needed
        while count_below > self.parent.num_lines:
            self.pop()
            count_below = len(self)-position

        # Trim from top if needed
        while count_above > self.parent.num_lines:
            #import pdb ; pdb.set_trace()
            self.pop(0)
            position -= 1
            count_above = position

        super(LazyFocusListWalker, self).set_focus(position)


class JsonFileDisplay(urwid.ListBox):
    def __init__(self, json_file, preview_keys):
        self.reader = LazyJsonReader(json_file)
        self.preview_keys = preview_keys

        # maximum number of loaded lines above AND below the cursor
        # TODO height of window / 2
        self.num_lines = 100

        body = []
        for i in range(0, self.num_lines):
            next_ob = self.reader.read_next()
            reader_position = self.reader._get_position()
            if next_ob is None:
                break
            body.append(
                self.build_item(next_ob, reader_position)
            )

        self.walker = LazyFocusListWalker(body, self)
        super(JsonFileDisplay, self).__init__(self.walker)


    def build_item(self, ob, meta):
        return urwid.AttrMap(
                    JsonObject(ob, meta=meta, hidden=True, preview_keys=self.preview_keys),
                    'json_row',
                    'json_row_h'
                )


class JsonReader(object):
    def __init__(self, file_path, preview_keys=None):
        self.file_path = file_path
        self.preview_keys = preview_keys if preview_keys else []

        palette = [
            ('I say', 'default,bold', 'default'),
            ('header', 'black', 'light green'),
            ('row_odd', 'white', 'dark gray'),

            ('json_row', 'dark gray', 'black'),
            ('json_row_h', 'white', 'black')
            #('json_row_h', 'light gray', 'dark blue', 'standout','#ff8', '#806')
            #('json_row_h', 'white', 'dark gray', '','#f0f', '#00f')
        ]

        header_buttons = [
            ('fixed', 13, urwid.Button("F1 Help")),
            ('fixed', 13, urwid.Button("F2 Load")),
            ('fixed', 15, urwid.Button("F3 Export")),
            ('fixed', 15, urwid.Button("F4 Filter")),
            ('fixed', 15, urwid.Button("F5 Reload")),
            ('fixed', 13, urwid.Button("F8 Exit")),
        ]

        _navColumns = urwid.Columns(header_buttons, dividechars=3, focus_column=None, min_width=1, box_columns=None)

        navColumns = urwid.AttrMap(_navColumns, 'header')

        self.main_display = JsonFileDisplay(self.file_path, self.preview_keys)
        mainFrame = urwid.Frame(self.main_display, header=navColumns, footer=None, focus_part='body')

        screen = urwid.raw_display.Screen()
        screen.set_terminal_properties(colors=256) # <-- not working?
        screen.register_palette(palette)
        self.loop = urwid.MainLoop(mainFrame, palette, unhandled_input=self.unhandled)

    def unhandled(self, key):
        if key in ['f8', 'q']:
            self.teardown()
            raise urwid.ExitMainLoop()
        elif key in ['f1', 'h']:
            pass # show help
        elif key in ['f2', 'l']:
            pass # load ?
        elif key in ['f3', 'e']:
            pass # export
        elif key in ['f4', 'f']:
            pass # filter
        elif key in ['f5', 'r']:
            pass # reload file from disk (?)

    def teardown(self):
        self.main_display.walker.async_loader.enabled = False

    def run(self):
        try:
            self.loop.run()
        except KeyboardInterrupt as e:
            self.teardown()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Graphical json structured log explorer")
    parser.add_argument('-p', '--preview-keys', type=lambda x: x.split(","), default=['_t', 'severity', 'event_name', '__time__'])
    parser.add_argument('file_path', nargs=1, help="File path to view")

    args = parser.parse_args()

    reader = JsonReader(args.file_path[0], preview_keys=args.preview_keys)
    reader.run()


if __name__ == '__main__':
    main()
