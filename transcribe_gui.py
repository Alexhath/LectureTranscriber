#!/usr/bin/env python3
import os
import sys
import shlex
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QTextEdit, QComboBox,
    QCheckBox, QMessageBox, QProgressBar, QFrame, QListView
)

# ──────────────────────────────────────────────
# STILI MODERNI (Tailwind-inspired Dark Mode)
# ──────────────────────────────────────────────
MODERN_QSS = """
QWidget {
    background-color: #0F172A;
    color: #F8FAFC;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 14px;
}

QFrame#ControlsFrame {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 12px;
}
QFrame#ControlsFrame QLabel, QFrame#ControlsFrame QCheckBox {
    background-color: transparent;
}

QPushButton {
    background-color: #3B82F6;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 10px 18px;
    font-weight: 600;
}
QPushButton:hover { background-color: #2563EB; }
QPushButton:disabled { background-color: #334155; color: #94A3B8; }

QPushButton#SecondaryBtn { background-color: #475569; }
QPushButton#SecondaryBtn:hover { background-color: #334155; }

QPushButton#StartBtn {
    background-color: #10B981; 
    color: #FFFFFF; /* Testo forzato a bianco */
}
QPushButton#StartBtn:hover { background-color: #059669; }
QPushButton#StartBtn:disabled { background-color: #064E3B; color: #9CA3AF; }

QPushButton#StopBtn { background-color: #EF4444; }
QPushButton#StopBtn:hover { background-color: #DC2626; }

QComboBox {
    background-color: #0F172A;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 6px 12px;
    color: #F8FAFC;
    min-width: 90px;
    min-height: 24px;
}
QComboBox:hover { border-color: #3B82F6; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView, QListView {
    background-color: #1E293B;
    border: 1px solid #475569;
    color: #F8FAFC;
    outline: none;
}
QListView::item { background-color: #1E293B; color: #F8FAFC; padding: 8px; }
QListView::item:hover, QListView::item:selected { background-color: #3B82F6; color: white; }

QTextEdit {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 12px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 13px;
    color: #CBD5E1;
}
QCheckBox { spacing: 8px; }
QCheckBox::indicator {
    width: 18px; height: 18px; border-radius: 4px;
    border: 1px solid #475569; background-color: #0F172A;
}
QCheckBox::indicator:checked { background-color: #3B82F6; border-color: #3B82F6; }
QProgressBar {
    border: none; background-color: #1E293B; border-radius: 4px;
    height: 6px; text-align: center; color: transparent;
}
QProgressBar::chunk { background-color: #10B981; border-radius: 4px; }
"""

class TranscribeWorker(QThread):
    line = Signal(str)
    finished_ok = Signal(Path)
    finished_err = Signal(str)

    def __init__(self, video_path: Path, transcribe_py: Path, model: str, language: str, keep_audio: bool):
        super().__init__()
        self.video_path = video_path
        self.transcribe_py = transcribe_py
        self.model = model
        self.language = language
        self.keep_audio = keep_audio
        
        self.proc = None
        self._is_cancelled = False

    def run(self):
        if not self.transcribe_py.exists():
            self.finished_err.emit(f"Impossibile trovare transcribe.py in: {self.transcribe_py}")
            return

        cmd = [
            sys.executable,
            str(self.transcribe_py),
            str(self.video_path),
            "--model", self.model,
            "--language", self.language,
        ]
        if self.keep_audio:
            cmd.append("--keep-audio")

        try:
            self.line.emit("⚙️ Esecuzione:\n  " + " ".join(shlex.quote(c) for c in cmd) + "\n")
            self.proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, universal_newlines=True,
            )
            
            assert self.proc.stdout is not None
            for out_line in self.proc.stdout:
                if self._is_cancelled: break
                self.line.emit(out_line.rstrip("\n"))
            
            rc = self.proc.wait()
            
            if self._is_cancelled: self.finished_err.emit("⚠️ Trascrizione interrotta dall'utente.")
            elif rc == 0: self.finished_ok.emit(self.video_path)
            else: self.finished_err.emit(f"Trascrizione fallita (codice uscita {rc}). Controlla i log.")
        except Exception as e:
            self.finished_err.emit(f"Errore durante l'avvio della trascrizione: {e}")

    def stop(self):
        self._is_cancelled = True
        if self.proc: self.proc.terminate()


class DropArea(QLabel):
    file_dropped = Signal(Path)

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.set_default_state()

    def set_default_state(self):
        self.setAcceptDrops(True)
        self.setText("📁 Trascina qui un video (.mp4)\noppure usa il pulsante in basso")
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #475569; border-radius: 12px;
                background-color: #1E293B; padding: 30px;
                font-size: 16px; color: #94A3B8;
            }
            QLabel:hover { border-color: #3B82F6; background-color: #1e2e4a; color: #F8FAFC; }
        """)

    def set_locked_state(self, filename: str):
        self.setAcceptDrops(False)
        self.setText(f"✅ Video Caricato:\n{filename}")
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #10B981; border-radius: 12px;
                background-color: #064E3B; padding: 30px;
                font-size: 18px; color: #F8FAFC; font-weight: bold;
            }
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
        else: event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls: return
        path = Path(urls[0].toLocalFile())
        if path.exists(): self.file_dropped.emit(path)


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lecture Transcriber")
        self.resize(880, 650)
        self.setStyleSheet(MODERN_QSS)

        self.selected_video: Path | None = None
        self.worker: TranscribeWorker | None = None
        self.transcribe_py = Path(__file__).parent / "transcribe.py"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        header = QLabel("Lecture Transcriber ✨")
        header.setStyleSheet("font-size: 26px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(header)

        self.drop = DropArea()
        self.drop.file_dropped.connect(self.set_video)
        layout.addWidget(self.drop)

        controls_frame = QFrame()
        controls_frame.setObjectName("ControlsFrame")
        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setContentsMargins(20, 20, 20, 20)
        controls_layout.setSpacing(16)

        info_layout = QHBoxLayout()
        self.file_label = QLabel("Nessun file selezionato")
        self.file_label.setStyleSheet("color: #94A3B8; font-style: italic;")
        info_layout.addWidget(self.file_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        info_layout.addWidget(self.progress_bar)
        controls_layout.addLayout(info_layout)

        settings_layout = QHBoxLayout()
        
        # Bottone "Scegli Video" (che diventerà "Rimuovi")
        self.choose_btn = QPushButton("Scegli Video...")
        self.choose_btn.setObjectName("SecondaryBtn")
        self.choose_btn.clicked.connect(self.handle_file_button)
        settings_layout.addWidget(self.choose_btn)

        settings_layout.addSpacing(10)
        settings_layout.addWidget(QLabel("Modello:"))
        self.model_box = QComboBox()
        self.model_box.addItems(["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"])
        self.model_box.setCurrentText("base")
        self.model_box.setView(QListView())
        settings_layout.addWidget(self.model_box)

        settings_layout.addSpacing(10)
        settings_layout.addWidget(QLabel("Lingua:"))
        self.lang_box = QComboBox()
        self.lang_box.addItems(["en", "it", "auto"])
        self.lang_box.setCurrentText("auto")
        self.lang_box.setView(QListView())
        settings_layout.addWidget(self.lang_box)

        settings_layout.addSpacing(10)
        self.keep_audio = QCheckBox("Mantieni .wav")
        self.keep_audio.setChecked(False)
        settings_layout.addWidget(self.keep_audio)
        settings_layout.addStretch(1)

        self.transcribe_btn = QPushButton("Inizia Trascrizione")
        self.transcribe_btn.setObjectName("StartBtn")
        self.transcribe_btn.clicked.connect(self.start_transcription)
        self.transcribe_btn.setEnabled(False)
        settings_layout.addWidget(self.transcribe_btn)

        self.stop_btn = QPushButton("Ferma 🛑")
        self.stop_btn.setObjectName("StopBtn")
        self.stop_btn.clicked.connect(self.stop_transcription)
        self.stop_btn.hide()
        settings_layout.addWidget(self.stop_btn)

        controls_layout.addLayout(settings_layout)
        layout.addWidget(controls_frame)

        log_label = QLabel("Output di Sistema:")
        log_label.setStyleSheet("color: #94A3B8; font-size: 13px; font-weight: 600;")
        layout.addWidget(log_label)
        
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

    def append_log(self, text: str):
        self.log.append(text)
        scrollbar = self.log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def handle_file_button(self):
        # Gestisce il doppio ruolo del pulsante (Scegli / Rimuovi)
        if self.selected_video is None:
            self.choose_video()
        else:
            self.clear_video()

    def clear_video(self):
        self.selected_video = None
        self.file_label.setText("Nessun file selezionato")
        self.file_label.setStyleSheet("color: #94A3B8; font-style: italic;")
        
        # Ripristina l'interfaccia
        self.drop.set_default_state()
        self.transcribe_btn.setEnabled(False)
        
        # Trasforma il bottone indietro a "Scegli Video"
        self.choose_btn.setObjectName("SecondaryBtn")
        self.choose_btn.style().unpolish(self.choose_btn)
        self.choose_btn.style().polish(self.choose_btn)
        self.choose_btn.setText("Scegli Video...")
        
        self.append_log("🗑️ Video rimosso. Pronto per un nuovo file.")

    def set_video(self, path: Path):
        if path.suffix.lower() not in [".mp4", ".mov", ".avi", ".mkv", ".webm"]:
            QMessageBox.warning(self, "Formato Sconosciuto", f"L'estensione {path.suffix} potrebbe non essere supportata.\nProverò comunque.")
        self.selected_video = path
        self.file_label.setText(f"🎬 Pronto: {path.name}")
        self.file_label.setStyleSheet("color: #10B981; font-weight: bold;")
        
        # Blocca l'area di drop e mostra il file
        self.drop.set_locked_state(path.name)
        self.transcribe_btn.setEnabled(True)
        
        # Trasforma il bottone "Scegli" in "Rimuovi" (Rosso)
        self.choose_btn.setObjectName("StopBtn")
        self.choose_btn.style().unpolish(self.choose_btn)
        self.choose_btn.style().polish(self.choose_btn)
        self.choose_btn.setText("Rimuovi Video ✖")

        # Notifica nei log
        self.append_log(f"📎 Video selezionato con successo: {path.name}")

    def choose_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleziona video", str(Path.home()),
            "Video files (*.mp4 *.mov *.avi *.mkv *.webm);;All files (*)"
        )
        if file_path:
            self.set_video(Path(file_path))

    def start_transcription(self):
        if not self.selected_video: return

        self.transcribe_btn.hide()
        self.stop_btn.show()
        self.stop_btn.setEnabled(True)
        self.choose_btn.setEnabled(False) # Disabilita la rimozione durante il processo
        self.model_box.setEnabled(False)
        self.lang_box.setEnabled(False)
        
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)
        
        self.append_log("\n" + "━"*50)
        self.append_log("🚀 Avvio processo di trascrizione...")

        model = self.model_box.currentText()
        language = self.lang_box.currentText()
        keep_audio = self.keep_audio.isChecked()

        self.worker = TranscribeWorker(
            self.selected_video, self.transcribe_py,
            model, language, keep_audio
        )
        self.worker.line.connect(self.append_log)
        self.worker.finished_ok.connect(self.on_done_ok)
        self.worker.finished_err.connect(self.on_done_err)
        self.worker.start()

    def stop_transcription(self):
        if self.worker and self.worker.isRunning():
            self.append_log("\n🛑 Invio segnale di arresto al processo...")
            self.stop_btn.setEnabled(False)
            self.worker.stop()

    def reset_ui_state(self):
        self.choose_btn.setEnabled(True)
        self.model_box.setEnabled(True)
        self.lang_box.setEnabled(True)
        
        self.stop_btn.hide()
        self.transcribe_btn.show()
        self.transcribe_btn.setEnabled(True)
        
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_bar.hide()

    def notify(self, title: str, message: str):
        try: subprocess.run(["notify-send", title, message], check=False)
        except Exception: pass

    def on_done_ok(self, video_path: Path):
        self.append_log("\n✅ Trascrizione completata con successo!")
        self.notify("Trascrizione completata", f"File finito: {video_path.name}")
        self.reset_ui_state()

    def on_done_err(self, err: str):
        self.append_log(f"\n❌ {err}")
        self.notify("Avviso di Trascrizione", "Processo interrotto o fallito.")
        self.reset_ui_state()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    w = App()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()