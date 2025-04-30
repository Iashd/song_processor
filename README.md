### **song_processor**

This is a WIP python script that allows you to:
* Search for a song on YouTube
* Download the song
* Extract the vocals
* Save the vocals

It allows you to automatically get vocals from any given song in a matter of seconds, and works... *somewhat* flawlessly.

I created this using Claude 3.7 and it surprisingly worked, so I am uploading it here for anybody who would like to try it out and maybe I inspire others to create something better.

### Tutorial:
1. Run the `.exe` in the `\Dist` folder  
   OR  
   Run the `.pyw` file.
2. Type the name of a song
3. Confirm the song, then wait
4. Check the vocals folder

### How It Works

The application uses a combination of tools to extract vocals:
1. Searches YouTube using the `youtube-search-python` library
2. Downloads the audio using `yt-dlp`
3. Primary method: Extracts vocals using `Demucs` (AI-based source separation)
4. Fallback method: Uses `FFmpeg`'s center channel isolation technique

### Requirements

**Dependencies:**
- Python 3.6+
- PyQt5
- youtube-search-python
- yt-dlp
- Demucs
- FFmpeg

**Installation:**
```bash
pip install PyQt5 youtube-search-python yt-dlp demucs
```

Install FFmpeg from your operating system's package manager or from [ffmpeg.org](https://ffmpeg.org/download.html).

### Project Structure

- `song_processor_gui.py`: Main GUI application
- `song_processor_launcher.pyw`: Launcher script (use this to start the application)
- `song_processor_silent.py`: Backend processing logic
- `\Dist`: Contains compiled executable (if available)

### Known Limitations

- Extraction quality depends on the original mix
- Demucs processing can be slow on computers without GPU acceleration
- FFmpeg fallback method is less effective but faster

### License

This project is open source and available for anyone to use and modify.
