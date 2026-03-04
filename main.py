import sys
import os
import subprocess
import re
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QProgressBar,
                               QHBoxLayout, QLineEdit, QComboBox, QSpinBox, QCheckBox, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal

class VideoCompressor(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Advanced Video Compressor")
        self.setGeometry(100, 100, 600, 500)

        self.layout = QVBoxLayout()

        self.label = QLabel("Select video files to compress:")
        self.layout.addWidget(self.label)

        self.select_button = QPushButton("Select Video Files")
        self.select_button.clicked.connect(self.select_video_files)
        self.layout.addWidget(self.select_button)

        self.output_dir_layout = QHBoxLayout()
        self.output_dir_label = QLabel("Output Directory:")
        self.output_dir_layout.addWidget(self.output_dir_label)
        self.output_dir_lineedit = QLineEdit()
        self.output_dir_layout.addWidget(self.output_dir_lineedit)
        self.output_dir_button = QPushButton("Browse")
        self.output_dir_button.clicked.connect(self.select_output_directory)
        self.output_dir_layout.addWidget(self.output_dir_button)
        self.layout.addLayout(self.output_dir_layout)

        self.settings_layout = QVBoxLayout()

        self.codec_layout = QHBoxLayout()
        self.codec_label = QLabel("Codec:")
        self.codec_layout.addWidget(self.codec_label)
        self.codec_combobox = QComboBox()
        self.codec_combobox.addItems(["libx264", "libx265"])
        self.codec_layout.addWidget(self.codec_combobox)
        self.settings_layout.addLayout(self.codec_layout)

        self.crf_layout = QHBoxLayout()
        self.crf_label = QLabel("CRF:")
        self.crf_layout.addWidget(self.crf_label)
        self.crf_spinbox = QSpinBox()
        self.crf_spinbox.setRange(0, 51)
        self.crf_spinbox.setValue(23)
        self.crf_layout.addWidget(self.crf_spinbox)
        self.settings_layout.addLayout(self.crf_layout)

        self.bitrate_layout = QHBoxLayout()
        self.bitrate_label = QLabel("Video Bitrate (kbps):")
        self.bitrate_layout.addWidget(self.bitrate_label)
        self.bitrate_lineedit = QLineEdit("1000")
        self.bitrate_layout.addWidget(self.bitrate_lineedit)
        self.settings_layout.addLayout(self.bitrate_layout)

        self.audio_bitrate_layout = QHBoxLayout()
        self.audio_bitrate_label = QLabel("Audio Bitrate (kbps):")
        self.audio_bitrate_layout.addWidget(self.audio_bitrate_label)
        self.audio_bitrate_lineedit = QLineEdit("128")
        self.audio_bitrate_layout.addWidget(self.audio_bitrate_lineedit)
        self.settings_layout.addLayout(self.audio_bitrate_layout)

        self.preset_layout = QHBoxLayout()
        self.preset_label = QLabel("Preset:")
        self.preset_layout.addWidget(self.preset_label)
        self.preset_combobox = QComboBox()
        self.preset_combobox.addItems(["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"])
        self.preset_layout.addWidget(self.preset_combobox)
        self.settings_layout.addLayout(self.preset_layout)

        self.resolution_layout = QHBoxLayout()
        self.resolution_label = QLabel("Resolution:")
        self.resolution_layout.addWidget(self.resolution_label)
        self.resolution_combobox = QComboBox()
        self.resolution_combobox.addItems(["Same as source", "1920x1080", "1280x720", "640x480"])
        self.resolution_layout.addWidget(self.resolution_combobox)
        self.settings_layout.addLayout(self.resolution_layout)

        self.layout.addLayout(self.settings_layout)

        self.batch_processing_checkbox = QCheckBox("Batch Processing")
        self.layout.addWidget(self.batch_processing_checkbox)

        self.compress_button = QPushButton("Compress Video(s)")
        self.compress_button.clicked.connect(self.compress_videos)
        self.compress_button.setEnabled(False)
        self.layout.addWidget(self.compress_button)

        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar)

        self.setLayout(self.layout)

        self.video_files = []

    def select_video_files(self):
        options = QFileDialog.Options()
        file_names, _ = QFileDialog.getOpenFileNames(self, "Select Video Files", "", "Video Files (*.mp4 *.avi *.mkv);;All Files (*)", options=options)
        if file_names:
            self.video_files = file_names
            self.label.setText(f"Selected {len(self.video_files)} file(s)")
            self.compress_button.setEnabled(True)

    def select_output_directory(self):
        options = QFileDialog.Options()
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory", options=options)
        if directory:
            self.output_dir_lineedit.setText(directory)

    def compress_videos(self):
        if not self.video_files:
            QMessageBox.warning(self, "Warning", "No video files selected.")
            return

        output_dir = self.output_dir_lineedit.text()
        if not output_dir:
            QMessageBox.warning(self, "Warning", "Please select an output directory.")
            return

        codec = self.codec_combobox.currentText()
        crf = self.crf_spinbox.value()
        video_bitrate = self.bitrate_lineedit.text()
        audio_bitrate = self.audio_bitrate_lineedit.text()
        preset = self.preset_combobox.currentText()
        resolution = self.resolution_combobox.currentText()

        self.compress_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.label.setText("Compressing videos...")

        # Start the compression in a separate thread
        self.compressor_thread = VideoCompressorThread(self.video_files, output_dir, codec, crf, video_bitrate, audio_bitrate, preset, resolution)
        self.compressor_thread.progress_updated.connect(self.update_progress)
        self.compressor_thread.finished.connect(self.compression_finished)
        self.compressor_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def compression_finished(self):
        self.label.setText("Compression completed!")
        self.compress_button.setEnabled(True)

class VideoCompressorThread(QThread):
    progress_updated = Signal(int)

    def __init__(self, video_files, output_dir, codec, crf, video_bitrate, audio_bitrate, preset, resolution):
        super().__init__()
        self.video_files = video_files
        self.output_dir = output_dir
        self.codec = codec
        self.crf = crf
        self.video_bitrate = video_bitrate
        self.audio_bitrate = audio_bitrate
        self.preset = preset
        self.resolution = resolution

    def run(self):
        total_files = len(self.video_files)
        for index, video_file in enumerate(self.video_files):
            output_file = os.path.join(self.output_dir, os.path.splitext(os.path.basename(video_file))[0] + "_compressed.mp4")
            command = [
                'ffmpeg',
                '-i', video_file,
                '-vcodec', self.codec,
                '-crf', str(self.crf),
                '-b:v', self.video_bitrate + 'k',
                '-b:a', self.audio_bitrate + 'k',
                '-preset', self.preset,
            ]

            if self.resolution != "Same as source":
                command.extend(['-vf', f'scale={self.resolution}'])

            command.append(output_file)

            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            duration_pattern = re.compile(r"Duration: (\d{2}:\d{2}:\d{2}\.\d{2})")
            time_pattern = re.compile(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})")

            duration = None
            while True:
                output = process.stderr.readline()
                if process.poll() is not None:
                    break
                if output:
                    print(output.strip())
                    duration_match = duration_pattern.search(output)
                    if duration_match:
                        duration = self.parse_time(duration_match.group(1))
                    if duration:
                        time_match = time_pattern.search(output)
                        if time_match:
                            current_time = self.parse_time(time_match.group(1))
                            progress = int((current_time / duration) * 100)
                            self.progress_updated.emit(progress)

            self.progress_updated.emit(100)

    def parse_time(self, time_str):
        h, m, s = map(float, time_str.split(':'))
        return h * 3600 + m * 60 + s

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoCompressor()
    window.show()
    sys.exit(app.exec())
