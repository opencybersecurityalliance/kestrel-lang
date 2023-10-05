import sys
import re

from IPython.core.magic import (
    line_cell_magic,
    Magics,
    magics_class,
)

from kestrel.session import Session


@magics_class
class KestrelMagic(Magics):
    def __init__(self, shell=None, config=None, user_magics=None, **traits):
        super().__init__(shell=shell, config=config, user_magics=user_magics, **traits)
        self.session = None

    def __check_magic(self, line="", cell=None):
        """
        Some non-Kestrel commands to handle separately for initializing the session.
        This likely includes how to connect to UDI, ATK, and other parameters.
        """
        # regex is a simple hack
        r = r"^\s*(session)\s+(init)\s*(true|false)?\s*$"
        m = re.match(r, line, re.IGNORECASE)
        if m is None:
            return False
        stderr = m.groups()[2] is not None and m.groups()[2].lower() == "true"
        self.session = Session(stderr)
        return True

    @line_cell_magic
    def kestrel(self, line="", cell=None):
        """
        session init [true / false]
        """
        if self.__check_magic(line, cell):
            if len(line) > 0:
                line = ""
                if cell is None:
                    return

        if self.session is None:
            self.session = Session()
        if len(line) == 0 and cell is None:
            sys.stderr.write("Need to provide a Kestrel query to execute")
            return None
        if cell is None:
            # assert cell is None
            return self.session.execute(line)
        else:
            sys.stderr.write(repr(cell))
            if len(line) != 0:
                self.session.execute(line)
            return self.session.execute(cell)
        # indx = line.lower().find('as df')
        # if indx != -1:
        #     return pd.DataFrame.from_records(self.session.execute(line[:indx])[0])
        # else: return self.session.execute(line)


ip = get_ipython()
ip.register_magics(KestrelMagic)
