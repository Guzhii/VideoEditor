# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QDir, Qt, QUrl
from PyQt5.QtGui import QIcon, QIntValidator, QFont
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QAction, QComboBox, QFileDialog, QHBoxLayout,
                             QLabel, QMainWindow, QPushButton, QShortcut,
                             QSlider, QStyle, QVBoxLayout, QWidget, QLineEdit)
import sys

from utils import ffmpeg_convert_to_avi, ffmpeg_extract_subclip


class VideoWindow(QMainWindow):
    """ Class:
    Video player window.
    """

    # Main window size.
    WIN_SIZE = [800, 600]

    def __init__(self, parent=None):
        """ Function:
        Setup user interface of Video player window.
        """

        super(VideoWindow, self).__init__(parent)
        self.setWindowTitle("Video cutter")
        self.resize(VideoWindow.WIN_SIZE[0], VideoWindow.WIN_SIZE[1])
        self.setWindowIcon(
            self.style().standardIcon(QStyle.SP_DriveDVDIcon))

        self.video_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        self.record_start_time = "0:00"
        self.record_start_time_s = 0
        self.record_end_time = "0:00"
        self.record_end_time_s = 0
        self.record_time_intervals = []
        self.video_name = ""
        self.output_folder = ""

        self.widget_video = QVideoWidget()

        self.statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)

        self.button_play = QPushButton()
        self.button_play.setEnabled(False)
        self.button_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.button_play.clicked.connect(self.play_video)

        self.video_slider = QSlider(Qt.Horizontal)
        self.video_slider.setRange(0, 0)
        self.video_slider.sliderMoved.connect(self.set_position)
        self.video_duration = 0

        self.current_time = QLabel("0:00")
        self.total_time = QLabel("0:00")

        # Action 'Open'.
        self.action_open = QAction(QIcon('open.png'), '&Open', self)
        self.action_open.setShortcut('Ctrl+O')
        self.action_open.setStatusTip('Open a video')
        self.action_open.triggered.connect(self.open_video)

        # Menu bar.
        self.menu_bar = self.menuBar()
        self.menu_menu = self.menu_bar.addMenu('&Menu')
        self.menu_menu.addAction(self.action_open)

        # Widget.
        self.widget_window = QWidget(self)
        self.setCentralWidget(self.widget_window)

        self.layout_operation = QHBoxLayout()
        self.layout_operation.setContentsMargins(0, 0, 0, 0)
        self.choice_label = QLabel('Cut video by: ')
        self.choice = QComboBox()
        choice = ['fixed length (s)', 'adding marker']
        self.choice.addItems(choice)
        self.fixed_length = QLineEdit()
        self.onlyInt = QIntValidator()
        self.fixed_length.setValidator(self.onlyInt)
        self.button_starter = QPushButton('Select start time')
        self.button_ender = QPushButton('Select end time')
        self.button_process = QPushButton('Process')
        self.choice_label.setFixedWidth(70)
        self.layout_operation.addWidget(self.choice_label)
        self.choice.setFixedWidth(120)
        self.layout_operation.addWidget(self.choice)
        self.fixed_length.setFixedWidth(30)
        self.layout_operation.addWidget(self.fixed_length)
        self.button_starter.setEnabled(False)
        self.layout_operation.addWidget(self.button_starter)
        self.button_ender.setEnabled(False)
        self.layout_operation.addWidget(self.button_ender)
        self.button_process.setFixedWidth(150)
        self.layout_operation.addWidget(self.button_process)

        #self.layout_record = QHBoxLayout()
        #self.layout_record.setContentsMargins(0, 0, 0, 0)
        #self.button_start = QPushButton('Start')
        #self.button_end = QPushButton('End')
        #self.button_clear = QPushButton('Clear')
        #self.layout_record.addWidget(self.button_start)
        #self.layout_record.addWidget(self.button_end)
        #self.layout_record.addWidget(self.button_clear)

        self.button_starter.clicked.connect(self.record_start)
        self.button_ender.clicked.connect(self.record_end)

        self.button_process.clicked.connect(self.process)
        self.choice.currentTextChanged.connect(self.on_combobox_changed)

        # Widget layout.
        self.layout_widget = QHBoxLayout()
        self.layout_widget.setContentsMargins(0, 0, 0, 0)
        self.layout_widget.addWidget(self.button_play)
        self.layout_widget.addWidget(self.video_slider)
        self.current_time.setFixedHeight(10)
        self.total_time.setFixedHeight(10)
        self.layout_widget.addWidget(self.current_time)
        self.layout_widget.addWidget(self.total_time)

        self.layout_time = QHBoxLayout()
        self.time_interval = QLabel( self.record_start_time + ' - ' + self.record_end_time)
        self.time_interval.setFixedHeight(20)
        font = QFont("Calibri")
        font.setPointSize(20)
        self.time_interval.setFont(font)
        self.time_interval.setAlignment(Qt.AlignCenter)
        self.layout_time.addWidget(self.time_interval)
        self.button_add = QPushButton('Add')
        self.button_add.setFixedWidth(100)
        self.layout_time.addWidget(self.button_add)
        self.button_add.clicked.connect(self.add)

        self.layout_time_label = QHBoxLayout()
        self.time_label = QLabel("Time intervals selected: ")
        self.time_label.setFixedHeight(20)
        self.layout_time_label.addWidget(self.time_label)
        self.layout_time_intervals = QHBoxLayout()
        self.time_intervals = QLabel("")
        self.time_intervals.setFixedHeight(20)
        self.layout_time_intervals.addWidget(self.time_intervals)

        self.layout_window = QVBoxLayout()
        self.layout_window.addWidget(self.widget_video)
        #self.layout_window.addLayout(self.layout_record)
        self.layout_window.addLayout(self.layout_widget)
        self.layout_window.addLayout(self.layout_operation)


        # Window layout.
        self.widget_window.setLayout(self.layout_window)

        self.video_player.setVideoOutput(self.widget_video)
        self.video_player.stateChanged.connect(self.media_state_changed)
        self.video_player.positionChanged.connect(self.position_changed)
        self.video_player.durationChanged.connect(self.duration_changed)
        self.video_player.error.connect(self.error_control)

        QShortcut(Qt.Key_Up, self, self.arrow_up)
        QShortcut(Qt.Key_Down, self, self.arrow_down)
        QShortcut(Qt.Key_Left, self, self.arrow_left_event)
        QShortcut(Qt.Key_Right, self, self.arrow_right_event)
        QShortcut(Qt.Key_Space, self, self.play_video)

    def arrow_up(self):
        if self.video_player.state() != QMediaPlayer.StoppedState:
            self.video_player.setVolume(min(self.video_player.volume() + 10, 100))

    def arrow_down(self):
        if self.video_player.state() != QMediaPlayer.StoppedState:
            self.video_player.setVolume(max(self.video_player.volume() - 10, 0))

    def arrow_left_event(self):
        """ Slot function:
        Action after the key 'arrow left' is pressed.
        Fast-forward to 10 seconds later.
        """

        self.set_position(self.video_slider.value() - 10 * 1000)

    def arrow_right_event(self):
        """ Slot function:
        Action after the key 'arrow right' is pressed.
        Go back to 10 seconds ago.
        """

        self.set_position(self.video_slider.value() + 10 * 1000)

    def mousePressEvent(self, event):
        """ Slot function:
        The starting position of the slider is 50.
        Note: This function still can't not accurately move the slider to the
        clicked position.
        """

        slider_start_pos = self.video_slider.geometry().topLeft().x()
        if 42 <= self.height() - event.pos().y() <= 62:
            position = self.video_slider.minimum() + (
                        event.pos().x() - slider_start_pos) / self.video_slider.width() * self.video_duration
            if position != self.video_slider.sliderPosition():
                self.set_position(position)

    def on_combobox_changed(self):
        if self.choice.currentText() == 'fixed length (s)':
            self.fixed_length.setEnabled(True)
            self.button_starter.setEnabled(False)
            self.button_ender.setEnabled(False)
            self.layout_window.removeItem(self.layout_time)
            self.layout_window.removeItem(self.layout_time_label)
            self.layout_window.removeItem(self.layout_time_intervals)
            self.record_time_intervals = []
        elif self.choice.currentText() == 'adding marker':
            self.fixed_length.setEnabled(False)
            self.button_starter.setEnabled(True)
            self.button_ender.setEnabled(True)
            self.layout_window.addLayout(self.layout_time)
            self.layout_window.addLayout(self.layout_time_label)
            self.layout_window.addLayout(self.layout_time_intervals)

    def open_video(self):
        """ Slot function:
        Open a video from the file system.
        """

        video_name, _ = QFileDialog.getOpenFileName(self, "Select a video",
                                                    QDir.homePath())

        if video_name[-4:] == '.mp4':
            video_name = ffmpeg_convert_to_avi(video_name)

        self.video_name = video_name

        if self.video_name != '':
            self.video_player.setMedia(
                QMediaContent(QUrl.fromLocalFile(self.video_name)))
            self.button_play.setEnabled(True)
            self.video_player.play()
            self.video_player.pause()

            index = self.video_name.rfind('/')
            self.statusbar.showMessage(
                "Info: Open the video '" + self.video_name[(index + 1):]
                + "' ...")

        self.output_folder = str(QFileDialog.getExistingDirectory(self, "Select Output Directory")) + "/"

    def play_video(self):
        """ Slot function:
        The slot function for the 'play' button.
        If the video player is currently paused, then play the video;
        otherwise, pause the video.
        """

        if self.video_player.state() == QMediaPlayer.PlayingState:
            self.video_player.pause()
        else:
            self.video_player.play()

    def media_state_changed(self, state):
        """ Slot function:
        If the playing state changes, change the icon for the 'play' button.
        If the video player is currently playing, change the icon to 'pause';
        otherwise, change the icon to 'play'.
        """

        if self.video_player.state() == QMediaPlayer.PlayingState:
            self.button_play.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.button_play.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPlay))

    def position_changed(self, position):
        """ Slot function:
        Change the position of the slider.
        """

        self.video_slider.setValue(position)
        self.current_time.setText(str(int((position/1000)/60)) + ":" + "{:02d}".format(round((position/1000)%60)))

    def duration_changed(self, duration):
        """ Slot function:
        If the duration of the video changed, change the range of the slider.
        This slot function is called after opening a video.
        """

        self.video_slider.setRange(0, duration)
        self.video_duration = duration
        self.total_time.setText(str(int((duration/1000)/60)) + ":" + str(round((duration/1000)%60)))

    def set_position(self, position):
        """ Slot function:
        Change the progress of the video.
        """

        self.video_player.setPosition(position)

    def error_control(self):
        """ Slot function:
        If an error occurs while opening the video, this slot function is
        called.
        """

        self.button_play.setEnabled(False)
        self.statusbar.showMessage(
            "Error: An error occurs while opening the video.")

    def record_start(self):
        position = self.video_slider.sliderPosition()
        self.record_start_time = str(int((position/1000)/60)) + ":" + "{:02d}".format(round((position/1000)%60))
        self.time_interval.setText(self.record_start_time + ' - ' + self.record_end_time)
        self.record_start_time_s = position/1000
        self.statusbar.showMessage("Info: start time selected")

    def record_end(self):
        position = self.video_slider.sliderPosition()
        self.record_end_time = str(int((position / 1000) / 60)) + ":" + "{:02d}".format(round((position / 1000) % 60))
        self.time_interval.setText(self.record_start_time + ' - ' + self.record_end_time)
        self.record_end_time_s = position / 1000
        self.statusbar.showMessage("Info: end time selected")

    def add(self):
        self.record_time_intervals.append(str(self.record_start_time_s) + "-" + str(self.record_end_time_s))
        self.time_intervals.setText(str(self.record_time_intervals)[1:-1])
        self.statusbar.showMessage("Info: interval added")

    def record_clear(self):
        self.record_start_time = 0
        self.record_end_time = 0

        self.statusbar.showMessage(
            "Info: Starting time: ({}), and Ending time: ({}).".format(self.record_start_time, self.record_end_time))

    def process(self):
        if self.choice.currentText() == "fixed length (s)" and self.fixed_length.text() != "" :
            inc = int(self.fixed_length.text())
            i = 0
            times = []
            while i < self.video_duration/1000:
                tmp = i + inc
                t = str(i) + "-" + str(tmp)
                times.append(t)
                i = tmp

            for time in times:
                starttime = int(time.split("-")[0])
                endtime = int(time.split("-")[1])
                print(starttime, endtime)
                self.statusbar.showMessage("Info: The process is working on slice number {}.".format(str(times.index(time))))
                ffmpeg_extract_subclip(self.video_name,
                                       starttime,
                                       endtime,
                                       targetname = self.output_folder + str(times.index(time) + 1) + ".mp4")
                self.statusbar.showMessage("Info: process complete.")

        elif self.choice.currentText() == "adding marker" and self.record_time_intervals != [] :
            times = self.record_time_intervals
            for time in times:
                starttime = int(float(time.split("-")[0]))
                endtime = int(float(time.split("-")[1]))
                print(starttime, endtime)
                self.statusbar.showMessage("Info: The process is working on slice number {}.".format(str(times.index(time))))
                ffmpeg_extract_subclip(self.video_name,
                                       starttime,
                                       endtime,
                                       targetname = self.output_folder + str(times.index(time) + 1) + ".mp4")
                self.statusbar.showMessage("Info: process complete.")

if __name__ == '__main__':
    """
    app = QApplication(sys.argv) will go wrong.
    """
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)

    player = VideoWindow()
    player.show()

    """
    sys.exit(app.exec_()) will go wrong.
    """
    app.exec_()