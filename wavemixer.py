#!/usr/bin/python
# -*- coding: utf-8 -*-


import sys
import pyaudio
import wave
import wx
import os
import struct
import time
from math import floor
from sys import byteorder
from array import array
from struct import pack 
from datetime import datetime

THRESHOLD = 500
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
RATE = 44100

def is_silent(snd_data):
    "Returns 'True' if below the 'silent' threshold"
    return max(snd_data) < THRESHOLD

def normalize(snd_data):
    "Average the volume out"
    MAXIMUM = 16384
    times = float(MAXIMUM)/max(abs(i) for i in snd_data)

    r = array('h')
    for i in snd_data:
        r.append(int(i*times))
    return r

def trim(snd_data):
    "Trim the blank spots at the start and end"
    def _trim(snd_data):
        snd_started = False
        r = array('h')

        for i in snd_data:
            if not snd_started and abs(i)>THRESHOLD:
                snd_started = True
                r.append(i)

            elif snd_started:
                r.append(i)
        return r

    # Trim to the left
    snd_data = _trim(snd_data)

    # Trim to the right
    snd_data.reverse()
    snd_data = _trim(snd_data)
    snd_data.reverse()
    return snd_data

def add_silence(snd_data, seconds):
    "Add silence to the start and end of 'snd_data' of length 'seconds' (float)"
    r = array('h', [0 for i in xrange(int(seconds*RATE))])
    r.extend(snd_data)
    r.extend([0 for i in xrange(int(seconds*RATE))])
    return r

def record():
    """
    Record a word or words from the microphone and 
    return the data as an array of signed shorts.

    Normalizes the audio, trims silence from the 
    start and end, and pads with 0.5 seconds of 
    blank sound to make sure VLC et al can play 
    it without getting chopped off.
    """
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=1, rate=RATE,
        input=True, output=True,
        frames_per_buffer=CHUNK_SIZE)

    num_silent = 0
    snd_started = False

    r = array('h')

    while 1:
        # little endian, signed short
        snd_data = array('h', stream.read(CHUNK_SIZE))
        if byteorder == 'big':
            snd_data.byteswap()
        r.extend(snd_data)

        silent = is_silent(snd_data)
	print "Snd_started "
	print snd_started
	print "Silent "
	print silent
	
        if silent and snd_started:
            num_silent += 1
        elif not silent and not snd_started:
            snd_started = True
	print num_silent
        if snd_started and num_silent > 30:
            break

    sample_width = p.get_sample_size(FORMAT)
    stream.stop_stream()
    stream.close()
    p.terminate()

    r = normalize(r)
    r = trim(r)
    r = add_silence(r, 0.5)
    return sample_width, r

def record_to_file(path):
    "Records from the microphone and outputs the resulting data to 'path'"
    sample_width, data = record()
    data = pack('<' + ('h'*len(data)), *data)

    wf = wave.open(path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)
    wf.writeframes(data)
    wf.close()


class Example(wx.Frame):
	def __init__(self, *args, **kwargs):
		super(Example, self).__init__(*args, **kwargs) 
		self.InitUI()

	def InitUI(self):    
		#		toolbar = self.CreateToolBar()
		#qtool = toolbar.AddLabelTool(wx.ID_ANY, 'Quit')
		#toolbar.Realize()
		#self.Bind(wx.EVT_TOOL, self.OnQuit, qtool)
		
		print "Loading ..."
		# instantiate PyAudio (1)


		pnl = wx.Panel(self)
	        font = wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD)
	     	heading = wx.StaticText(pnl, label='Wave Mixer', pos=(512, 15))
	        heading.SetFont(font)
	        wx.StaticLine(pnl, pos=(10, 40), size=(1336,1))

		wx.StaticBox(pnl, label='Wave 1', pos=(40, 60), size=(300, 400))
		sfile1 = wx.Button(pnl, label='Select File', pos=(50, 90))
		sfile1.Bind(wx.EVT_BUTTON, self.Browse1)
		self.song1='S1.wav'
		self.fname1 = wx.StaticText(pnl, label='S1.wav', pos=(150, 100))
		wx.StaticText(pnl, label='Amplitude (%)', pos=(50, 130))
		slda1 = wx.Slider(pnl, value=100, minValue=0, maxValue=500, pos=(50, 150), size=(200, -1), style=wx.SL_HORIZONTAL)
		self.amp1 = wx.StaticText(pnl, label='100', pos=(260, 150))
	        slda1.Bind(wx.EVT_SCROLL, self.OnSliderScrollA1)
		wx.StaticText(pnl, label='Time Shift (s)', pos=(50, 180))
		sldt1 = wx.Slider(pnl, value=0, minValue=-100, maxValue=100, pos=(50, 200), size=(200, -1), style=wx.SL_HORIZONTAL)
		self.shift1 = wx.StaticText(pnl, label='0', pos=(260, 200))
	        sldt1.Bind(wx.EVT_SCROLL, self.OnSliderScrollT1)
		wx.StaticText(pnl, label='Time Scale (s)', pos=(50, 230))
		sldtt1 = wx.Slider(pnl, value=100, minValue=0, maxValue=1000, pos=(50, 250), size=(200, -1), style=wx.SL_HORIZONTAL)
		self.scale1 = wx.StaticText(pnl, label='1', pos=(260, 250))
	        sldtt1.Bind(wx.EVT_SCROLL, self.OnSliderScrollTT1)
		tr1 = wx.CheckBox(pnl, label='Time Reversal', pos=(50, 280))
		tr1.Bind(wx.EVT_CHECKBOX, self.TR1)
		self.treverse1=0
		mod1 = wx.CheckBox(pnl, label='Select for Modulation', pos=(50, 310))
		mod1.Bind(wx.EVT_CHECKBOX, self.MOD1)
		self.mod1=0
		mix1 = wx.CheckBox(pnl, label='Select for Mixing', pos=(50, 340))
		mix1.Bind(wx.EVT_CHECKBOX, self.MIX1)
		play1 = wx.Button(pnl, label='Play Audio', pos=(50, 390))
		play1.Bind(wx.EVT_BUTTON, self.Play1)

#		wx.CheckBox(pnl, label='Male', pos=(150, 300))
#		wx.CheckBox(pnl, label='Married', pos=(150, 250))
#		wx.StaticText(pnl, label='Age', pos=(150, 125))
#		wx.SpinCtrl(pnl, value='1', pos=(150, 160), size=(60, -1), min=1, max=120)

		wx.StaticBox(pnl, label='Wave 2', pos=(350, 60), size=(300, 400))
		sfile2 = wx.Button(pnl, label='Select File', pos=(360, 90))
		sfile2.Bind(wx.EVT_BUTTON, self.Browse2)
		self.song2='S2.wav'
		self.fname2 = wx.StaticText(pnl, label='S2.wav', pos=(460, 100))
		wx.StaticText(pnl, label='Amplitude (%)', pos=(360, 130))
		slda2 = wx.Slider(pnl, value=100, minValue=0, maxValue=500, pos=(360, 150), size=(200, -1), style=wx.SL_HORIZONTAL)
		self.amp2 = wx.StaticText(pnl, label='100', pos=(570, 150))
	        slda2.Bind(wx.EVT_SCROLL, self.OnSliderScrollA2)
		wx.StaticText(pnl, label='Time Shift (s)', pos=(360, 180))
		sldt2 = wx.Slider(pnl, value=0, minValue=-100, maxValue=100, pos=(360, 200), size=(200, -1), style=wx.SL_HORIZONTAL)
		self.shift2 = wx.StaticText(pnl, label='0', pos=(570, 200))
	        sldt2.Bind(wx.EVT_SCROLL, self.OnSliderScrollT2)
		wx.StaticText(pnl, label='Time Scale (s)', pos=(360, 230))
		sldtt2 = wx.Slider(pnl, value=100, minValue=0, maxValue=1000, pos=(360, 250), size=(200, -1), style=wx.SL_HORIZONTAL)
		self.scale2 = wx.StaticText(pnl, label='1', pos=(570, 250))
	        sldtt2.Bind(wx.EVT_SCROLL, self.OnSliderScrollTT2)
		tr2 =wx.CheckBox(pnl, label='Time Reversal', pos=(360, 280))
		tr2.Bind(wx.EVT_CHECKBOX, self.TR2)
		self.treverse2=0
		mod2 = wx.CheckBox(pnl, label='Select for Modulation', pos=(360, 310))
		self.mod2=0
		mod2.Bind(wx.EVT_CHECKBOX, self.MOD2)
		mix2 = wx.CheckBox(pnl, label='Select for Mixing', pos=(360, 340))
		mix2.Bind(wx.EVT_CHECKBOX, self.MIX2)
		play2 = wx.Button(pnl, label='Play Audio', pos=(360, 390))
		play2.Bind(wx.EVT_BUTTON, self.Play2)
		
		
		
		wx.StaticBox(pnl, label='Wave 3', pos=(660, 60), size=(300, 400))
		sfile3 = wx.Button(pnl, label='Select File', pos=(670, 90))
		sfile3.Bind(wx.EVT_BUTTON, self.Browse3)
		self.song3='S3.wav'
		self.fname3 = wx.StaticText(pnl, label='S3.wav', pos=(770, 100))
		wx.StaticText(pnl, label='Amplitude (%)', pos=(670, 130))
		slda3 = wx.Slider(pnl, value=100, minValue=0, maxValue=500, pos=(670, 150), size=(200, -1), style=wx.SL_HORIZONTAL)
		self.amp3 = wx.StaticText(pnl, label='100', pos=(880, 150))
	        slda3.Bind(wx.EVT_SCROLL, self.OnSliderScrollA3)
		wx.StaticText(pnl, label='Time Shift (s)', pos=(670, 180))
		sldt3 = wx.Slider(pnl, value=0, minValue=-100, maxValue=100, pos=(670, 200), size=(200, -1), style=wx.SL_HORIZONTAL)
		self.shift3 = wx.StaticText(pnl, label='0', pos=(880, 200))
	        sldt3.Bind(wx.EVT_SCROLL, self.OnSliderScrollT3)
		wx.StaticText(pnl, label='Time Scale (s)', pos=(670, 230))
		sldtt3 = wx.Slider(pnl, value=100, minValue=0, maxValue=1000, pos=(670, 250), size=(200, -1), style=wx.SL_HORIZONTAL)
		self.scale3 = wx.StaticText(pnl, label='1', pos=(880, 250))
	        sldtt3.Bind(wx.EVT_SCROLL, self.OnSliderScrollTT3)
		tr3 = wx.CheckBox(pnl, label='Time Reversal', pos=(670, 280))
		tr3.Bind(wx.EVT_CHECKBOX, self.TR3)
		self.treverse3=0
		mod3 =wx.CheckBox(pnl, label='Select for Modulation', pos=(670, 310))
		mod3.Bind(wx.EVT_CHECKBOX, self.MOD3)
		self.mod3=0
		mix3 = wx.CheckBox(pnl, label='Select for Mixing', pos=(670, 340))
		mix3.Bind(wx.EVT_CHECKBOX, self.MIX3)
		play3 = wx.Button(pnl, label='Play Audio', pos=(670, 390))
		play3.Bind(wx.EVT_BUTTON, self.Play3)


		self.tmix1=0
		self.tmix2=0
		self.tmix3=0
		self.tmod1=0
		self.tmod2=0
		self.tmod3=0

		rcbutton = wx.Button(pnl, label='Record', pos=(460, 500))
		rcbutton.Bind(wx.EVT_BUTTON, self.Record)
		playmodulation = wx.Button(pnl, label='Play Modulation', pos=(50, 500))
		playmodulation.Bind(wx.EVT_BUTTON, self.PlayModulation)
		playmixing = wx.Button(pnl, label='Play Mixing', pos=(870, 500))
		playmixing.Bind(wx.EVT_BUTTON, self.PlayMixing)
		self.SetSize((1024, 600))
		self.SetTitle('Wave Mixer')
		self.Centre()
		self.Show(True)
	def OnQuit(self, e):
		self.Close()

	def OnSliderScrollA1(self, e):
		obj = e.GetEventObject()
		val = obj.GetValue()
		self.amp1.SetLabel(str(val)) 
	
	def OnSliderScrollT1(self, e):
		obj = e.GetEventObject()
		val = obj.GetValue()
		self.shift1.SetLabel(str(val/100.0)) 
	
	def OnSliderScrollTT1(self, e):
		obj = e.GetEventObject()
		val = obj.GetValue()
		self.scale1.SetLabel(str(val/100.0)) 
	
	def OnSliderScrollA2(self, e):
		obj = e.GetEventObject()
		val = obj.GetValue()
		self.amp2.SetLabel(str(val)) 
	
	def OnSliderScrollT2(self, e):
		obj = e.GetEventObject()
		val = obj.GetValue()
		self.shift2.SetLabel(str(val/100.0)) 
	
	def OnSliderScrollTT2(self, e):
		obj = e.GetEventObject()
		val = obj.GetValue()
		self.scale2.SetLabel(str(val/100.0)) 
	
	def OnSliderScrollA3(self, e):
		obj = e.GetEventObject()
		val = obj.GetValue()
		self.amp3.SetLabel(str(val)) 
	
	def OnSliderScrollT3(self, e):
		obj = e.GetEventObject()
		val = obj.GetValue()
		self.shift3.SetLabel(str(val/100.0)) 
	
	def OnSliderScrollTT3(self, e):
		obj = e.GetEventObject()
		val = obj.GetValue()
		self.scale3.SetLabel(str(val/100.0)) 

	def Browse1(self,e):
		dlg = wx.FileDialog(self, message="Open a file", defaultDir=os.getcwd(),defaultFile="", style=wx.OPEN)
		if dlg.ShowModal() == wx.ID_OK:
			self.song1 = str(dlg.GetPath())
			self.fname1.SetLabel( os.path.basename( str(dlg.GetPath())))
			
		dlg.Destroy()


	def Browse2(self,e):
		dlg = wx.FileDialog(self, message="Open a file", defaultDir=os.getcwd(),defaultFile="", style=wx.OPEN)
		if dlg.ShowModal() == wx.ID_OK:
			self.song2 = str(dlg.GetPath())
			self.fname2.SetLabel( os.path.basename( str(dlg.GetPath())))
			
		dlg.Destroy()

	def Browse3(self,e):
		dlg = wx.FileDialog(self, message="Open a file", defaultDir=os.getcwd(),defaultFile="", style=wx.OPEN)
		if dlg.ShowModal() == wx.ID_OK:
			self.song3 = str(dlg.GetPath())
			self.fname3.SetLabel( os.path.basename( str(dlg.GetPath())))
			
		dlg.Destroy()

	def amplitude(self,stream) :
		num_channels = stream.getnchannels()
		sample_rate = stream.getframerate()
		sample_width = stream.getsampwidth()
		num_frames = stream.getnframes()
		raw_data = stream.readframes( num_frames ) # Returns byte data
#		stream.close()
	        total_samples = num_frames * num_channels


		if sample_width == 1:
			fmt = "%iB" % total_samples # read unsigned chars
		elif sample_width == 2:
		        fmt = "%ih" % total_samples # read signed 2 byte shorts
		else:
        	        raise ValueError("Only supports 8 and 16 bit audio formats.")

		integer_data = struct.unpack(fmt, raw_data)
		del raw_data # Keep memory tidy (who knows how big it might be)
		new_data = list(integer_data)
		channels = [ [] for time in range(num_channels) ]
		for index, value in enumerate(integer_data):
	        	bucket = index % num_channels
		        channels[bucket].append(value)
		
		
		if self.player==1:
			jj = float(self.amp1.GetLabel()) / 100
			mult = float(self.scale1.GetLabel())
		elif self.player==2:
			jj = float(self.amp2.GetLabel()) / 100
			mult = float(self.scale2.GetLabel())
		else :
			jj = float(self.amp3.GetLabel()) / 100
			mult = float(self.scale3.GetLabel())
		
		left = []
		right = []
		net = []
		for i in range(len(channels[0])):
			if( int(floor(mult * i)) >= len(channels[0]) ):
				break
			left.append(channels[0][int(floor(i*mult))])
			if num_channels==2:
				right.append(channels[1][int(floor(i*mult))])

		for i in range(len(left)):
			net.append(left[i])
			if num_channels==2:
				net.append(right[i])
		
		new_data = net
		total_samples = len(net)
		




		if( self.treverse1==1 or self.treverse2==1 or self.treverse3==1 ):
			new_data.reverse()
		
		for i in range(len(new_data)):
			if jj*new_data[i] >= 2**15:
				new_data[i] = 2**15 -1
		        elif jj*new_data[i] <= -2**15:
		                new_data[i] = -2**15
		        else :
			        new_data[i] = jj*new_data[i]
		
		if self.player==1:
			stl = int(abs(float(self.shift1.GetLabel())))
			if float(self.shift1.GetLabel()) < 0 :
				new_data = [0]*stl*sample_rate +new_data

			elif total_samples <= stl*sample_rate*1 :
        	        	raise ValueError("Audio File not long enough. Play aborted.")
				self.ShowMessageBadShift()
				return ''
			else:
				new_data = new_data[ stl*sample_rate*1 : ]
		elif self.player==2:
			stl = int(abs(float(self.shift2.GetLabel())))
			if float(self.shift2.GetLabel()) < 0 :
				new_data = [0]*stl*sample_rate +new_data
			elif total_samples <= stl*sample_rate*1 :
        	        	raise ValueError("Audio File not long enough. Play aborted.")
				self.ShowMessageBadShift()
				return ''
			else:
				new_data = new_data[ stl*sample_rate*1 : ]
		else :
			stl = int(abs(float(self.shift3.GetLabel())))
			if float(self.shift3.GetLabel()) < 0 :
				new_data = [0]*stl*sample_rate +new_data
			elif total_samples <= stl*sample_rate*1 :
        	        	raise ValueError("Audio File not long enough. Play aborted.")
				self.ShowMessageBadShift()
				return ''
			else:
				new_data = new_data[stl*sample_rate* 1 : ]

		total_samples = len(new_data)
		if sample_width == 1:
			fmt = "%iB" % total_samples # read unsigned chars
		elif sample_width == 2:
		        fmt = "%ih" % total_samples # read signed 2 byte shorts

		int_data = tuple(new_data)
		new = struct.pack(fmt, *(int_data))
		return new


	def ampli(self,stream) :
		num_channels = stream.getnchannels()
		sample_rate = stream.getframerate()
		sample_width = stream.getsampwidth()
		num_frames = stream.getnframes()
		raw_data = stream.readframes( num_frames ) # Returns byte data
#		stream.close()
	        total_samples = num_frames * num_channels


		if sample_width == 1:
			fmt = "%iB" % total_samples # read unsigned chars
		elif sample_width == 2:
		        fmt = "%ih" % total_samples # read signed 2 byte shorts
		else:
        	        raise ValueError("Only supports 8 and 16 bit audio formats.")

		integer_data = struct.unpack(fmt, raw_data)
		del raw_data # Keep memory tidy (who knows how big it might be)
		new_data = list(integer_data)
		channels = [ [] for time in range(num_channels) ]
		for index, value in enumerate(integer_data):
	        	bucket = index % num_channels
		        channels[bucket].append(value)
		
		
		if self.player==1:
			jj = float(self.amp1.GetLabel()) / 100
			mult = float(self.scale1.GetLabel())
		elif self.player==2:
			jj = float(self.amp2.GetLabel()) / 100
			mult = float(self.scale2.GetLabel())
		else :
			jj = float(self.amp3.GetLabel()) / 100
			mult = float(self.scale3.GetLabel())
		
		left = []
		right = []
		net = []
		for i in range(len(channels[0])):
			if( int(floor(mult * i)) >= len(channels[0]) ):
				break
			left.append(channels[0][int(floor(i*mult))])
			if num_channels==2:
				right.append(channels[1][int(floor(i*mult))])
		for i in range(len(left)):
			net.append(left[i])
			if num_channels==2:
				net.append(right[i])
		
		new_data = net
		total_samples = len(net)
		




		if( self.treverse1==1 or self.treverse2==1 or self.treverse3==1 ):
			new_data.reverse()
		
		for i in range(len(new_data)):
			if jj*new_data[i] >= 2**15:
				new_data[i] = 2**15 -1
		        elif jj*new_data[i] <= -2**15:
		                new_data[i] = -2**15
		        else :
			        new_data[i] = jj*new_data[i]
		
		if self.player==1:
			stl = int(abs(float(self.shift1.GetLabel())))
			if float(self.shift1.GetLabel()) < 0 :
				new_data = [0]*stl*sample_rate +new_data

			elif total_samples <= stl*sample_rate*1 :
        	        	raise ValueError("Audio File not long enough. Play aborted.")
				self.ShowMessageBadShift()
				return ''
			else:
				new_data = new_data[ stl*sample_rate*1 : ]
		elif self.player==2:
			stl = int(abs(float(self.shift2.GetLabel())))
			if float(self.shift2.GetLabel()) < 0 :
				new_data = [0]*stl*sample_rate +new_data
			elif total_samples <= stl*sample_rate*1 :
        	        	raise ValueError("Audio File not long enough. Play aborted.")
				self.ShowMessageBadShift()
				return ''
			else:
				new_data = new_data[ stl*sample_rate*1 : ]
		else :
			stl = int(abs(float(self.shift3.GetLabel())))
			if float(self.shift3.GetLabel()) < 0 :
				new_data = [0]*stl*sample_rate +new_data
			elif total_samples <= stl*sample_rate*1 :
        	        	raise ValueError("Audio File not long enough. Play aborted.")
				self.ShowMessageBadShift()
				return ''
			else:
				new_data = new_data[stl*sample_rate* 1 : ]
		
		total_samples = len(new_data)
		if sample_width == 1:
			fmt = "%iB" % total_samples # read unsigned chars
		elif sample_width == 2:
		        fmt = "%ih" % total_samples # read signed 2 byte shorts
		#int_data = tuple(new_data)
		#new = struct.pack(fmt, *(int_data))
		return new_data,fmt

	def MOD1(self,e):
		sender = e.GetEventObject()
		isChecked = sender.GetValue()     
		if isChecked:
			#			print "FIRST mod CHECKED"
			self.tmod1 = 1            
		else: 
			self.tmod1 = 0 
	def MOD2(self,e):
		sender = e.GetEventObject()
		isChecked = sender.GetValue()     
		if isChecked:
			#			print "FIRST mod CHECKED"
			self.tmod2 = 1            
		else: 
			self.tmod2 = 0 
	def MOD3(self,e):
		sender = e.GetEventObject()
		isChecked = sender.GetValue()     
		if isChecked:
			#			print "FIRST shift CHECKED"
			self.tmod3 = 1            
		else: 
			self.tmod3 = 0 
	def MIX1(self,e):
		sender = e.GetEventObject()
		isChecked = sender.GetValue()     
		if isChecked:
			#			print "FIRST shift CHECKED"
			self.tmix1 = 1            
		else: 
			self.tmix1 = 0 
	def MIX2(self,e):
		sender = e.GetEventObject()
		isChecked = sender.GetValue()     
		if isChecked:
			#			print "2nd shift CHECKED"
			self.tmix2 = 1            
		else: 
			self.tmix2 = 0 
	def MIX3(self,e):
		sender = e.GetEventObject()
		isChecked = sender.GetValue()     
		if isChecked:
			#			print "3rd shift CHECKED"
			self.tmix3 = 1            
		else: 
			self.tmix3 = 0 

	def TR1(self,e):
		sender = e.GetEventObject()
		isChecked = sender.GetValue()     
		if isChecked:
			#			print "FIRST CHECKED"
			self.treverse1 = 1            
		else: 
			self.treverse1 = 0 
	
	def TR2(self,e):
		sender = e.GetEventObject()
		isChecked = sender.GetValue()     
		if isChecked:
			#			print "2nd CHECKED"
			self.treverse2 = 1            
		else: 
			self.treverse2 = 0 
	
	def TR3(self,e):
		sender = e.GetEventObject()
		isChecked = sender.GetValue()     
		if isChecked:
			#			print "3rd CHECKED"
			self.treverse3 = 1            
		else: 
			self.treverse3 = 0 

	def PlayMixing(self,e):
		data1=[]
		data2=[]
		data3=[]
		fmt1=0
		fmt2=0
		fmt3=0
		len1=0
		len2=0
		len3=0
		small=0
		sample_rate1=0
		sample_rate2=0
		sample_rate3=0
		samp_wid=0
		if self.tmix1==1 :
			wf1 = wave.open(self.song1, 'rb')
			sample_rate1 = wf1.getframerate()
			sample_rate2 = wf1.getframerate()
			sample_rate3 = wf1.getframerate()
			num_channels = wf1.getnchannels()
			sample_rate = wf1.getframerate()
			sample_width = wf1.getsampwidth()
			num_frames = wf1.getnframes()

			samp_wid = wf1.getsampwidth()
			fl1 = 1
			self.player=1
			data1 , fmt1 = self.ampli(wf1)
			len1 = len(data1)
			small=len1
		if self.tmix2==1 :
			wf2 = wave.open(self.song2, 'rb')
			sample_rate1 = wf2.getframerate()
			sample_rate2 = wf2.getframerate()
			sample_rate3 = wf2.getframerate()
			num_channels = wf2.getnchannels()
			sample_rate = wf2.getframerate()
			sample_width = wf2.getsampwidth()
			num_frames = wf2.getnframes()
			samp_wid = wf2.getsampwidth()
			fl2 = 1
			self.player=2
			data2 , fmt2 = self.ampli(wf2)
			len2=len(data2)
			small=len2
		if self.tmix3==1 :
			wf3 = wave.open(self.song3, 'rb')
			sample_rate1 = wf3.getframerate()
			sample_rate2 = wf3.getframerate()
			sample_rate3 = wf3.getframerate()
			samp_wid = wf3.getsampwidth()
			num_channels = wf3.getnchannels()
			sample_rate = wf3.getframerate()
			sample_width = wf3.getsampwidth()
			num_frames = wf3.getnframes()
			fl3 = 1
			self.player=3
			data3 , fmt3 = self.ampli(wf3)
			len3=len(data3)
			small=len3
		if self.tmix1==0 and self.tmix2==0 and self.tmix3==0:
			return

		if self.tmix1==1:
			small=max(small,len1)
			sample_rate1 = wf1.getframerate()

		if self.tmix2==1:
			small=max(small,len2)
			sample_rate2 = wf2.getframerate()
		if self.tmix3==1:
			small=max(small,len3)
			sample_rate3 = wf3.getframerate()

		if( sample_rate1!=sample_rate2 or sample_rate2!=sample_rate3 or sample_rate1!=sample_rate3):
			print "Selected files cannot be mixed, have different frame rates"
			self.ShowMessageBadMix()
			return
		net=[]
		if small == len1 :
			for i in range(small):
				net.append(data1[i])
			if self.tmix2==1:
				for i in range(len2):
					net[i] = net[i] + data2[i]
					if net[i] >= 2**15 :
						net[i] = 2**15-1
					if net[i] < -2**15:
						net[i] = -2**15
			if self.tmix3==1:
				for i in range(len3):
					net[i] = net[i] + data3[i]
					if net[i] >= 2**15 :
						net[i] = 2**15-1
					if net[i] < -2**15:
						net[i] = -2**15

		elif small == len2 :
			for i in range(small):
				net.append(data2[i])
			if self.tmix1==1:
				for i in range(len1):
					net[i] = net[i] + data1[i]
					if net[i] >= 2**15 :
						net[i] = 2**15-1
					if net[i] < -2**15:
						net[i] = -2**15
			if self.tmix3==1:
				for i in range(len3):
					net[i] = net[i] + data3[i]
					if net[i] >= 2**15 :
						net[i] = 2**15-1
					if net[i] < -2**15:
						net[i] = -2**15

		elif small == len3 :
			for i in range(small):
				net.append(data3[i])
			if self.tmix2==1:
				for i in range(len2):
					net[i] = net[i] + data2[i]
					if net[i] >= 2**15 :
						net[i] = 2**15-1
					if net[i] < -2**15:
						net[i] = -2**15
			if self.tmix1==1:
				for i in range(len1):
					net[i] = net[i] + data1[i]
					if net[i] >= 2**15 :
						net[i] = 2**15-1
					if net[i] < -2**15:
						net[i] = -2**15
        	fmt = "%ih" % (len(net))
	        new_data = tuple(net)
		raw_data = struct.pack(fmt , *new_data)
#		nstream = wave.open('result_mix',"wb")
		print "Mixing ..."
		'''
		nstream.setnchannels(num_channels)
		nstream.setsampwidth(sample_width)
		nstream.setframerate(sample_rate)
		nstream.setnframes(len(net)/2)
		nstream.writeframes(raw_data)
		nstream.close()
		'''
		global p
		p = pyaudio.PyAudio()

		print "Num : %d"%num_channels
		# open stream (2)
		stream = p.open(format=p.get_format_from_width(sample_width),  channels=num_channels,rate=sample_rate, output=True)
		data = raw_data

		# play stream (3)
		while data != '':
			stream.write(data)
			data=''
	#		data = wf.readframes(1024)

		# stop stream (4)
		stream.stop_stream()
		stream.close()

		# close PyAudio (5)
		p.terminate()
		

	def PlayModulation(self,e):
		data1=[]
		data2=[]
		data3=[]
		fmt1=0
		fmt2=0
		fmt3=0
		len1=0
		len2=0
		len3=0
		small=0
		sample_rate1=0
		sample_rate2=0
		sample_rate3=0
		samp_wid=0
		if self.tmod1==1 :
			wf1 = wave.open(self.song1, 'rb')
			sample_rate1 = wf1.getframerate()
			sample_rate2 = wf1.getframerate()
			sample_rate3 = wf1.getframerate()
			num_channels = wf1.getnchannels()
			sample_rate = wf1.getframerate()
			sample_width = wf1.getsampwidth()
			num_frames = wf1.getnframes()

			samp_wid = wf1.getsampwidth()
			fl1 = 1
			self.player=1
			data1 , fmt1 = self.ampli(wf1)
			len1 = len(data1)
			small=len1
		if self.tmod2==1 :
			wf2 = wave.open(self.song2, 'rb')
			sample_rate1 = wf2.getframerate()
			sample_rate2 = wf2.getframerate()
			sample_rate3 = wf2.getframerate()
			num_channels = wf2.getnchannels()
			sample_rate = wf2.getframerate()
			sample_width = wf2.getsampwidth()
			num_frames = wf2.getnframes()
			samp_wid = wf2.getsampwidth()
			fl2 = 1
			self.player=2
			data2 , fmt2 = self.ampli(wf2)
			len2=len(data2)
			small=len2
		if self.tmod3==1 :
			wf3 = wave.open(self.song3, 'rb')
			sample_rate1 = wf3.getframerate()
			sample_rate2 = wf3.getframerate()
			sample_rate3 = wf3.getframerate()
			samp_wid = wf3.getsampwidth()
			num_channels = wf3.getnchannels()
			sample_rate = wf3.getframerate()
			sample_width = wf3.getsampwidth()
			num_frames = wf3.getnframes()
			fl3 = 1
			self.player=3
			data3 , fmt3 = self.ampli(wf3)
			len3=len(data3)
			small=len3
		if self.tmod1==0 and self.tmod2==0 and self.tmod3==0:
			return

		if self.tmod1==1:
			small=max(small,len1)
			sample_rate1 = wf1.getframerate()

		if self.tmod2==1:
			small=max(small,len2)
			sample_rate2 = wf2.getframerate()
		if self.tmod3==1:
			small=max(small,len3)
			sample_rate3 = wf3.getframerate()

		if( sample_rate1!=sample_rate2 or sample_rate2!=sample_rate3 or sample_rate1!=sample_rate3):
			print "Selected files cannot be modulated, have different frame rates"
			self.ShowMessageBadMix()
			return
		net=[]
		if small == len1 :
			for i in range(small):
				net.append(data1[i])
			if self.tmod2==1:
				for i in range(len2):
					net[i] = net[i] * data2[i]
					if net[i] >= 2**15 :
						net[i] = 2**15-1
					if net[i] < -2**15:
						net[i] = -2**15
			if self.tmod3==1:
				for i in range(len3):
					net[i] = net[i] * data3[i]
					if net[i] >= 2**15 :
						net[i] = 2**15-1
					if net[i] < -2**15:
						net[i] = -2**15

		elif small == len2 :
			for i in range(small):
				net.append(data2[i])
			if self.tmod1==1:
				for i in range(len1):
					net[i] = net[i] * data1[i]
					if net[i] >= 2**15 :
						net[i] = 2**15-1
					if net[i] < -2**15:
						net[i] = -2**15
			if self.tmod3==1:
				for i in range(len3):
					net[i] = net[i] * data3[i]
					if net[i] >= 2**15 :
						net[i] = 2**15-1
					if net[i] < -2**15:
						net[i] = -2**15

		elif small == len3 :
			for i in range(small):
				net.append(data3[i])
			if self.tmod2==1:
				for i in range(len2):
					net[i] = net[i] * data2[i]
					if net[i] >= 2**15 :
						net[i] = 2**15-1
					if net[i] < -2**15:
						net[i] = -2**15
			if self.tmod1==1:
				for i in range(len1):
					net[i] = net[i] * data1[i]
					if net[i] >= 2**15 :
						net[i] = 2**15-1
					if net[i] < -2**15:
						net[i] = -2**15
        	fmt = "%ih" % (len(net))
	        new_data = tuple(net)
		raw_data = struct.pack(fmt , *new_data)
#		nstream = wave.open('result_mix',"wb")
		print "Modulating ..."
		'''
		nstream.setnchannels(num_channels)
		nstream.setsampwidth(sample_width)
		nstream.setframerate(sample_rate)
		nstream.setnframes(len(net)/2)
		nstream.writeframes(raw_data)
		nstream.close()
		'''
		global p
		p = pyaudio.PyAudio()

		# open stream (2)
		stream = p.open(format=p.get_format_from_width(sample_width),  channels=num_channels,rate=sample_rate, output=True)
		data = raw_data

		# play stream (3)
		while data != '':
			stream.write(data)
			data=''
	#		data = wf.readframes(1024)

		# stop stream (4)
		stream.stop_stream()
		stream.close()

		# close PyAudio (5)
		p.terminate()
		

	def Play1(self,e):
		wf = wave.open(self.song1, 'rb')
		global p

		# instantiate PyAudio (1)
		p = pyaudio.PyAudio()

		# open stream (2)
		stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),  channels=wf.getnchannels(),rate=wf.getframerate(), output=True)

		self.player = 1
		data = self.amplitude(wf)
		# read data
		#data = wf.readframes(1024)

		# play stream (3)
		while data != '':
			stream.write(data)
			data = wf.readframes(1024)

		# stop stream (4)
		stream.stop_stream()
		stream.close()

		# close PyAudio (5)
		p.terminate()

	def Play2(self,e):
		wf = wave.open(self.song2, 'rb')
		global p

		# instantiate PyAudio (1)
		p = pyaudio.PyAudio()

		# open stream (2)
		stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),  channels=wf.getnchannels(),rate=wf.getframerate(), output=True)

		self.player = 2
		data = self.amplitude(wf)
		# read data
		#data = wf.readframes(1024)

		# play stream (3)
		while data != '':
			stream.write(data)
			data = wf.readframes(1024)

		# stop stream (4)
		stream.stop_stream()
		stream.close()

		# close PyAudio (5)
		p.terminate()

	def Play3(self,e):
		wf = wave.open(self.song3, 'rb')

		global p
		# instantiate PyAudio (1)
		p = pyaudio.PyAudio()

		# open stream (2)
		stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),  channels=wf.getnchannels(),rate=wf.getframerate(), output=True)

		self.player = 3
		data = self.amplitude(wf)

		# play stream (3)
		while data != '':
			stream.write(data)
			data = wf.readframes(1024)

		# stop stream (4)
		stream.stop_stream()
		stream.close()

		# close PyAudio (5)
		p.terminate()

	def Record(self,e):
		print "Recording started... "
		record_to_file('Recording_%s.wav'%(datetime.now()))
		print "Recording finished! "
		self.ShowMessageRF()

	def ShowMessageNF(self):
		wx.MessageBox('No File Selected', 'Info',wx.OK | wx.ICON_INFORMATION)
	
	def ShowMessageBadMix(self):
		wx.MessageBox('Selected files cannot be mixed/modulated, have different frame rates', 'Info',wx.OK | wx.ICON_INFORMATION)

	def ShowMessageBadShift(self):
		wx.MessageBox('Audio File not long enough. Play aborted.', 'Info',wx.OK | wx.ICON_INFORMATION)
	def ShowMessageRF(self):
		wx.MessageBox('Recording Finished!', 'Info',wx.OK | wx.ICON_INFORMATION)

def main():
	ex = wx.App()
	Example(None)
	ex.MainLoop()    
		
if __name__ == '__main__':
	main()
