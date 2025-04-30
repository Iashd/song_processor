# song_processor_launcher.pyw
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from song_processor_gui import SongProcessorGUI

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application icon at the app level too (affects taskbar on Windows)
    try:
        # Get base path whether running as script or frozen exe
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        # Try several possible icon locations
        icon_paths = [
            os.path.join(base_path, "vocalremover.ico"),
            os.path.join(base_path, ".ico"),
            os.path.join(base_path, "vocalremover.ico"),
            os.path.join(os.path.dirname(base_path), "vocalremover.ico")
        ]
        
        # Use the first icon found
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                app.setWindowIcon(QIcon(icon_path))
                break
    except Exception:
        pass  # Continue without icon if there's an error
    
    # Create and show the main window
    window = SongProcessorGUI()
    window.show()
    sys.exit(app.exec_())