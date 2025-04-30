import os
import sys
import subprocess
import re
import shutil
from pathlib import Path
from youtubesearchpython import VideosSearch
import yt_dlp

class SongProcessorSilent:
    """A version of SongProcessor that doesn't use Rich console output and works silently"""
    
    def __init__(self, base_dir="SongProcessor"):
        self.base_dir = Path(base_dir)
        self.dirs = {
            "downloads": self.base_dir / "downloads",
            "vocals": self.base_dir / "vocals",
            "temp": self.base_dir / "temp"
        }
        for d in self.dirs.values():
            d.mkdir(parents=True, exist_ok=True)
        self.config = {'max_search_results': 5}

    def search_youtube(self, query):
        """Search YouTube without console output"""
        try:
            results = VideosSearch(query, limit=self.config['max_search_results']).result().get('result', [])
            return results
        except Exception:
            return []

    def download_audio(self, video):
        """Download audio without console output"""
        url = video['link']
        safe_title = re.sub(r'[\\/*?:"<>|]', '', video['title']).replace(' ', '_')
        outpath = self.dirs['downloads'] / f"{safe_title}.mp3"
        
        if outpath.exists():
            return outpath
            
        opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(self.dirs['downloads'] / '%(title)s.%(ext)s'),
            'postprocessors': [{ 'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320' }],
            'quiet': True,
            'no_warnings': True
        }
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
            orig = Path(os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3")
            if orig != outpath:
                shutil.move(orig, outpath)
            return outpath
        except Exception:
            return None

    def extract_vocals_demucs(self, audio_file):
        """Extract vocals with Demucs without console output"""
        audio_path = Path(audio_file)
        stem = audio_path.stem
        out = self.dirs['vocals'] / f"{stem}_acapella.mp3"
        
        if out.exists():
            return out
            
        try:
            # Redirect output to null
            with open(os.devnull, 'w') as devnull:
                subprocess.run(
                    [sys.executable, '-m', 'demucs.separate', '--two-stems=vocals', 
                     '-o', str(self.dirs['temp']/ 'demucs'), str(audio_path)],
                    check=True, stdout=devnull, stderr=devnull
                )
                
            sep_dir = self.dirs['temp']/ 'demucs'/ 'htdemucs'/ stem
            wav = sep_dir/ 'vocals.wav'
            
            # Convert to MP3
            with open(os.devnull, 'w') as devnull:
                subprocess.run(
                    ['ffmpeg', '-y', '-i', str(wav), '-b:a', '320k', str(out)],
                    check=True, stdout=devnull, stderr=devnull
                )
                
            return out
        except Exception:
            return None

    def extract_vocals_ffmpeg(self, audio_file):
        """Extract vocals with FFmpeg without console output"""
        audio_path = Path(audio_file)
        stem = audio_path.stem
        out = self.dirs['vocals'] / f"{stem}_acapella_ffmpeg.mp3"
        
        if out.exists():
            return out
            
        try:
            with open(os.devnull, 'w') as devnull:
                subprocess.run(
                    ['ffmpeg', '-y', '-i', str(audio_path),
                    '-af', 'pan=mono|c0=c0-c1',
                    str(out)],
                    check=True, stdout=devnull, stderr=devnull
                )
            return out
        except Exception:
            return None