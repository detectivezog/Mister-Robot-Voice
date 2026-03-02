import customtkinter as ctk
import threading
import winsound
import os
import re
import numpy as np
import wave
from samtts import SamTTS

class SamManualControl(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("S.A.M. Manual Lab")
        self.geometry("800x700")

        self.sam = SamTTS()
        self.temp_wav = "sam_chunk.wav"
        self.is_playing = False

        # --- UI LAYOUT ---
        self.text_area = ctk.CTkTextbox(self, font=("Courier", 14))
        self.text_area.pack(padx=20, pady=20, fill="both", expand=True)
        self.text_area.insert("0.0", "Type a very long story here. I will now process it sentence by sentence so I do not crash. " * 5)

        self.slider_frame = ctk.CTkFrame(self)
        self.slider_frame.pack(pady=10, fill="x", padx=20)

        # Parameter Sliders
        self.speed = self.create_slider("Speed (Lower=Faster)", 40, 150, 72, 0)
        self.pitch = self.create_slider("Pitch", 15, 100, 64, 1)
        self.mouth = self.create_slider("Mouth", 0, 255, 128, 2)
        self.throat = self.create_slider("Throat", 0, 255, 128, 3)
        self.volume = self.create_slider("Volume", 0, 1, 0.8, 4)

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=20)

        self.play_btn = ctk.CTkButton(self.btn_frame, text="▶ Start Reading", command=self.start_reading, fg_color="#2ecc71")
        self.play_btn.pack(side="left", padx=10)

        self.stop_btn = ctk.CTkButton(self.btn_frame, text="⏹ Stop", command=self.stop_reading, fg_color="#e74c3c")
        self.stop_btn.pack(side="left", padx=10)

    def create_slider(self, label, start, end, default, row):
        ctk.CTkLabel(self.slider_frame, text=label).grid(row=row, column=0, padx=10, sticky="w")
        slider = ctk.CTkSlider(self.slider_frame, from_=start, to=end)
        slider.set(default)
        slider.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        self.slider_frame.grid_columnconfigure(1, weight=1)
        return slider

    def start_reading(self):
        if not self.is_playing:
            self.is_playing = True
            text = self.text_area.get("1.0", "end-1c").strip()
            # Split text by punctuation to avoid SAM's internal buffer crash
            chunks = re.split(r'(?<=[.!?])\s+', text)
            threading.Thread(target=self._read_chunks, args=(chunks,), daemon=True).start()

    def _read_chunks(self, chunks):
        for chunk in chunks:
            if not self.is_playing or not chunk.strip():
                break
            
            try:
                # Update SAM with slider values
                self.sam.speed = int(self.speed.get())
                self.sam.pitch = int(self.pitch.get())
                self.sam.mouth = int(self.mouth.get())
                self.sam.throat = int(self.throat.get())
                
                # Save and Scale Volume
                self.sam.save(chunk, self.temp_wav)
                self._apply_volume(self.temp_wav, self.volume.get())
                
                # Blocking play (winsound blocks the thread until finished)
                winsound.PlaySound(self.temp_wav, winsound.SND_FILENAME)
            except Exception as e:
                print(f"Synthesis error on chunk: {e}")
        
        self.is_playing = False

    def _apply_volume(self, filename, volume):
        with wave.open(filename, 'rb') as wav:
            params = wav.getparams()
            frames = wav.readframes(wav.getnframes())
            samples = np.frombuffer(frames, dtype=np.uint8).astype(np.float32)
            samples = (samples - 128) * volume + 128
            samples = np.clip(samples, 0, 255).astype(np.uint8)
        with wave.open(filename, 'wb') as wav:
            wav.setparams(params)
            wav.writeframes(samples.tobytes())

    def stop_reading(self):
        self.is_playing = False
        winsound.PlaySound(None, winsound.SND_PURGE) # Immediate stop

if __name__ == "__main__":
    app = SamManualControl()
    app.mainloop()