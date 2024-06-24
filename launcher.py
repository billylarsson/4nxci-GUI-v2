import pathlib,os
from PyQt6 import QtWidgets, QtCore, QtGui
import subprocess
from PyQt6.QtWidgets import QApplication
from styles import *
from widgets import StartBTN
import sys
from threadpool import CustomThreadPool, ThreadThenMain
from smartpos import *
from widgets import LineEditWithCanvas,TermOutput,FinalDestination

class Main(QtWidgets.QMainWindow):
    ready: bool = False
    def __init__(self, qapplication):
        self._qapplication = qapplication
        self.thread_then_main = ThreadThenMain()
        self.main_then_main = CustomThreadPool()
        super().__init__()
        self.setWindowTitle('4nxci GUI v0.something-something...')
        self.show()
        fn = lambda: self.screen_starting_geometry(x_factor=0.5)
        self.main_then_main(fn, self.draw_things, wait=0.1)


    def draw_things(self):

        bars: list = []
        for i in ['exe_path', 'keyfile_path', 'xcifile_path', 'tmp_dir', 'output_dir']:
            label = LineEditWithCanvas(self, settings_var=i)
            setattr(self, i, label)
            kwgs: dict = dict(below=bars[-1], y_offset=2) if bars else dict()
            pos(label, height=44, width=self, sub=8, left=4, top=4, **kwgs)
            style(label, background='rgb(40,40,40)', border='gray', color='white', font=14)
            label.expand()
            bars.append(label)

        for var, obj in [('term_output', TermOutput), ('final_destination', FinalDestination)]:
            label = obj(self)
            setattr(self, var, label)
            kwgs: dict = dict(below=bars[-1], y_offset=2) if bars else dict()
            pos(label, height=label.h, width=self, sub=8, left=4, top=4, **kwgs)
            style(label, background='black', border='gray', color='white', font=label.font_size)
            bars.append(label)

        pos(self, height=max(x.geometry().bottom() + 5 for x in bars))
        qsize: QtCore.QSize = self.size()
        self.setFixedSize(qsize)
        self.ready = True
        self.show_job()

    def get_free_tmp_dir(self) -> str:
        tmp_dir: str = self.tmp_dir.lineedit.text().rstrip(os.sep)
        extra: str = '4XNCI_TMP'
        free_tmp_dir: str = f'{tmp_dir}{os.sep}{extra}'
        add_num: int = 0
        while os.path.exists(free_tmp_dir):
            add_num += 1
            free_tmp_dir: str = f'{tmp_dir}{os.sep}{extra}_{add_num}'
        return free_tmp_dir

    def get_args(self) -> str:
        if self.ready:
            nxci: str = self.exe_path.lineedit.text().rstrip(os.sep)
            xci: str = self.xcifile_path.lineedit.text().rstrip(os.sep)
            keys: str = self.keyfile_path.lineedit.text().rstrip(os.sep)
            tmp_dir: str = self.tmp_dir.lineedit.text().rstrip(os.sep)
            output_dir: str = self.output_dir.lineedit.text().rstrip(os.sep)
            if all(os.path.exists(path) for path in [nxci, xci, keys, tmp_dir, output_dir]):
                free_tmp_dir: str = self.get_free_tmp_dir()
                return f'"{nxci}" -k "{keys}" -t "{free_tmp_dir}" -o "{output_dir}" "{xci}" -r'
        return ""

    def show_job(self):
        if self.ready:
            args: str = self.get_args()
            self.term_output.setText(args)
            try:
                self.start_btn
            except AttributeError:
                self.start_btn = StartBTN(self)
                pos(self.start_btn, size=[170, 30], bottom=self.term_output, y_offset=3, right=self.width())
                style(self.start_btn, background='green', border='black 2px', color='rgb(50,50,50)', bold=True)
                self.start_btn.setText('SEND TO TERMINAL')
            finally:
                if args:
                    self.start_btn.show()
                else:
                    self.start_btn.hide()


    def start_job(self):
        args: str = self.get_args()
        if args:
            output_dir: str = self.output_dir.lineedit.text()
            files: set = set()
            for walk in os.walk(output_dir):
                for fname in walk[-1]:
                    files.add(fname)

            free_tmp_dir: str = self.get_free_tmp_dir()
            pathobj = pathlib.Path(free_tmp_dir)
            pathobj.mkdir(parents=True, exist_ok=True)
            subprocess.call(args, shell=True)
            for walk in os.walk(output_dir):
                for fname in walk[-1]:
                    if fname not in files:
                        final: str = f'{output_dir}{os.sep}{fname}'
                        self.final_destination.show_final_destination(final)



    def screen_starting_geometry(self,
                                 x_factor: float = 0.8,
                                 y_factor: float = 0.8,
                                 primary: bool = True,
                                 fixed: bool = False,
                                 ):

        for screen in self._qapplication.screens():
            primary_screen: bool = screen == QtGui.QGuiApplication.primaryScreen()
            criteria1: bool = primary and primary_screen
            criteria2: bool = not primary and not primary_screen
            if not criteria1 and not criteria2:
                continue

            x: int = screen.geometry().left()
            y: int = screen.geometry().top()
            w: int = screen.geometry().width()
            h: int = screen.geometry().height()

            x_bleed: int = (w - int(w * x_factor)) // 2
            y_bleed: int = (h - int(h * y_factor)) // 2

            new_w: int = int(w * x_factor) or 1280
            new_h: int = int(h * y_factor) or 768

            x_cent: int = x_bleed + x
            y_cent: int = y_bleed + y

            if not fixed:
                self.setGeometry(x_cent, y_cent, new_w, new_h)
            else:
                self.setFixedSize(new_w, new_h)
                self.move(x_cent, y_cent)
            break
        else:
            self.setGeometry(0, 0, 1280, 768)  # fallback


if '__main__' in __name__:
    app = QApplication(sys.argv)
    ui = Main(qapplication=app)
    app.exec()