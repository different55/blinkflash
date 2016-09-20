# Original script by: Will Yager
# http://yager.io/LEDStrip/LED.html
# Mod by Different55 <burritosaur@protonmail.com>
# Seriously he did like 99% of the work here, all I changed was the
# device it outputs to and changed the way it outputs the info.
# This dude's amazing, definitely check him out.

loop = False
sensitivity = 1.3

import pyaudio as pa
import numpy as np
import sys
from blinkstick import blinkstick
import notes_scaled_nosaturation
from time import sleep, time, localtime
from colorsys import hsv_to_rgb

audio_stream = pa.PyAudio().open(format=pa.paInt16, \
								channels=2, \
								rate=44100, \
								input=True, \
								# Uncomment and set this using find_input_devices.py
								# if default input device is not correct
								#input_device_index=2, \
								frames_per_buffer=1024)

# Convert the audio data to numbers, num_samples at a time.
def read_audio(audio_stream, num_samples):
	while True:
		# Read all the input data. 
		samples = audio_stream.read(num_samples) 
		# Convert input data to numbers
		samples = np.fromstring(samples, dtype=np.int16).astype(np.float)
		samples_l = samples[::2]  
		samples_r = samples[1::2]
		yield samples_l, samples_r


stick = blinkstick.find_first()
count = stick.get_led_count()

#print(count)
def send_to_stick(strip):
	stick.set_led_data(0, strip)

if __name__ == '__main__':

	audio = read_audio(audio_stream, num_samples=1024)
	leds = notes_scaled_nosaturation.process(audio, num_leds=count, num_samples=1024, sample_rate=44100, sensitivity=sensitivity)
		
	last_frame = [0]*count # For smooth transitions, we need to know what things looked like last frame.
	
	sent = 0
	#print(leds)
	for frame in leds:
		data = []
		size = []
			
		brightness = 0
		brightest = 0
		totalsize = 0
		
		for i in range(count): # First pass, let's get an idea of how loud things are.
			brightness = brightness + frame[i]
			if frame[i] > frame[brightest]:
				brightest = i
				
		for i in range(count): # Second pass, let's try and figure out the rough size of each section.
			if brightness == 0:
				frame[i] = 1
				size.append(1)
				totalsize = totalsize + 1
				continue
			try:
				size.append(int(frame[i]/brightness*count))
				totalsize = totalsize+size[-1]
			except ValueError:
				pass
		
		if brightness == 0:
			brightness = count
		
		while totalsize < count: # Third pass, adjust the size of each section so that it properly fills the strip. There's probably a thousand better ways to do this. Probably a thousand better ways to do all of this tbqh.
			for i in range(count):
				if totalsize < count and size[i] > 0:
					size[i] = size[i] + 1
					totalsize = totalsize + 1
				elif totalsize == count:
					break	
					
		#print(size, totalsize)
		
		for i in range(count): # Fourth pass, put it all together.
			hue = i/(count*1.75)
			r, g, b = hsv_to_rgb(hue, 1, min((last_frame[i]*2.6+frame[i]*1.3)/3, 1))
			data = data+[int(g*255), int(r*255), int(b*255)]*int(size[i])
		
		now = time()
		if now-sent < .02:
			sleep(max(0, .02-(now-sent)))
		
		sent = time()
		send_to_stick(data)
		last_frame = frame

# IDEAS:
# Accelerate movement with amplitude?
# Draw bars sized according to loudness and colored according to frequency
# Draw just one bar sized according to loudness and ^
