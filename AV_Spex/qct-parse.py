#!/usr/bin/env python
# -*- coding: utf-8 -*-

# The majority of this code is derived from the open source project qct-parse
# which is licensed under the GNU Version 3 License. You may obtain a copy of the license at: https://github.com/FutureDays/qct-parse/blob/master/LICENSE
# Original code is here: https://github.com/FutureDays/qct-parse  

# The original code from the qct-parse was written by Brendan Coates and Morgan Morel as part of the 2016 AMIA "Hack Day"
# Summary of that event here: https://wiki.curatecamp.org/index.php/Association_of_Moving_Image_Archivists_%26_Digital_Library_Federation_Hack_Day_2016

from lxml import etree  
import argparse         
import configparser		
import gzip            
import logging         
import collections   
import os      			
import subprocess	
import gc			
import math				
import sys			
import re
import yaml
from utils.log_setup import logger
from utils.find_config import config_path				


# Creates timestamp for pkt_dts_time
def dts2ts(frame_pkt_dts_time):
    seconds = float(frame_pkt_dts_time)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if hours < 10:
        hours = "0" + str(int(hours))
    else:
        hours = str(int(hours))  
    if minutes < 10:
        minutes = "0" + str(int(minutes))
    else:
        minutes = str(int(minutes))
    secondsStr = str(round(seconds,4))
    if int(seconds) < 10:
        secondsStr = "0" + secondsStr
    else:
        seconds = str(minutes)
    while len(secondsStr) < 7:
        secondsStr = secondsStr + "0"
    timeStampString = hours + ":" + minutes + ":" + secondsStr
    return timeStampString
	
# finds stuff over/under threshold
def threshFinder(video_path,inFrame,startObj,pkt,tag,over,thumbPath,thumbDelay):
	tagValue = float(inFrame[tag])
	frame_pkt_dts_time = inFrame[pkt]
	if "MIN" in tag or "LOW" in tag:
		under = over
		if tagValue < float(under): # if the attribute is under usr set threshold
			timeStampString = dts2ts(frame_pkt_dts_time)
			#logging.warning(tag + " is under " + str(under) + " with a value of " + str(tagValue) + " at duration " + timeStampString)
			if config_path.config_dict['qct-parse']['checks']['thumbExport'] and (thumbDelay > int(config_path.config_dict['qct-parse']['checks']['thumbExportDelay'])): # if thumb export is turned on and there has been enough delay between this frame and the last exported thumb, then export a new thumb
				printThumb(video_path,tag,startObj,thumbPath,tagValue,timeStampString)
				thumbDelay = 0
			return True, thumbDelay # return true because it was over and thumbDelay
		else:
			return False, thumbDelay # return false because it was NOT over and thumbDelay
	else:
		if tagValue > float(over): # if the attribute is over usr set threshold
			timeStampString = dts2ts(frame_pkt_dts_time)
			#logging.warning(tag + " is over " + str(over) + " with a value of " + str(tagValue) + " at duration " + timeStampString)
			if config_path.config_dict['qct-parse']['checks']['thumbExport'] and (thumbDelay > int(config_path.config_dict['qct-parse']['checks']['thumbExportDelay'])): # if thumb export is turned on and there has been enough delay between this frame and the last exported thumb, then export a new thumb
				printThumb(video_path,tag,startObj,thumbPath,tagValue,timeStampString)
				thumbDelay = 0
			return True, thumbDelay # return true because it was over and thumbDelay
		else:
			return False, thumbDelay # return false because it was NOT over and thumbDelay

#  print thumbnail images of overs/unders	
#  Need to update - file naming convention has changed
def printThumb(video_path,tag,startObj,thumbPath,tagValue,timeStampString):
	inputVid = video_path
	if os.path.isfile(inputVid):
		baseName = os.path.basename(startObj)
		baseName = baseName.replace(".qctools.xml.gz", "")
		outputFramePath = os.path.join(thumbPath,baseName + "." + tag + "." + str(tagValue) + "." + timeStampString + ".png")
		ffoutputFramePath = outputFramePath.replace(":",".")
		# for windows we gotta see if that first : for the drive has been replaced by a dot and put it back
		match = ''
		match = re.search(r"[A-Z]\.\/",ffoutputFramePath) # matches pattern R./ which should be R:/ on windows
		if match:
			ffoutputFramePath = ffoutputFramePath.replace(".",":",1) # replace first instance of "." in string ffoutputFramePath
		ffmpegString = "ffmpeg -ss " + timeStampString + ' -i "' + inputVid +  '" -vframes 1 -s 720x486 -y "' + ffoutputFramePath + '"' # Hardcoded output frame size to 720x486 for now, need to infer from input eventually
		output = subprocess.Popen(ffmpegString,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
		out,err = output.communicate()
		if config_path.config_dict['qct-parse']['checks']['quiet'] is False:
			print(out)
			print(err)
	else:
		print("Input video file not found. Ensure video file is in the same directory as the QCTools report and report file name contains video file extension.")
		exit()
	return	
	
# detect bars	
def detectBars(startObj,pkt,durationStart,durationEnd,framesList,buffSize):
	frame_count = 0
	with gzip.open(startObj) as xml:
		for event, elem in etree.iterparse(xml, events=('end',), tag='frame'): # iterparse the xml doc
			if elem.attrib['media_type'] == "video": # get just the video frames
				frame_pkt_dts_time = elem.attrib[pkt] # get the timestamps for the current frame we're looking at
				frameDict = {}  # start an empty dict for the new frame
				frameDict[pkt] = frame_pkt_dts_time  # give the dict the timestamp, which we have now
				for t in list(elem):    # iterating through each attribute for each element
					keySplit = t.attrib['key'].split(".")   # split the names by dots 
					keyName = str(keySplit[-1])             # get just the last word for the key name
					frameDict[keyName] = t.attrib['value']	# add each attribute to the frame dictionary
				framesList.append(frameDict)
				frame_count += 1
				if frame_count % 25 == 0:  #  Check every 25 frames
					if float(frameDict['YMAX']) > 800 and float(frameDict['YMIN']) < 10 and float(frameDict['YDIF']) < 7 :
						if durationStart == "":
							durationStart = float(frameDict[pkt])
							print("Bars start at " + str(frameDict[pkt]) + " (" + dts2ts(frameDict[pkt]) + ")")	
							# using JPC_AV_01663 as a test case:
							# bars start at 0.868 (26 frames) and end at 45.87 sec (1375 frames)	
							# XML has YMAX going over 220 at frame 37, and above 800 on frame 45, starts dipping below 900 on frame 967 and stays below 900 starting on frame 1003, below 800 for the first time on frame 1425 					
						durationEnd = float(frameDict[pkt])
					else:
						if durationStart != "" and durationEnd != "" and durationEnd - durationStart > 2: 
							print("Bars ended at " + str(frameDict[pkt]) + " (" + dts2ts(frameDict[pkt]) + ")")							
							break
			elem.clear() # we're done with that element so let's get it outta memory
	return durationStart, durationEnd

def analyzeIt(video_path,profile,startObj,pkt,durationStart,durationEnd,thumbPath,thumbDelay,framesList,frameCount=0,overallFrameFail=0):
	kbeyond = {} # init a dict for each key which we'll use to track how often a given key is over
	fots = ""
	if config_path.config_dict['qct-parse']['checks']['tagname']:
		kbeyond[config_path.config_dict['qct-parse']['checks']['tagname']] = 0 
	else:
		for k,v in profile.items(): 
			kbeyond[k] = 0
	with gzip.open(startObj) as xml:	
		for event, elem in etree.iterparse(xml, events=('end',), tag='frame'): # iterparse the xml doc
			if elem.attrib['media_type'] == "video": 	# get just the video frames
				frameCount = frameCount + 1
				frame_pkt_dts_time = elem.attrib[pkt] 	# get the timestamps for the current frame we're looking at
				if frame_pkt_dts_time >= str(durationStart): 	# only work on frames that are after the start time
					if durationEnd:
						if float(frame_pkt_dts_time) > durationEnd:		# only work on frames that are before the end time
							print("started at " + str(durationStart) + " seconds and stopped at " + str(frame_pkt_dts_time) + " seconds (" + dts2ts(frame_pkt_dts_time) + ") or " + str(frameCount) + " frames!")
							break
					frameDict = {}  								# start an empty dict for the new frame
					frameDict[pkt] = frame_pkt_dts_time  			# make a key for the timestamp, which we have now
					for t in list(elem):    						# iterating through each attribute for each element
						keySplit = t.attrib['key'].split(".")   	# split the names by dots 
						keyName = str(keySplit[-1])             	# get just the last word for the key name
						if len(keyName) == 1:						# if it's psnr or mse, keyName is gonna be a single char
							keyName = '.'.join(keySplit[-2:])		# full attribute made by combining last 2 parts of split with a period in btw
						frameDict[keyName] = t.attrib['value']		# add each attribute to the frame dictionary
					framesList.append(frameDict)					# add this dict to our circular buffer
					if config_path.config_dict['qct-parse']['checks']['profile'] is True:								# display "timestamp: Tag Value" (654.754100: YMAX 229) to the terminal window
						print(framesList[-1][pkt] + ": " + config_path.config_dict['qct-parse']['checks']['tagname'] + " " + framesList[-1][config_path.config_dict['qct-parse']['checks']['tagname']])
					# Now we can parse the frame data from the buffer!	
					if config_path.config_dict['qct-parse']['checks']['over'] or config_path.config_dict['qct-parse']['checks']['under'] and config_path.config_dict['qct-parse']['checks']['profile'] is None: # if we're just doing a single tag
						tag = config_path.config_dict['qct-parse']['checks']['tagname']
						if config_path.config_dict['qct-parse']['checks']['over']:
							over = float(config_path.config_dict['qct-parse']['checks']['over'])
						if config_path.config_dict['qct-parse']['checks']['under']:
							over = float(config_path.config_dict['qct-parse']['checks']['under'])
						# ACTAULLY DO THE THING ONCE FOR EACH TAG
						frameOver, thumbDelay = threshFinder(video_path,framesList[-1],startObj,pkt,tag,over,thumbPath,thumbDelay)
						if frameOver is True:
							kbeyond[tag] = kbeyond[tag] + 1 # note the over in the keyover dictionary
					elif config_path.config_dict['qct-parse']['checks']['profile'] is not None: # if we're using a profile
						for k,v in profile.items():
							tag = k
							over = float(v)
							# ACTUALLY DO THE THING ONCE FOR EACH TAG
							frameOver, thumbDelay = threshFinder(video_path,framesList[-1],startObj,pkt,tag,over,thumbPath,thumbDelay)
							if frameOver is True:
								kbeyond[k] = kbeyond[k] + 1 # note the over in the key over dict
								if not frame_pkt_dts_time in fots: # make sure that we only count each over frame once
									overallFrameFail = overallFrameFail + 1
									fots = frame_pkt_dts_time # set it again so we don't dupe
					thumbDelay = thumbDelay + 1				
			elem.clear() # we're done with that element so let's get it outta memory
	return kbeyond, frameCount, overallFrameFail


# This function is admittedly very ugly, but what it puts out is very pretty. Need to revamp 	
def printresults(kbeyond,frameCount,overallFrameFail):
	if frameCount == 0:
		percentOverString = "0"
	else:
		print("")
		print("TotalFrames:\t" + str(frameCount))
		print("")
		print("By Tag:")
		print("")
		percentOverall = float(overallFrameFail) / float(frameCount)
		if percentOverall == 1:
			percentOverallString = "100"
		elif percentOverall == 0:
			percentOverallString = "0"
		elif percentOverall < 0.0001:
			percentOverallString = "<0.01"
		else:
			percentOverallString = str(percentOverall)
			percentOverallString = percentOverallString[2:4] + "." + percentOverallString[4:]
			if percentOverallString[0] == "0":
				percentOverallString = percentOverallString[1:]
				percentOverallString = percentOverallString[:4]
			else:
				percentOverallString = percentOverallString[:5]			
		for k,v in kbeyond.items():
			percentOver = float(kbeyond[k]) / float(frameCount)
			if percentOver == 1:
				percentOverString = "100"
			elif percentOver == 0:
				percentOverString = "0"
			elif percentOver < 0.0001:
				percentOverString = "<0.01"
			else:
				percentOverString = str(percentOver)
				percentOverString = percentOverString[2:4] + "." + percentOverString[4:]
				if percentOverString[0] == "0":
					percentOverString = percentOverString[1:]
					percentOverString = percentOverString[:4]
				else:
					percentOverString = percentOverString[:5]
			print(k + ":\t" + str(kbeyond[k]) + "\t" + percentOverString + "\t% of the total # of frames")
			print("")
		print("Overall:")
		print("")
		print("Frames With At Least One Fail:\t" + str(overallFrameFail) + "\t" + percentOverallString + "\t% of the total # of frames")
		print("")
		print("**************************")
		print("")
	return
	
def run_qctparse(video_path, file_path):
	###### Initialize values from the Config Parser
	profile = {} # init a dictionary where we'll store reference values from our config file
	# init a list of every tag available in a QCTools Report
	tagList = ["YMIN","YLOW","YAVG","YHIGH","YMAX","UMIN","ULOW","UAVG","UHIGH","UMAX","VMIN","VLOW","VAVG","VHIGH","VMAX","SATMIN","SATLOW","SATAVG","SATHIGH","SATMAX","HUEMED","HUEAVG","YDIF","UDIF","VDIF","TOUT","VREP","BRNG","mse_y","mse_u","mse_v","mse_avg","psnr_y","psnr_u","psnr_v","psnr_avg"]
	if config_path.config_dict['qct-parse']['checks']['profile'] is not None:
		template = config_path.config_dict['qct-parse']['checks']['profile'] # get the profile/ section name from CLI
		if template in config_path.config_dict['qct-parse']['profiles']:
		# If the template matches one of the profiles
			for t in tagList:
				formatted_tag = t.replace("_", ".")  # replace _ necessary for config file with . which xml attributes use, assign the value in config
				try:
					# Attempt to assign the value from the YAML profile to the profile dict
					profile[formatted_tag] = config_path.config_dict['qct-parse']['profiles'][template].get(t)
				except Exception as e:
					# If no config tag exists or any other error, do nothing
					pass
	
	###### Initialize some other stuff ######
	startObj = file_path
	buffSize = int(config_path.config_dict['qct-parse']['checks']['buffSize'])   # cast the input buffer as an integer
	if buffSize%2 == 0:
		buffSize = buffSize + 1
	logger.info("Starting qct-parse")	# initialize the log
	overcount = 0	# init count of overs
	undercount = 0	# init count of unders
	count = 0		# init total frames counter
	framesList = collections.deque(maxlen=buffSize)		# init holding object for holding all frame data in a circular buffer. 
	bdFramesList = collections.deque(maxlen=buffSize) 	# init holding object for holding all frame data in a circular buffer. 
	thumbDelay = int(config_path.config_dict['qct-parse']['checks']['thumbExportDelay'])	# get a seconds number for the delay in the original file btw exporting tags
	parentDir = os.path.dirname(startObj)
	baseName = os.path.basename(startObj)
	baseName = baseName.replace(".qctools.xml.gz", "")
	durationStart = config_path.config_dict['qct-parse']['checks']['durationStart']
	durationEnd = config_path.config_dict['qct-parse']['checks']['durationEnd']

	# we gotta find out if the qctools report has pkt_dts_time or pkt_pts_time ugh
	with gzip.open(startObj) as xml:    
		for event, elem in etree.iterparse(xml, events=('end',), tag='frame'):  # iterparse the xml doc
			if elem.attrib['media_type'] == "video":  # get just the video frames
				# we gotta find out if the qctools report has pkt_dts_time or pkt_pts_time ugh
				match = re.search(r"pkt_.ts_time", etree.tostring(elem).decode('utf-8'))
				if match:
					pkt = match.group()
					break

	# set the start and end duration times
	if config_path.config_dict['qct-parse']['checks']['barsDetection']:
		durationStart = ""				# if bar detection is turned on then we have to calculate this
		durationEnd = ""				# if bar detection is turned on then we have to calculate this
	elif config_path.config_dict['qct-parse']['checks']['durationStart']:
		durationStart = float(config_path.config_dict['qct-parse']['checks']['durationStart']) 	# The duration at which we start analyzing the file if no bar detection is selected
	elif not config_path.config_dict['qct-parse']['checks']['durationEnd'] == 99999999:
		durationEnd = float(config_path.config_dict['qct-parse']['checks']['durationEnd']) 	# The duration at which we stop analyzing the file if no bar detection is selected
	
	
	# set the path for the thumbnail export	
	if config_path.config_dict['qct-parse']['checks']['thumbExportPath'] and not config_path.config_dict['qct-parse']['checks']['thumbExport']:
		logger.critical("You specified a thumbnail export path without setting thumbExport to 'true'. Please either set thumbExport to true or set thumbExportPath to '' ")
	
	if config_path.config_dict['qct-parse']['checks']['thumbExportPath'] : # if user supplied thumbExportPath, use that
	    thumbPath = str(config_path.config_dict['qct-parse']['checks']['thumbExportPath'])
	else :
		if config_path.config_dict['qct-parse']['checks']['tagname']: # if they supplied a single tag
			if config_path.config_dict['qct-parse']['checks']['over']: # if the supplied tag is looking for a threshold Over
				thumbPath = os.path.join(parentDir, str(config_path.config_dict['qct-parse']['checks']['tagname']) + "." + str(config_path.config_dict['qct-parse']['checks']['over']))
			elif config_path.config_dict['qct-parse']['checks']['under']: # if the supplied tag was looking for a threshold Under
				thumbPath = os.path.join(parentDir, str(config_path.config_dict['qct-parse']['checks']['tagname']) + "." + str(config_path.config_dict['qct-parse']['checks']['under']))
		else: # if they're using a profile, put all thumbs in 1 dir
			thumbPath = os.path.join(parentDir, "ThumbExports")
	
	if config_path.config_dict['qct-parse']['checks']['thumbExportPath']: # make the thumb export path if it doesn't already exist
		if not os.path.exists(thumbPath):
			os.makedirs(thumbPath)
	
	
	######## Iterate Through the XML for Bars detection ########
	if config_path.config_dict['qct-parse']['checks']['barsDetection']:
		print("")
		print("Starting Bars Detection on " + baseName)
		print("")
		durationStart,durationEnd = detectBars(startObj,pkt,durationStart,durationEnd,framesList,buffSize,)
	

	######## Iterate Through the XML for General Analysis ########
	print("")
	print("Starting Analysis on " + baseName)
	print("")
	kbeyond, frameCount, overallFrameFail = analyzeIt(video_path,profile,startObj,pkt,durationStart,durationEnd,thumbPath,thumbDelay,framesList)
	
	
	print("Finished Processing File: " + baseName + ".qctools.xml.gz")
	print("")
	
	
	# do some maths for the printout
	if config_path.config_dict['qct-parse']['checks']['over'] or config_path.config_dict['qct-parse']['checks']['under'] or config_path.config_dict['qct-parse']['checks']['profile'] is not None:
		printresults(kbeyond,frameCount,overallFrameFail)
	
	return

if __name__ == "__main__":
	#if len(sys.argv) != 2:
	#	print("Usage: python qct-parse.py <input_video> <qctools_report>")
	#	sys.exit(1)
	video_path = sys.argv[1]
	report_path = sys.argv[2]
	if not os.path.isfile(report_path):
		print(f"Error: {report_path} is not a valid file.")
		sys.exit(1)
	run_qctparse(video_path, report_path)