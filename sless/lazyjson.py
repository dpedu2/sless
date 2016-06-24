try:
    import ujson as json
except:
    import json
from gzip import GzipFile
import pdb
import logging


class LazyJsonReader(object):

    chunk_size = 2048

    """Newline-separated json log reader tolerating massive log files"""
    def __init__(self, file_path, file_gzipped=False):
        self.gz = file_gzipped
        self.file = GzipFile(file_path, 'rb') if file_gzipped else open(file_path, 'rb')
        """
        As bytes are read from the file a line count is kept. At any time we know:
        * the position of our pointer in the file's contents
        * what line number we are on
        So, it should be possible to fetch the previous/next line with some crafty seeking
        """
        self.line = 0

    def _get_position(self):
        """
        Return set of (current_line, current_file_position)
        """
        return (self.line, self.file.tell())

    def _seek_to(self, line, pos):
        """
        Seek to arbitrary locations. There's no logic here, this method assumes the line number and position specified
        are correct.
        """
        self.line = line
        self.file.seek(pos)

    def decode(self, s):
        return s.decode('UTF-8')

    def read_next(self):
        """
        Read the next line from the file, parse and return. Returns None if out of lines.
        """
        data = self.file.readline().strip()
        if data:
            self.line += 1
        try:
            return json.loads(self.decode(data)) if data else None
        except:
            logging.info("Bad line: {}".format(data))
            pdb.set_trace()

    def read_prev(self):
        """
        Read the previous line from the file, parse and return. Returns None if out of lines.
        """
        original_pos = current_pos = self.file.tell()

        # can't fall off the beginning
        if current_pos == 0:
            return None

        # rewind by chunk_size and read chunk_size bytes
        # repeat until we've found TWO \n - the end of the previous line, and the beginning of the line before the line we want
        # then split n grab
        #print(current_pos)
        rewound_chunk = b""
        while rewound_chunk.count(b"\n") < 3: # changed from 2 to 3 to fix partial reads
            before_jump = current_pos

            # Jump backwards x bytes, and prevent falling off the start
            current_pos = max(0, current_pos-self.chunk_size)
            self.file.seek(current_pos)
            jumped_by = before_jump-current_pos

            # prepend the chunk to our buffer
            rewound_chunk = b''.join([self.file.read(jumped_by), rewound_chunk])
            #rewound_chunk = ''.join([rewound_chunk, '|||||', self.file.read(jumped_by)])
            #print("Read ", jumped_by)

            # If we just read from the beginning of the file this loop should break regardless
            if current_pos == 0:
                break

        # we have a chunk containing at least one full line
        # find the last line in the chunk
        lines_split = rewound_chunk.split(b"\n")

        # -1 => blank
        # -2 => last line emitted
        # -3 => previous line. wont exist if we hit BOF
        # -4+ => line before that and/or partial line garbage
        if len(lines_split) < 3:
            self.line = 0
            self.file.seek(0)
            try:
                return json.loads(self.decode(lines_split[0]))
            except:
                logging.info("Bad line: {}".format(self.decode(lines_split[0])))
                pdb.set_trace()
        prev_line = lines_split[-2]

        # Calculate how far backwards we jumped, seek to the beginning of the line we're returning
        # TODO should it be elsewhere so if next_line is called we dont get this line again?
        after_prev_line = lines_split[-1:]
        rewound_len = len(b"\n".join([prev_line] + after_prev_line))
        self.file.seek(original_pos - rewound_len)
        self.line -= 1
        try:
            return json.loads(self.decode(prev_line))
        except:
            logging.info("Bad line: {}".format(self.decode(prev_line)))
            pdb.set_trace()

def test():
    import pdb
    from time import time

    #reader = LazyJsonReader("./query_api_server.log.20160527t012105.gz", file_gzipped=True)
    #reader = LazyJsonReader("./query_api_server.log.20160527t012105")
    reader = LazyJsonReader("./numbers.json")
    #reader = LazyJsonReader("./test.json.gz", file_gzipped=True)
    #reader = LazyJsonReader("./test.json")

    #print(">>>", reader.read_next())
    #print(">>>", reader.read_prev())



    # Read until EOF
    line_count = 0 # should match our position in the file
    lines_read = 0 # total count of lines read
    lines_rev = 0 # total count of lines read in reverse
    while True:
        line = reader.read_next()
        if line is None:
            break
        if line["number"] != line_count:
            print("Skipped a line!")
            pdb.set_trace()
        line_count+=1
        lines_read+=1

    print("line_count: ", line_count)
    print("lines_read: ", lines_read)
    print("lines_rev:  ", lines_rev)
    print("-------------")
    #line_count-=1
    # Read until BOF
    while True:
        line = reader.read_prev()
        if line is None:
            break
        line_count-=1
        if line["number"] != line_count:
            print("Skipped a line!")
            pdb.set_trace()
        lines_rev +=1

    print("line_count: ", line_count)
    print("lines_read: ", lines_read)
    print("lines_rev:  ", lines_rev)
    # Counts much match
    pdb.set_trace()






    burn_lines = 5000
    last_line = None
    start = time()
    for i in range(0, burn_lines):
        last_line = reader.read_next()
        #print(last_line)
    end = time()

    print("Burned {} lines in {}".format(burn_lines, round(end-start, 2)))

    print("Line:", reader.line, "Pos:", reader.file.tell())

    #print(reader.read_prev())

    start = time()
    while True:
        x = reader.read_prev()
        #print(x)
        if x == None:
            break
    end = time()
    print("Unburned {} lines in {}".format(burn_lines, round(end-start, 2)))

    pdb.set_trace()

if __name__ == '__main__':
    test()

