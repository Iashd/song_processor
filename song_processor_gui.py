import sys
import os
import threading
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QListWidget, QListWidgetItem, QProgressBar, 
                            QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QIcon

# Import silent song processor
from song_processor_silent import SongProcessorSilent

class WorkerSignals(QObject):
    """Define signals available for the worker thread."""
    progress = pyqtSignal(str, int)  # Message, percent
    finished = pyqtSignal(str, str)  # Result type, result path
    error = pyqtSignal(str)
    search_results = pyqtSignal(list)
    
class ProcessThread(threading.Thread):
    """Thread for running the song processor operations."""
    def __init__(self, processor, operation, args=None):
        threading.Thread.__init__(self)
        self.processor = processor
        self.operation = operation
        self.args = args or {}
        self.signals = WorkerSignals()
        self.daemon = True  # Thread will close when main program exits
        
    def run(self):
        try:
            if self.operation == "search":
                self.signals.progress.emit("Searching YouTube...", 0)
                results = self.processor.search_youtube(self.args["query"])
                self.signals.search_results.emit(results)
                self.signals.progress.emit("Search complete", 100)
                
            elif self.operation == "process":
                video = self.args["video"]
                # Download audio
                self.signals.progress.emit(f"Downloading: {video['title']}", 10)
                audio_path = self.processor.download_audio(video)
                if not audio_path:
                    self.signals.error.emit("Download failed")
                    return
                    
                # Extract vocals with Demucs
                self.signals.progress.emit("Extracting vocals (this may take a few minutes)...", 40)
                vocals_path = self.processor.extract_vocals_demucs(audio_path)
                
                # Fallback to FFmpeg if Demucs fails
                if not vocals_path:
                    self.signals.progress.emit("Trying alternative extraction method...", 60)
                    vocals_path = self.processor.extract_vocals_ffmpeg(audio_path)
                
                if vocals_path:
                    self.signals.finished.emit("vocals", str(vocals_path))
                    self.signals.progress.emit("Vocal extraction complete!", 100)
                else:
                    self.signals.error.emit("Vocal extraction failed")
                    
        except Exception as e:
            self.signals.error.emit(f"Error: {str(e)}")

class SongProcessorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.processor = SongProcessorSilent()
        self.search_results = []
        self.set_application_icon()
        self.init_ui()
        
    def set_application_icon(self):
        """Set the application icon for the window and taskbar"""
        try:
            # First try to find icon in the executable's directory
            if getattr(sys, 'frozen', False):
                # Running as compiled exe
                base_path = sys._MEIPASS
            else:
                # Running in a normal Python environment
                base_path = os.path.dirname(os.path.abspath(__file__))
                
            # Try several possible icon locations and names
            icon_paths = [
                os.path.join(base_path, "vocalremover.ico"),
                os.path.join(base_path, ".ico"),
                os.path.join(base_path, "vocalremover.ico"),
                os.path.join(os.path.dirname(base_path), "vocalremover.ico")
            ]
            
            # Use the first icon found
            for icon_path in icon_paths:
                if os.path.exists(icon_path):
                    app_icon = QIcon(icon_path)
                    self.setWindowIcon(app_icon)
                    break
        except Exception:
            # If there's any error, just continue without an icon
            pass
        
    def init_ui(self):
        # Set window properties
        self.setWindowTitle("Song Processor")
        self.setGeometry(100, 100, 800, 600)
        
        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Search section
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter song name and artist...")
        self.search_input.returnPressed.connect(self.search_songs)
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.search_songs)
        search_layout.addWidget(self.search_input, 7)
        search_layout.addWidget(search_button, 1)
        main_layout.addLayout(search_layout)
        
        # Results section
        results_label = QLabel("Search Results:")
        results_label.setFont(QFont("Arial", 12, QFont.Bold))
        main_layout.addWidget(results_label)
        
        self.results_list = QListWidget()
        self.results_list.setMinimumHeight(200)
        self.results_list.itemDoubleClicked.connect(self.process_selected)
        main_layout.addWidget(self.results_list)
        
        # Process button
        self.process_button = QPushButton("Process Selected Song")
        self.process_button.setEnabled(False)
        self.process_button.clicked.connect(self.process_selected)
        main_layout.addWidget(self.process_button)
        
        # Progress section
        progress_label = QLabel("Progress:")
        progress_label.setFont(QFont("Arial", 12, QFont.Bold))
        main_layout.addWidget(progress_label)
        
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        
        # Output section
        output_layout = QHBoxLayout()
        self.output_path_label = QLabel("No output yet")
        open_folder_button = QPushButton("Open Output Folder")
        open_folder_button.clicked.connect(self.open_output_folder)
        output_layout.addWidget(self.output_path_label, 7)
        output_layout.addWidget(open_folder_button, 1)
        main_layout.addLayout(output_layout)
        
    def search_songs(self):
        query = self.search_input.text()
        if not query:
            QMessageBox.warning(self, "Warning", "Please enter a search query")
            return
            
        # Clear previous results
        self.results_list.clear()
        self.search_results = []
        self.process_button.setEnabled(False)
        self.status_label.setText("Searching...")
        self.progress_bar.setValue(0)
        
        # Start search thread
        search_thread = ProcessThread(
            self.processor, 
            "search",
            {"query": query}
        )
        search_thread.signals.progress.connect(self.update_progress)
        search_thread.signals.search_results.connect(self.display_results)
        search_thread.signals.error.connect(self.show_error)
        search_thread.start()
        
    def display_results(self, results):
        self.search_results = results
        if not results:
            self.results_list.addItem("No results found")
            return
            
        for i, video in enumerate(results):
            item_text = f"{video['title']} - {video['channel']['name']} ({video.get('duration', '')})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, i)  # Store index for reference
            self.results_list.addItem(item)
            
        self.process_button.setEnabled(True)
        
    def process_selected(self):
        selected_items = self.results_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a song from the list")
            return
            
        selected_index = selected_items[0].data(Qt.UserRole)
        selected_video = self.search_results[selected_index]
        
        # Update UI
        self.status_label.setText(f"Processing: {selected_video['title']}")
        self.progress_bar.setValue(0)
        self.process_button.setEnabled(False)
        
        # Start processing thread
        process_thread = ProcessThread(
            self.processor,
            "process",
            {"video": selected_video}
        )
        process_thread.signals.progress.connect(self.update_progress)
        process_thread.signals.finished.connect(self.process_finished)
        process_thread.signals.error.connect(self.show_error)
        process_thread.start()
        
    @pyqtSlot(str, int)
    def update_progress(self, message, percent):
        self.status_label.setText(message)
        self.progress_bar.setValue(percent)
        
    @pyqtSlot(str, str)
    def process_finished(self, result_type, result_path):
        self.output_path_label.setText(result_path)
        self.process_button.setEnabled(True)
        QMessageBox.information(self, "Success", f"Processing complete!\nOutput saved to: {result_path}")
        
    @pyqtSlot(str)
    def show_error(self, error_message):
        self.status_label.setText(f"Error: {error_message}")
        self.process_button.setEnabled(True)
        QMessageBox.critical(self, "Error", error_message)
        
    def open_output_folder(self):
        path = Path(self.output_path_label.text())
        if path.exists():
            folder_path = path.parent
            if sys.platform == 'win32':
                os.startfile(folder_path)
            elif sys.platform == 'darwin':  # macOS
                import subprocess
                subprocess.Popen(['open', folder_path])
            else:  # Linux
                import subprocess
                subprocess.Popen(['xdg-open', folder_path])
        else:
            # Default to opening the vocals folder
            folder_path = self.processor.dirs['vocals']
            if sys.platform == 'win32':
                os.startfile(folder_path)
            elif sys.platform == 'darwin':  # macOS
                import subprocess
                subprocess.Popen(['open', folder_path])
            else:  # Linux
                import subprocess
                subprocess.Popen(['xdg-open', folder_path])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SongProcessorGUI()
    window.show()
    sys.exit(app.exec_())