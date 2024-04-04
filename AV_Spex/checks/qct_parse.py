#!/usr/bin/env python
# -*- coding: utf-8 -*-

# The majority of this code is derived from the open source project qct-parse
# which is licensed under the GNU Version 3 License. You may obtain a copy of the license at: https://github.com/FutureDays/qct-parse/blob/master/LICENSE
# Original code is here: https://github.com/FutureDays/qct-parse  

# The original code from the qct-parse was written by Brendan Coates and Morgan Morel as part of the 2016 AMIA "Hack Day"
# Summary of that event here: https://wiki.curatecamp.org/index.php/Association_of_Moving_Image_Archivists_%26_Digital_Library_Federation_Hack_Day_2016

from lxml import etree	
import gzip            
import logging         
import collections   
import os      			
import subprocess			
import math				
import sys			
import re
import yaml
from utils.log_setup import logger
from utils.find_config import config_path, command_config			


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
def threshFinder(qct_parse,video_path,inFrame,startObj,pkt,tag,over,thumbPath,thumbDelay,thumbExportDelay):
	tagValue = float(inFrame[tag])
	frame_pkt_dts_time = inFrame[pkt]
	if "MIN" in tag or "LOW" in tag:
		under = over
		if tagValue < float(under): # if the attribute is under usr set threshold
			timeStampString = dts2ts(frame_pkt_dts_time)
			#logging.warning(tag + " is under " + str(under) + " with a value of " + str(tagValue) + " at duration " + timeStampString)
			if qct_parse['thumbExport'] and (thumbDelay > int(thumbExportDelay)): # if thumb export is turned on and there has been enough delay between this frame and the last exported thumb, then export a new thumb
				printThumb(video_path,tag,startObj,thumbPath,tagValue,timeStampString)
				thumbDelay = 0
			return True, thumbDelay # return true because it was over and thumbDelay
		else:
			return False, thumbDelay # return false because it was NOT over and thumbDelay
	else:
		if tagValue > float(over): # if the attribute is over usr set threshold
			timeStampString = dts2ts(frame_pkt_dts_time)
			#logging.warning(tag + " is over " + str(over) + " with a value of " + str(tagValue) + " at duration " + timeStampString)
			if qct_parse['thumbExport'] and (thumbDelay > int(thumbExportDelay)): # if thumb export is turned on and there has been enough delay between this frame and the last exported thumb, then export a new thumb
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
		logger.warning(f"Exporting thumbnail image of {baseName} to {os.path.basename(ffoutputFramePath)}")
		output = subprocess.Popen(ffmpegString,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
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
							logger.info("Bars start at " + str(frameDict[pkt]) + " (" + dts2ts(frameDict[pkt]) + ")")						
						durationEnd = float(frameDict[pkt])
					else:
						if durationStart != "" and durationEnd != "" and durationEnd - durationStart > 2: 
							logger.info("Bars ended at " + str(frameDict[pkt]) + " (" + dts2ts(frameDict[pkt]) + ")")							
							break
			elem.clear() # we're done with that element so let's get it outta memory
	return durationStart, durationEnd

def analyzeIt(qct_parse,video_path,profile,startObj,pkt,durationStart,durationEnd,thumbPath,thumbDelay,thumbExportDelay,framesList,frameCount=0,overallFrameFail=0):
	kbeyond = {} # init a dict for each key which we'll use to track how often a given key is over
	fots = ""
	if qct_parse['tagname']:
		kbeyond[qct_parse['tagname']] = 0 
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
							logger.debug(f"qct-parse started at {str(durationStart)} seconds and stopped at {str(frame_pkt_dts_time)} seconds {dts2ts(frame_pkt_dts_time)} or {str(frameCount)} frames")
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
					if qct_parse['profile'] is True:								# display "timestamp: Tag Value" (654.754100: YMAX 229) to the terminal window
						logger.debug(framesList[-1][pkt] + ": " + qct_parse['tagname'] + " " + framesList[-1][qct_parse['tagname']])
					# Now we can parse the frame data from the buffer!	
					if qct_parse['over'] or qct_parse['under'] and qct_parse['profile'] is None: # if we're just doing a single tag
						tag = qct_parse['tagname']
						if qct_parse['over']:
							over = float(qct_parse['over'])
						if qct_parse['under']:
							over = float(qct_parse['under'])
						# ACTAULLY DO THE THING ONCE FOR EACH TAG
						frameOver, thumbDelay = threshFinder(qct_parse,video_path,framesList[-1],startObj,pkt,tag,over,thumbPath,thumbDelay,thumbExportDelay)
						if frameOver is True:
							kbeyond[tag] = kbeyond[tag] + 1 # note the over in the keyover dictionary
					elif qct_parse['profile'] is not None: # if we're using a profile
						for k,v in profile.items():
							# confirm k (tag) is in config.yaml profile
							if v is not None:
								tag = k
								over = float(v)
								# ACTUALLY DO THE THING ONCE FOR EACH TAG
								frameOver, thumbDelay = threshFinder(qct_parse,video_path,framesList[-1],startObj,pkt,tag,over,thumbPath,thumbDelay,thumbExportDelay)
								if frameOver is True:
									kbeyond[k] = kbeyond[k] + 1 # note the over in the key over dict
									if not frame_pkt_dts_time in fots: # make sure that we only count each over frame once
										overallFrameFail = overallFrameFail + 1
										fots = frame_pkt_dts_time # set it again so we don't dupe
					thumbDelay = thumbDelay + 1				
			elem.clear() # we're done with that element so let's get it outta memory
	return kbeyond, frameCount, overallFrameFail


# This function is admittedly very ugly, but what it puts out is very pretty. Need to revamp 	
def printresults(kbeyond,frameCount,overallFrameFail, qctools_check_output):
	with open(qctools_check_output, 'w') as f:
		f.write("**************************\n")
		f.write("\nqct-parse results summary:\n")
		if frameCount == 0:
			percentOverString = "0"
		else:
			f.write("\nTotalFrames:\t" + str(frameCount))
			f.write("\nBy Tag:\n")
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
				f.write(k + ":\t" + str(kbeyond[k]) + "\t" + percentOverString + "\t% of the total # of frames")
				f.write("\n")
			f.write("\n\nOverall:")
			f.write("\nFrames With At Least One Fail:\t" + str(overallFrameFail) + "\t" + percentOverallString + "\t% of the total # of frames")
			f.write("\n**************************")
	return
	
def run_qctparse(video_path, qctools_output_path, qctools_check_output):
	logger.info("Starting qct-parse")
	
	###### Initialize variables ######
	qct_parse = command_config.command_dict['tools']['qct-parse']
	
	startObj = qctools_output_path
	
	# Set buffer size
	if qct_parse['buffSize'] is not None:
		buffSize = int(qct_parse['buffSize'])   # cast the input buffer as an integer
		if buffSize%2 == 0:
			buffSize = buffSize + 1
	else:
		buffSize = 11
	
	# Set thumbExport delay
	if qct_parse['thumbExportDelay'] is not None:
		thumbDelay = int(qct_parse['thumbExportDelay'])	# get a seconds number for the delay in the original file btw exporting tags
	else:
		thumbDelay = 9000
	thumbExportDelay = thumbDelay
	
	# Set parentDir and baseName
	parentDir = os.path.dirname(startObj)
	baseName = os.path.basename(startObj)
	baseName = baseName.replace(".qctools.xml.gz", "")

	# Initialize duration variables, may be over written...
	durationStart = qct_parse['durationStart']
	durationEnd = qct_parse['durationEnd']

	# set the start and end duration times
	if qct_parse['barsDetection']:
		durationStart = ""				# if bar detection is turned on then we have to calculate this
		durationEnd = ""				# if bar detection is turned on then we have to calculate this
	elif qct_parse['durationStart'] is not None:
		durationStart = float(qct_parse['durationStart']) 	# The duration at which we start analyzing the file if no bar detection is selected
	elif qct_parse['durationEnd'] != 99999999 and qct_parse['durationEnd'] is not None:
		durationEnd = float(qct_parse['durationEnd']) 	# The duration at which we stop analyzing the file if no bar detection is selected
	else:
		durationStart = 0
		durationEnd = 99999999

	# Initialize counts
	overcount = 0	# init count of overs
	undercount = 0	# init count of unders
	count = 0		# init total frames counter
	framesList = collections.deque(maxlen=buffSize)		# init holding object for holding all frame data in a circular buffer. 
	bdFramesList = collections.deque(maxlen=buffSize) 	# init holding object for holding all frame data in a circular buffer. 

	# set the path for the thumbnail export
	metadata_dir = os.path.dirname(qctools_output_path)
	thumbPath = metadata_dir
	if qct_parse['tagname']: # if tag is in command_config.yaml
		if qct_parse['profile']: # if profile has been specified 
			logger.error(f"Values will be assessed against profile in command_config.yaml: {qct_parse['profile']}\nTagname cannot be used in combination with profile. Listed tagname in command_config.yaml will be ignored: {qct_parse['tagname']}")
			thumbPath = os.path.join(metadata_dir, "ThumbExports")
		elif qct_parse['over']: # if the tag is looking for a threshold Over
			thumbPath = os.path.join(metadata_dir, str(qct_parse['tagname']) + "." + str(qct_parse['over']))
		elif qct_parse['under']: # if the tag was looking for a threshold Under
			thumbPath = os.path.join(metadata_dir, str(qct_parse['tagname']) + "." + str(qct_parse['under']))
	else:
		thumbPath = os.path.join(metadata_dir, "ThumbExports")
	
	if not os.path.exists(thumbPath):
		os.makedirs(thumbPath)
	
	profile = {} # init a dictionary where we'll store reference values from config.yaml file
	
	# init a list of every tag available in a QCTools Report
	tagList = ["YMIN","YLOW","YAVG","YHIGH","YMAX","UMIN","ULOW","UAVG","UHIGH","UMAX","VMIN","VLOW","VAVG","VHIGH","VMAX","SATMIN","SATLOW","SATAVG","SATHIGH","SATMAX","HUEMED","HUEAVG","YDIF","UDIF","VDIF","TOUT","VREP","BRNG","mse_y","mse_u","mse_v","mse_avg","psnr_y","psnr_u","psnr_v","psnr_avg"]
	
	if qct_parse['profile'] is not None:
		template = qct_parse['profile'] # get the profile/ section name from the command config
		if template in config_path.config_dict['qct-parse']['profiles']:
		# If the template matches one of the profiles
			for t in tagList:
				if t in config_path.config_dict['qct-parse']['profiles'][template]:
					profile[t] = config_path.config_dict['qct-parse']['profiles'][template][t]
	
	# open qctools report 
	# determine if report stores pkt_dts_time or pkt_pts_time
	with gzip.open(startObj) as xml:    
		for event, elem in etree.iterparse(xml, events=('end',), tag='frame'):  # iterparse the xml doc
			if elem.attrib['media_type'] == "video":  # get just the video frames
				# we gotta find out if the qctools report has pkt_dts_time or pkt_pts_time ugh
				match = re.search(r"pkt_.ts_time", etree.tostring(elem).decode('utf-8'))
				if match:
					pkt = match.group()
					break
	
	######## Iterate Through the XML for Bars detection ########
	if qct_parse['barsDetection']:
		logger.debug(f"\nStarting Bars Detection on {baseName}")
		durationStart,durationEnd = detectBars(startObj,pkt,durationStart,durationEnd,framesList,buffSize)

	######## Iterate Through the XML for General Analysis ########
	logger.debug(f"\nStarting qct-parse analysis on {baseName}")
	kbeyond, frameCount, overallFrameFail = analyzeIt(qct_parse,video_path,profile,startObj,pkt,durationStart,durationEnd,thumbPath,thumbDelay,thumbExportDelay,framesList)
	
	logger.info(f"\nqct-parse finished processing file: {baseName}.qctools.xml.gz")

	logger.debug(f"qct-parse summary written to {qctools_check_output}")
	
	# do some maths for the printout
	if qct_parse['over'] or qct_parse['under'] or qct_parse['profile'] is not None:
		printresults(kbeyond,frameCount,overallFrameFail, qctools_check_output)
	
	return

if __name__ == "__main__":
	#if len(sys.argv) != 2:
	#	print("Usage: python qct-parse.py <input_video> <qctools_report>")
	#	sys.exit(1)
	video_path = sys.argv[1]
	report_path = sys.argv[2]
	qctools_check_output = os.path.dirname(video_path)
	if not os.path.isfile(report_path):
		print(f"Error: {report_path} is not a valid file.")
		sys.exit(1)
	run_qctparse(video_path, report_path, qctools_check_output)