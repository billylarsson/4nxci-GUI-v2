import shutil,os
from database import db
from PyQt6.QtGui import QFont, QFontMetrics
from PyQt6           import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QLabel
from smartpos import *
from styles   import *


def add(
        val: [int | float],
        factor: float = 0.0,
        min_add: int = 1,
        max_add: int = 255,
        min_val: int = 0,
        max_val: int = 255,
) -> int:
    if factor == 0.0:
        add_val: int = min_add
    else:
        add_val: int = int(val * factor)

    add_val = min(add_val, max_add)
    add_val = max(min_add, add_val)

    v: int = int(val) + add_val

    v = min(max_val, v)
    v = max(v, min_val)
    return v


def sub(
        val: [int | float],
        factor: float = 0.0,
        min_sub: int = 1,
        max_sub: int = 255,
        min_val: int = 0,
        max_val: int = 255,
) -> int:
    if factor == 0.0:
        sub_val: int = min_sub
    else:
        sub_val: int = int(val * factor)

    sub_val = min(sub_val, max_sub)
    sub_val = max(min_sub, sub_val)

    v: int = int(val) - sub_val

    v = min(max_val, v)
    v = max(v, min_val)
    return v


class Base(QLabel):
    def __init__(self, master, monospace: bool = False, *args, **kwargs):
        self.master = master
        super().__init__(master, *args, **kwargs)

        if monospace:
            font: QFont = QFont('monospace')
            self.setFont(font)

        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.show()

class CustomLineEdit(QtWidgets.QLineEdit):
    def __init__(self, master, *args, **kwargs):
        self.master = master
        super().__init__(master, *args, **kwargs)
        self.setContentsMargins(5, 0, 0, 0)
        style(self, background='transparent', color='white', border='transparent', font=14)
        font: QFont = QFont('monospace')
        self.setFont(font)
        self.show()


    def text_size(self) -> tuple:
        text: str = self.text()
        font: QFont = self.font()
        metrics: QFontMetrics = QtGui.QFontMetrics(font)
        bound = metrics.boundingRect(text)
        return bound.width(), bound.height()

    def text_height(self) -> int:
        _, height = self.text_size()
        return height

    def text_width(self) -> int:
        width, _ = self.text_size()
        return width
    def keyPressEvent(self, *args):
        self.setReadOnly(False)
        super().keyPressEvent(*args)
        self.setReadOnly(True)

    def text_changed(self, *args, **kwargs):
        text: str = self.text().strip()
        db.save(self.master.settings_var, text)

        try:
            self.shade.setText(text)
        except AttributeError:

            if text:
                self.shade: CustomLineEdit = CustomLineEdit(self.master, text=text)
                self.shade.keyPressEvent = lambda *args: None
                self.shade.lower()

                pos(self.shade, size=self, sub=4, left=1, top=3)
                copy_stylesheet(self.shade, self, color='rgba(30, 30, 30, 255)')

        if (self.text_width() + 10) > self.width():
            self.shade.hide()
        else:
            self.shade.show()

        if self.master.settings_var.endswith('dir'):
            self.create_dir_size_label()
            if os.path.isdir(text):
                _, _, free = shutil.disk_usage(text)
                free: float = round(free / 1_000_000_000, 2)
                self.size_label.setText(f"{free} GB FREE")
            else:
                self.size_label.setText('')

        elif self.master.settings_var.endswith('path'):
            self.create_file_size_label()
            if os.path.isfile(text):
                size: int = os.path.getsize(text)
                shrt_size: float = round(size / 1_000_000_000, 2) if size > 100_000_000 else round(size / 1_000_000, 2)
                size_str: str = str(shrt_size) + '00'
                size_str = size_str[: size_str.rfind('.') + 3]
                self.size_label.setText(f"{size_str} {'GB' if size > 100_000_000 else 'MB'} FILE")
            else:
                self.size_label.setText('')

        self.master.master.show_job()

    def create_file_size_label(self):
        self.create_size_label()
        style(self.size_label, background='transparent', color='rgb(210,200,150)', font=12)

    def create_dir_size_label(self):
        self.create_size_label()
        style(self.size_label, background='transparent', color='rgb(200,150,120)', font=12)

    def create_size_label(self):
        try:
            self.size_label
        except AttributeError:
            self.size_label = Base(self.master)
            align_flags = QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignBottom
            self.size_label.setAlignment(align_flags)
            width: int = 150
            pos(self.size_label, height=self, width=width, right=self.width() - 5)


class LineEditWithCanvas(Base):
    def __init__(self, master, settings_var: str):
        self.settings_var: str = settings_var
        super().__init__(master)

    def enterEvent(self, event):
        try:
            style(self.tooltip_label.tooltip_text, color='white')
        except AttributeError:
            return

        try:
            self.lineedit.size_label
        except AttributeError:
            return

        if self.settings_var.endswith('dir'):
            style(self.lineedit.size_label, color='orange')
        else:
            style(self.lineedit.size_label, color='yellow')

    def leaveEvent(self, a0):
        try:
            style(self.tooltip_label.tooltip_text, color='rgb(190,190,190)')
        except AttributeError:
            return

        try:
            self.lineedit.size_label
        except AttributeError:
            return

        if self.settings_var.endswith('dir'):
            style(self.lineedit.size_label, color='rgb(200,150,120)')
        else:
            style(self.lineedit.size_label, color='rgb(210,200,150)')
    def expand(self):
        self.create_lineedit()
        self.create_tooltip()

    def create_lineedit(self):
        self.lineedit: QtWidgets.QLineEdit = CustomLineEdit(self)
        pos(self.lineedit, size=self, sub=2, left=1, top=1)
        self.lineedit.textChanged.connect(self.lineedit.text_changed)
        if db.load_setting(self.settings_var):
            text: str = db.load_setting(self.settings_var)
            self.lineedit.setText(text)

    def create_tooltip(self):
        tooltip: Base = Base(self.master)
        tooltip_text: Base = Base(tooltip)
        self.tooltip_label = tooltip
        self.tooltip_label.tooltip_text = tooltip_text
        style(tooltip_text, background='transparent', color='rgb(190,190,190)', font=6)
        pos(tooltip, height=self.height() * 0.65, width=100, top=self, right=self.width(), y_offset=2)
        pos(tooltip_text, size=tooltip)
        align_flags = QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignTop
        tooltip_text.setAlignment(align_flags)
        texts: dict = dict(
            exe_path='executable 4XNCI',
            keyfile_path='prod.keys file',
            xcifile_path='XCI-image file',
            tmp_dir='working directory',
            output_dir='output directory'
        )
        for k in texts:
            if self.settings_var in k:
                tooltip_text.setText(texts[k])

class BaseVar(Base):
    def __init__(self, master):
        super().__init__(master)
        align_flags = QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignLeft
        self.setAlignment(align_flags)
        self.setContentsMargins(5, 0, 0, 0)
        self.setWordWrap(True)

class TermOutput(BaseVar):
    h: int = 79
    font_size: int = 10
    settings_var: str = 'term_output'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        align_flags = QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft
        self.setAlignment(align_flags)
        self.setContentsMargins(3, 3, 3, 3)
        self.setWordWrap(True)
        interact_flags = QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        self.setTextInteractionFlags(interact_flags)

class FinalDestination(BaseVar):
    h: int = 44
    font_size: int = 14
    settings_var: str = 'final_destination'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        interact_flags = QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        self.setTextInteractionFlags(interact_flags)

    def show_final_destination(self, final: str):
        self.setText(final)
        style(self, color='orange')
        try:
            self.size_label
        except AttributeError:
            self.size_label = Base(self)
            align_flags = QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignBottom
            self.size_label.setAlignment(align_flags)
            width: int = 150
            pos(self.size_label, height=self, width=width, right=self.width() - 5)
            style(self.size_label, background='transparent', color='rgb(210,200,150)', font=12)
            tooltip: Base = Base(self.master)
            tooltip_text: Base = Base(tooltip)
            self.tooltip_label = tooltip
            self.tooltip_label.tooltip_text = tooltip_text
            style(tooltip_text, background='transparent', color='rgb(190,190,190)', font=6)
            pos(tooltip, height=self.height() * 0.65, width=100, top=self, right=self.width(), y_offset=2)
            pos(tooltip_text, size=tooltip)
            align_flags = QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignTop
            tooltip_text.setAlignment(align_flags)
            tooltip_text.setText('NSP filesize')
        finally:
            size: int = os.path.getsize(final)
            shrt_size: float = round(size / 1_000_000_000, 2) if size > 100_000_000 else round(size / 1_000_000, 2)
            size_str: str = str(shrt_size) + '00'
            size_str = size_str[: size_str.rfind('.') + 3]
            self.size_label.setText(f"{size_str} {'GB' if size > 100_000_000 else 'MB'}")
class StartBTN(Base):
    def enterEvent(self, event):
        style(self, background='lightGreen', color='rgb(10,10,10)')
    def leaveEvent(self, a0):
        style(self, background='green', color='rgb(50,50,50)')
    def mouseReleaseEvent(self, ev):
        if ev.button().value == 1:
            self.master.start_job()