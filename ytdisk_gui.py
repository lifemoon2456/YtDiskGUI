"""واجهة سطح مكتب محلية لمشروع YTDISK."""
import shutil
import sys
import traceback
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFormLayout, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPushButton, QProgressBar, QSpinBox, QTabWidget, QTextEdit,
    QVBoxLayout, QWidget,
)

import ytdisk


APP_TITLE = "YTDISK — تخزين تجريبي داخل فيديو"


class Worker(QObject):
    progress = Signal(int, int)
    message = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, mode, source, destination, password, block=4, nsym=32):
        super().__init__()
        self.mode, self.source, self.destination = mode, source, destination
        self.password, self.block, self.nsym = password, block, nsym

    def run(self):
        try:
            if not shutil.which("ffmpeg"):
                raise RuntimeError("لم يتم العثور على FFmpeg. ثبّته ثم أعد تشغيل التطبيق.")

            def report(current, total):
                self.progress.emit(current, total)

            if self.mode == "encode":
                meta = ytdisk.encode_file(self.source, self.destination, self.block,
                                           self.nsym, self.password or None, report)
                self.finished.emit(True, f"اكتمل إنشاء الفيديو: {self.destination}\n"
                                   f"الملف الأصلي: {meta['name']}")
            else:
                ok, output = ytdisk.decode_video(self.source, self.destination,
                                                  self.password or None, report)
                self.finished.emit(ok, f"اكتمل الاسترجاع: {output}" if ok else
                                   "لم يكتمل الاسترجاع. راجع كلمة المرور وجودة الفيديو.")
        except Exception as error:
            self.message.emit(traceback.format_exc())
            self.finished.emit(False, f"حدث خطأ: {error}")


class PathPicker(QWidget):
    def __init__(self, caption, choose_file=True, save_file=False, parent=None):
        super().__init__(parent)
        self.choose_file, self.save_file = choose_file, save_file
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.field = QLineEdit()
        self.field.setPlaceholderText(caption)
        button = QPushButton("اختيار…")
        button.clicked.connect(self.pick)
        layout.addWidget(self.field, 1)
        layout.addWidget(button)

    def pick(self):
        if self.save_file:
            path, _ = QFileDialog.getSaveFileName(self, "حفظ الفيديو", self.field.text() or "upload.mp4", "MP4 (*.mp4)")
        elif self.choose_file:
            path, _ = QFileDialog.getOpenFileName(self, "اختيار ملف", self.field.text(), "كل الملفات (*.*)")
        else:
            path = QFileDialog.getExistingDirectory(self, "اختيار مجلد", self.field.text())
        if path:
            self.field.setText(path)

    def text(self):
        return self.field.text().strip()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.thread = None
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(720, 560)
        self.setLayoutDirection(Qt.RightToLeft)
        self.build_ui()

    def build_ui(self):
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setSpacing(14)
        title = QLabel("YTDISK")
        title.setObjectName("title")
        subtitle = QLabel("واجهة محلية لتحويل الملفات إلى فيديو 4K واستعادتها — للاستخدام التعليمي فقط")
        subtitle.setWordWrap(True)
        credit = QLabel("مبني على مشروع YtDisk الأصلي من Ahmed Sameh (ahmedfox1) — مرخّص MIT")
        credit.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(credit)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.encoder_tab(), "إنشاء فيديو")
        self.tabs.addTab(self.decoder_tab(), "استرجاع ملف")
        layout.addWidget(self.tabs, 1)

        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.status = QLabel("جاهز. تأكد من تثبيت FFmpeg قبل البدء.")
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setVisible(False)
        layout.addWidget(self.progress)
        layout.addWidget(self.status)
        layout.addWidget(self.log)
        self.setCentralWidget(root)
        self.setStyleSheet("""
            QMainWindow { background: #101827; color: #e5edf8; }
            QWidget { font-size: 14px; } QLabel { color: #d7e2f0; }
            #title { font-size: 30px; font-weight: 700; color: #6ee7b7; }
            QGroupBox { border: 1px solid #334155; border-radius: 8px; margin-top: 12px; padding: 12px; }
            QGroupBox::title { subcontrol-origin: margin; right: 12px; padding: 0 5px; }
            QLineEdit, QSpinBox, QComboBox, QTextEdit { background: #1e293b; border: 1px solid #475569; border-radius: 5px; padding: 7px; color: white; }
            QPushButton { background: #0f766e; border: 0; border-radius: 5px; color: white; padding: 8px 16px; font-weight: 600; }
            QPushButton:hover { background: #0d9488; } QPushButton:disabled { background: #475569; }
            QProgressBar { border: 1px solid #475569; border-radius: 5px; text-align: center; } QProgressBar::chunk { background: #10b981; }
        """)

    def encoder_tab(self):
        page, form = QWidget(), QFormLayout()
        page.setLayout(form)
        self.encode_source = PathPicker("اختر الملف المراد تحويله")
        self.encode_output = PathPicker("مكان حفظ ملف MP4", save_file=True)
        self.encode_password = QLineEdit(); self.encode_password.setEchoMode(QLineEdit.Password)
        self.encode_password.setPlaceholderText("اختياري — AES-256-GCM")
        self.block = QComboBox(); self.block.addItem("4 × 4 — الإعداد الموصى به", 4); self.block.addItem("8 × 8 — حماية أعلى وسعة أقل", 8)
        self.nsym = QSpinBox(); self.nsym.setRange(0, 128); self.nsym.setValue(32)
        self.encode_button = QPushButton("إنشاء فيديو 4K")
        self.encode_button.clicked.connect(self.start_encode)
        note = QLabel("ستنتج العملية فيديو 4K كبيرًا وقد تحتاج وقتًا طويلًا. لا تستخدم YouTube كنسخة احتياطية موثوقة.")
        note.setWordWrap(True)
        form.addRow("الملف:", self.encode_source); form.addRow("الفيديو الناتج:", self.encode_output)
        form.addRow("كلمة المرور:", self.encode_password); form.addRow("حجم البلوك:", self.block); form.addRow("تصحيح الأخطاء:", self.nsym)
        form.addRow("", self.encode_button); form.addRow(note)
        return page

    def decoder_tab(self):
        page, form = QWidget(), QFormLayout()
        page.setLayout(form)
        self.decode_source = PathPicker("اختر فيديو YTDISK")
        self.decode_output = PathPicker("اختر مجلد الحفظ", choose_file=False)
        self.decode_password = QLineEdit(); self.decode_password.setEchoMode(QLineEdit.Password)
        self.decode_password.setPlaceholderText("اكتبها فقط إذا شُفّر الملف")
        self.decode_button = QPushButton("استرجاع الملف")
        self.decode_button.clicked.connect(self.start_decode)
        form.addRow("الفيديو:", self.decode_source); form.addRow("مجلد الحفظ:", self.decode_output)
        form.addRow("كلمة المرور:", self.decode_password); form.addRow("", self.decode_button)
        return page

    def start_encode(self):
        source, destination = self.encode_source.text(), self.encode_output.text()
        if not source or not Path(source).is_file() or not destination:
            return self.warn("اختر ملفًا صحيحًا وحدد مكان حفظ الفيديو.")
        if Path(source).resolve() == Path(destination).resolve():
            return self.warn("لا يمكن أن يكون الملف المصدر والفيديو الناتج نفس المسار.")
        self.launch("encode", source, destination, self.encode_password.text(), self.block.currentData(), self.nsym.value())

    def start_decode(self):
        source, destination = self.decode_source.text(), self.decode_output.text()
        if not source or not Path(source).is_file() or not destination:
            return self.warn("اختر فيديو صحيحًا ومجلد حفظ.")
        self.launch("decode", source, destination, self.decode_password.text())

    def launch(self, mode, source, destination, password, block=4, nsym=32):
        self.set_busy(True); self.log.clear(); self.log.setVisible(False); self.progress.setRange(0, 0)
        self.status.setText("جارٍ تنفيذ العملية… لا تغلق التطبيق.")
        self.thread = QThread(self)
        self.worker = Worker(mode, source, destination, password, block, nsym)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.update_progress)
        self.worker.message.connect(self.show_log)
        self.worker.finished.connect(self.operation_finished)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def update_progress(self, current, total):
        self.progress.setRange(0, total); self.progress.setValue(current)
        self.status.setText(f"جارٍ المعالجة: {current:,} / {total:,} إطار")

    def show_log(self, text):
        self.log.setPlainText(text); self.log.setVisible(True)

    def operation_finished(self, success, message):
        self.set_busy(False); self.status.setText(message)
        if success: QMessageBox.information(self, "YTDISK", message)
        else: QMessageBox.warning(self, "YTDISK", message)

    def set_busy(self, busy):
        self.encode_button.setDisabled(busy); self.decode_button.setDisabled(busy)
        if not busy: self.progress.setRange(0, 100); self.progress.setValue(100)

    def warn(self, text):
        QMessageBox.warning(self, "بيانات ناقصة", text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("YTDISK")
    window = MainWindow(); window.show()
    sys.exit(app.exec())
