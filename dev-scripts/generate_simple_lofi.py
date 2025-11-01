#!/usr/bin/env python3
"""
Generate Simple Lofi Anime Music Track

Creates a working lofi anime ambient track for the interactive world.
"""

import numpy as np
import wave
import os


class SimpleLofiGenerator:
    """Generate simple but effective lofi anime music"""

    def __init__(self, sample_rate=44100, duration_minutes=3):  # Shorter for testing
        self.sample_rate = sample_rate
        self.duration_minutes = duration_minutes
        self.duration_seconds = duration_minutes * 60
        self.num_samples = sample_rate * self.duration_seconds

        # Pentatonic scale frequencies (lofi friendly)
        self.scale = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25]  # C, D, E, G, A, C

    def generate_sine_wave(self, frequency, duration, amplitude=0.1):
        """Generate a sine wave"""
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        return amplitude * np.sin(2 * np.pi * frequency * t)

    def apply_simple_envelope(self, signal, attack=0.1, release=0.1):
        """Apply simple envelope"""
        length = len(signal)
        attack_samples = int(attack * length)
        release_samples = int(release * length)

        envelope = np.ones(length)
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        envelope[-release_samples:] = np.linspace(1, 0, release_samples)

        return signal * envelope

    def generate_lofi_pad(self, frequency, duration):
        """Generate soft lofi pad"""
        # Main frequency with harmonics
        main = self.generate_sine_wave(frequency, duration, 0.3)
        octave = self.generate_sine_wave(frequency * 2, duration, 0.15)
        fifth = self.generate_sine_wave(frequency * 1.5, duration, 0.1)

        pad = main + octave + fifth
        pad = self.apply_simple_envelope(pad, attack=1.0, release=1.0)

        # Add some warmth
        warmth = np.random.normal(0, 0.01, len(pad))
        pad += warmth

        return pad

    def generate_melody(self, duration):
        """Generate simple lofi melody"""
        melody = np.zeros(int(self.sample_rate * duration))
        note_duration = 2.0  # 2 seconds per note
        num_notes = int(duration / note_duration)

        # Simple melody pattern
        pattern = [0, 2, 4, 2, 5, 4, 2, 0]  # Pentatonic pattern

        for i in range(num_notes):
            note_idx = pattern[i % len(pattern)]
            freq = self.scale[note_idx] if note_idx < len(self.scale) else self.scale[0]

            note = self.generate_sine_wave(freq, note_duration * 0.8, 0.1)
            note = self.apply_simple_envelope(note, attack=0.2, release=0.2)

            start_sample = int(i * note_duration * self.sample_rate)
            end_sample = start_sample + len(note)
            if end_sample <= len(melody):
                melody[start_sample:end_sample] += note * 0.5

        return melody

    def generate_rhythm(self, duration):
        """Generate simple lofi rhythm"""
        rhythm = np.zeros(int(self.sample_rate * duration))
        beat_duration = 1.0
        num_beats = int(duration / beat_duration)

        for i in range(num_beats):
            start_sample = int(i * beat_duration * self.sample_rate)

            # Soft kick on beat 1
            if i % 4 == 0:
                kick = np.random.normal(0, 0.2, int(0.2 * self.sample_rate))
                kick *= np.exp(-np.linspace(0, 15, len(kick)))
                end_sample = start_sample + len(kick)
                if end_sample <= len(rhythm):
                    rhythm[start_sample:end_sample] += kick

            # Hi-hat on off-beats
            if i % 2 == 1:
                hihat = np.random.normal(0, 0.05, int(0.05 * self.sample_rate))
                hihat *= np.exp(-np.linspace(0, 25, len(hihat)))
                end_sample = start_sample + len(hihat)
                if end_sample <= len(rhythm):
                    rhythm[start_sample:end_sample] += hihat

        return rhythm

    def generate_complete_track(self):
        """Generate the complete track"""
        print("🎵 Generating lofi anime track...")

        track = np.zeros(self.num_samples)

        # Chord progression (simple repeating pattern)
        chords = [
            (261.63, 4.0),  # C
            (392.00, 4.0),  # G
            (329.63, 4.0),  # E
            (440.00, 4.0),  # A
        ]

        progression_duration = sum(duration for _, duration in chords)
        num_progressions = int(self.duration_seconds / progression_duration)

        for i in range(num_progressions):
            for freq, duration in chords:
                start_time = i * progression_duration + sum(d for _, d in chords[:chords.index((freq, duration))])

                if start_time < self.duration_seconds:
                    actual_duration = min(duration, self.duration_seconds - start_time)
                    pad = self.generate_lofi_pad(freq, actual_duration)
                    start_sample = int(start_time * self.sample_rate)
                    end_sample = start_sample + len(pad)
                    if end_sample <= len(track):
                        track[start_sample:end_sample] += pad * 0.3

        # Add melody
        print("   Adding melody...")
        melody = self.generate_melody(self.duration_seconds)
        track += melody * 0.2

        # Add rhythm
        print("   Adding rhythm...")
        rhythm = self.generate_rhythm(self.duration_seconds)
        track += rhythm * 0.15

        # Add lofi noise
        print("   Adding lofi warmth...")
        noise = np.random.normal(0, 0.008, len(track))
        track += noise

        # Normalize and limit
        max_val = np.max(np.abs(track))
        if max_val > 0:
            track = track / max_val * 0.8
            track = np.tanh(track) * 0.8

        print("   ✅ Track complete!")
        return track

    def save_as_wav(self, signal, filename):
        """Save as WAV file"""
        print(f"💾 Saving as {filename}...")

        # Convert to 16-bit
        signal_int16 = (signal * 32767).astype(np.int16)

        with wave.open(filename, 'w') as wav_file:
            wav_file.setnchannels(2)  # Stereo
            wav_file.setsampwidth(2)   # 16-bit
            wav_file.setframerate(self.sample_rate)

            # Stereo (duplicate mono)
            stereo = np.column_stack((signal_int16, signal_int16))
            wav_file.writeframes(stereo.tobytes())

        size_mb = os.path.getsize(filename) / (1024 * 1024)
        print(f"   ✅ Saved! Size: {size_mb:.1f} MB")


def main():
    """Generate the lofi track"""
    print("🎧 Simple Lofi Anime Music Generator")
    print("=" * 40)

    # Create music directory
    os.makedirs('music', exist_ok=True)

    # Generate track
    generator = SimpleLofiGenerator(
        sample_rate=44100,
        duration_minutes=3  # 3 minutes for faster generation
    )

    track = generator.generate_complete_track()

    # Save
    output_file = 'music/eternal_study.wav'
    generator.save_as_wav(track, output_file)

    print(f"\n🎉 Success!")
    print(f"📁 File: {output_file}")
    print(f"📊 Size: {os.path.getsize(output_file) / (1024*1024):.1f} MB")
    print(f"⏱️  Duration: {generator.duration_minutes} minutes")

    return output_file


if __name__ == "__main__":
    main()
