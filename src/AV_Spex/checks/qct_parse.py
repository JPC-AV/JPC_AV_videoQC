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
import operator
from statistics import median
from ..utils.log_setup import logger
from ..utils.find_config import config_path, command_config			


def get_duration(video_path):
	"""
    Retrieves the duration of a video file using the ffprobe tool.

    Parameters:
        video_path (str): The file path of the video file.

    Returns:
        str: The duration of the video in seconds.
    """

	command = [
		'ffprobe',
		'-v', 'error',
		'-show_entries', 'format=duration',
		'-of', 'csv=p=0',
		video_path
	]
	result = subprocess.run(command, stdout=subprocess.PIPE)
	duration = result.stdout.decode().strip()
	return duration

# Dictionary to map the string to the corresponding operator function
operator_mapping = {
    'lt': operator.lt,
    'gt': operator.gt,
}

# Creates timestamp for pkt_dts_time
def dts2ts(frame_pkt_dts_time):
	"""
    Converts a time in seconds to a formatted time string in HH:MM:SS.ssss format.

    Parameters:
        frame_pkt_dts_time (str): The time in seconds as a string.

    Returns:
        str: The formatted time string.
    """

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
def threshFinder(qct_parse,video_path,inFrame,startObj,pkt,tag,over,comp_op,thumbPath,thumbDelay,thumbExportDelay):
	"""
    Compares tagValue in frameDict (from qctools.xml.gz) with threshold from config

    Parameters:
        qct_parse (dict): qct-parse dictionary from command_config.yaml 
        video_path (file): Path to the video file.
        inFrame (dict): The most recent frameDict added to framesList
        startObj (qctools.xml.gz): Starting object or reference, used in logging or naming.
        pkt (str): The attribute key used to extract timestamps from <frame> tag in qctools.xml.gz.
        tag (str): Attribute tag from <frame> tag in qctools.xml.gz, is checked against the threshold.
        over (float): The threshold value to compare against, from config
        comp_op (callable): The comparison operator function (e.g., operator.lt, operator.gt).
        thumbPath (str): Path where thumbnails are saved.
        thumbDelay (int): Current delay count between thumbnails.
        thumbExportDelay (int): Required delay count between exporting thumbnails.

    Returns:
        tuple: (bool indicating if threshold was met, updated thumbDelay)
    """

	tagValue = float(inFrame[tag])
	frame_pkt_dts_time = inFrame[pkt]
	# Perform the comparison using the retrieved operator if the attribute is over/under threshold
	if comp_op(float(tagValue), float(over)) :
		timeStampString = dts2ts(frame_pkt_dts_time)
		#logging.warning(f"{tag} is {comp_op} {str(over)} with a value of {str(tagValue)} at duration {timeStampString}")
		if qct_parse['thumbExport'] and (thumbDelay > int(thumbExportDelay)): # if thumb export is turned on and there has been enough delay between this frame and the last exported thumb, then export a new thumb
			printThumb(video_path,tag,startObj,thumbPath,tagValue,timeStampString)
			thumbDelay = 0
		return True, thumbDelay # return true because it was over and thumbDelay
	else:
		return False, thumbDelay # return false because it was NOT over and thumbDelay

#  print thumbnail images of overs/unders		
#  Need to update - file naming convention has changed
def printThumb(video_path,tag,startObj,thumbPath,tagValue,timeStampString):
	"""
    Exports a thumbnail image for a specific frame 

    Parameters:
        video_path (str): Path to the video file.
        tag (str): Attribute tag of the frame, used for naming the thumbnail.
        startObj
	"""
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
def detectBars(startObj,pkt,durationStart,durationEnd,framesList):
	"""
    USes specific luminance patterns (defined by YMAX, YMIN, and YDIF attributes) to detect the
    presence of color bars. If bars are detected, it logs the start and end times. The function is designed to
    check every 25th frame.

    Parameters:
        startObj (qctools.xml.gz): A gzip-compressed XML file containing frame attributes.
        pkt (str): The attribute key used to extract timestamps from <frame> tag in qctools.xml.gz.
        durationStart (float): Initial timestamp marking the potential start of detected bars.
        durationEnd (float): Timestamp marking the end of detected bars.
        framesList (list): List of frameDict dictionaries

    Returns:
        tuple: Returns a tuple containing the start and end timestamps of detected bars.
    """

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
							barsStartString = "Bars start at " + str(frameDict[pkt]) + " (" + dts2ts(frameDict[pkt]) + ")"
						durationEnd = float(frameDict[pkt])
					else:
						if durationStart != "" and durationEnd != "" and durationEnd - durationStart > 2: 
							logger.info("Bars ended at " + str(frameDict[pkt]) + " (" + dts2ts(frameDict[pkt]) + ")")
							barsEndString = "Bars ended at " + str(frameDict[pkt]) + " (" + dts2ts(frameDict[pkt]) + ")"
							break
			elem.clear() # we're done with that element so let's get it outta memory
	return durationStart, durationEnd, barsStartString, barsEndString

def evalBars(startObj,pkt,durationStart,durationEnd,framesList):
	with gzip.open(startObj) as xml:	
		for event, elem in etree.iterparse(xml, events=('end',), tag='frame'): # iterparse the xml doc
			if elem.attrib['media_type'] == "video": 	# get just the video frames
				frame_pkt_dts_time = elem.attrib[pkt] 	# get the timestamps for the current frame we're looking at
				if frame_pkt_dts_time >= str(durationStart): 	# only work on frames that are after the start time
					if float(frame_pkt_dts_time) > durationEnd:		# only work on frames that are before the end time
						logger.debug(f"qct-parse bars detection complete")
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

def get_duration(video_path):
	"""
    Retrieves the duration of a video file using ffprobe.

    This function executes an ffprobe command to obtain the duration of the specified video file.
    The output is processed to return the duration as a string.

    Parameters:
        video_path (str): The file path of the video for which the duration is to be retrieved.

    Returns:
        str: The duration of the video in seconds as a string.
    """
	
	command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'csv=p=0',
        video_path
    ]
	result = subprocess.run(command, stdout=subprocess.PIPE)
	duration = result.stdout.decode().strip()
	return duration

def find_common_durations(content_over):
    """
    Identifies common durations across different content tags.

    Extracts tags and their associated durations from content_over dictionary, and uses set
    intersection to find durations that are common across all tags.

    Parameters:
        content_over (dict): A dictionary with tags as keys and sets of durations (strings) as values.

    Returns:
        set: A set containing durations that are common across all provided tags.
    """

    # Extract all tags and their durations into a dictionary of sets
    tag_durations = {tag: set(durations) for tag, durations in content_over.items()}

    # Use set intersection to find common durations across all tags
    common_durations = set.intersection(*tag_durations.values())
    return common_durations

def print_consecutive_durations(durations, qctools_check_output, contentFilter_name):
	"""
    Intended to be used with detectContentFilter and find_common_durations
	
	Writes the start and end times of consecutive segments to a file and logs them.

    This function takes a list of durations (each a string in 'HH:MM:SS' format), sorts them,
    and identifies consecutive segments where the time difference between segments is less than 5 seconds.
    These segments are then written to a specified output file.

    Parameters:
        durations (list of str): A list of time durations in 'HH:MM:SS' format.
        qctools_check_output (str): The file path where the output should be written.
        contentFilter_name (str): The name of the content filter used to determine the thresholds.

    Returns:
        None
    """

	logger.info(f"Segments found within thresholds of content filter {contentFilter_name}:")

	sorted_durations = sorted(durations, key=lambda x: list(map(float, x.split(':'))))

	start_time = None
	end_time = None

	with open(qctools_check_output, 'a') as f:
		f.write("**************************\n")
		f.write("\nqct-parse content detection summary:\n")
		f.write(f"\nSegments found within thresholds of content filter {contentFilter_name}:\n")

		for i in range(len(sorted_durations)):
			if start_time is None:
				start_time = sorted_durations[i]
				end_time = sorted_durations[i]
			else:
				current_time = sorted_durations[i]
				previous_time = sorted_durations[i - 1]

				current_seconds = sum(x * float(t) for x, t in zip([3600, 60, 1], current_time.split(':')))
				previous_seconds = sum(x * float(t) for x, t in zip([3600, 60, 1], previous_time.split(':')))

				if current_seconds - previous_seconds < 5:
					end_time = current_time
				else:
					if start_time != end_time:
						logger.info(f"{start_time} - {end_time}")
						f.write(f"{start_time} - {end_time}\n")
					else:
						logger.info(start_time)
						f.write(start_time)
					start_time = current_time
					end_time = current_time

		# Print the last range or single time
		if start_time and end_time:
			if start_time != end_time:
				logger.info(f"{start_time} - {end_time}")
				f.write(f"{start_time} - {end_time}\n")
			else:
				logger.info(start_time)
				f.write(start_time)
		f.write("\n**************************")


# Modified version of detectBars for finding segments that meet all thresholds instead of any thresholds (like analyze does)
def detectContentFilter(startObj,pkt,contentFilter_name,qctools_check_output,framesList):
	"""
    Checks values against thresholds of multiple values

    Parameters:
        startObj (qctools.xml.gz): A gzip-compressed XML file containing frame attributes.
        pkt (str): The attribute key used to extract timestamps from <frame> tag in qctools.xml.gz.
        contentFilter_name (str): The name of the content filter configuration to apply.
        qctools_check_output (str): The file path where segments meeting the content filter criteria are written.
    	framesList: List of frameDict dictionaries
    """
	
	content_over = {}

	for tag, settings in config_path.config_dict['qct-parse']['content'][contentFilter_name].items():
		content_over[tag] = []

	with gzip.open(startObj) as xml:	
		for event, elem in etree.iterparse(xml, events=('end',), tag='frame'): 	# iterparse the xml doc
			if elem.attrib['media_type'] == "video" or elem.attrib['media_type'] == "audio": 	# get audio and video frames
				frame_pkt_dts_time = elem.attrib[pkt] 											# get the timestamps for the current frame we're looking at
				frameDict = {}  																# start an empty dict for the new frame
				frameDict[pkt] = frame_pkt_dts_time
				for t in list(elem):    										# iterating through each attribute for each element
					if elem.attrib['media_type'] == "audio":
						keySplit = t.attrib['key'].replace('lavfi.astats.', '')  					# split the names 
						if '.' in keySplit:
							# Split the string at the period and join with an underscore
							audio_keyParts = keySplit.split('.')
							keyName = '_'.join(audio_keyParts)
							frameDict[keyName] = t.attrib['value']	
						else:
							# Use the cleaned line as the keyName if no period is present
							keyName = keySplit
					elif elem.attrib['media_type'] == "video":
						keySplit = t.attrib['key'].split(".")   					# split the names by dots 
						keyName = str(keySplit[-1])             					# get just the last word for the key name
						if len(keyName) == 1:										# if it's psnr or mse, keyName is gonna be a single char
							keyName = '.'.join(keySplit[-2:])						# full attribute made by combining last 2 parts of split with a period in btw
						frameDict[keyName] = t.attrib['value']						# add each attribute to the frame dictionary
				framesList.append(frameDict)
				for tag, config_value in config_path.config_dict['qct-parse']['content'][contentFilter_name].items():
					tag_threshold, op_string = config_value.split(", ")
					thresh = float(tag_threshold)
					comp_op = operator_mapping[op_string]
					if tag in frameDict:
						# Perform the comparison using the retrieved operator if the attribute is over/under threshold
						if comp_op(float(frameDict[tag]), float(thresh)) :
							timeStampString = dts2ts(frame_pkt_dts_time)
							content_over[tag].append(timeStampString)
				#thumbDelay = thumbDelay + 1
		elem.clear() # we're done with that element so let's get it outta memory
		common_durations = find_common_durations(content_over)
		if common_durations:
			print_consecutive_durations(common_durations, qctools_check_output, contentFilter_name)
		else:
			logger.error(f"No segments found matching content filter: {contentFilter_name}")

def getCompFromConfig(qct_parse,profile,tag):
	color_bar_keys = ['YMAX', 'YMIN', 'UMIN', 'UMAX', 'VMIN', 'VMAX', 'SATMIN', 'SATMAX']
	if qct_parse['profile']:
		template = qct_parse['profile']
		if set(profile.keys()) == set(config_path.config_dict['qct-parse']['profiles'][template].keys()):
			if "MIN" in tag or "LOW" in tag:
				comp_op = operator.lt
			else:
				comp_op = operator.gt
	if set(profile.keys()) == set(color_bar_keys):
		if "MIN" in tag:
			comp_op = operator.gt
		else:
			comp_op = operator.lt
	return comp_op


def analyzeIt(qct_parse,video_path,profile,startObj,pkt,durationStart,durationEnd,thumbPath,thumbDelay,thumbExportDelay,framesList,frameCount=0,overallFrameFail=0):
	"""
    Analyzes video frames to detect exceeded specified thresholds defined in a profile or tag,
    and optionally tracks and exports thumbnails for these frames.

    Parameters:
        qct_parse (dict): qct-parse dictionary from command_config.yaml 
        video_path (video file): Path to the video file being analyzed.
        profile (dict): A dictionary of tags and corresponding thresholds from profiles in config.yaml
        startObj (qctools.xml.gz): Starting object or reference, used in logging or naming.
        pkt (str): The attribute key used to extract timestamps from <frame> tag in qctools.xml.gz.
        durationStart (float): The start time in seconds for the analysis.
        durationEnd (float): The end time in seconds for the analysis.
        thumbPath (str): Directory path where thumbnails are saved.
        thumbDelay (int): Delay count between thumbnail exports.
        thumbExportDelay (int): Required delay count between exporting thumbnails.
        framesList (list): List of frameDict dictionaries
        frameCount (int, optional): Initial count of frames processed.
        overallFrameFail (int, optional): Count of frames that fail based on the profile.

    Returns:
        tuple: A tuple containing a dictionary of tags with the count of their exceedances, total frame count, and count of overall frame failures.
    """
	kbeyond = {} # init a dict for each key which we'll use to track how often a given key is over
	fots = "" # acronym for Frame Over Threshold Setting, I think? Used to prevent duplication of overall frame fail count for qct_parse['profile'] or qct_parse['evaluateBars']
	if profile == config_path.config_dict['qct-parse']['fullTagList']:
		for each_tag, tag_operator, tag_thresh in qct_parse['tagname']:
			if each_tag not in profile:
				logger.critical(f"The tag name {each_tag} retrieved from the command_config, is not listed in the fullTagList in config.yaml. Exiting qct-parse tag check!")
				break
			else:
				kbeyond[each_tag] = 0 
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
							logger.debug(f"qct-parse started at {str(durationStart)} seconds and stopped at {str(frame_pkt_dts_time)} seconds {dts2ts(frame_pkt_dts_time)}")
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
					#if qct_parse['profile']:								# display "timestamp: Tag Value" (654.754100: YMAX 229) to the terminal window
					#	logger.debug(framesList[-1][pkt] + ": " + qct_parse['tagname'] + " " + framesList[-1][qct_parse['tagname']])
					# Now we can parse the frame data from the buffer!	
					if profile == config_path.config_dict['qct-parse']['fullTagList']: # if we're just doing a single tag
						for config_tag, config_op, config_value in qct_parse['tagname']:
							over = float(config_value)
							comp_op = operator_mapping[config_op]
							if config_tag in frameDict:
								# ACTUALLY DO THE THING ONCE FOR EACH TAG
								tag = config_tag
								frameOver, thumbDelay = threshFinder(qct_parse,video_path,framesList[-1],startObj,pkt,tag,over,comp_op,thumbPath,thumbDelay,thumbExportDelay)
								if frameOver is True:
									kbeyond[config_tag] = kbeyond[config_tag] + 1 					# note the over in the key over dict
									if not frame_pkt_dts_time in fots: 				# make sure that we only count each over frame once
										overallFrameFail = overallFrameFail + 1
										fots = frame_pkt_dts_time 					# set it again so we don't dupe
					else: # if we're using a profile
						for k,v in profile.items():
							if v is not None:
								tag = k
								comp_op = getCompFromConfig(qct_parse,profile,tag)
								over = float(v)
								# ACTUALLY DO THE THING ONCE FOR EACH TAG
								frameOver, thumbDelay = threshFinder(qct_parse,video_path,framesList[-1],startObj,pkt,tag,over,comp_op,thumbPath,thumbDelay,thumbExportDelay)
								if frameOver is True:
									kbeyond[k] = kbeyond[k] + 1 # note the over in the key over dict
									if not frame_pkt_dts_time in fots: # make sure that we only count each over frame once
										overallFrameFail = overallFrameFail + 1
										fots = frame_pkt_dts_time # set it again so we don't dupe
					thumbDelay = thumbDelay + 1				
			elem.clear() # we're done with that element so let's get it outta memory
	return kbeyond, frameCount, overallFrameFail


# This function is admittedly very ugly, but what it puts out is very pretty. Need to revamp 	
def printresults(qct_parse,profile,kbeyond,frameCount,overallFrameFail, qctools_check_output):
	"""
    Writes the analyzeIt results into a summary file, detailing the count and percentage of frames that exceeded the thresholds.

    Parameters:
        kbeyond (dict): Dictionary mapping tags to the count of frames exceeding the thresholds.
        frameCount (int): Total number of frames analyzed.
        overallFrameFail (int): Total number of frames with at least one threshold exceedance.
        qctools_check_output (str): File path to write the output summary.

    Returns:
        None
    """
	color_bar_keys = ['YMAX', 'YMIN', 'UMIN', 'UMAX', 'VMIN', 'VMAX', 'SATMIN', 'SATMAX']
	
	with open(qctools_check_output, 'a') as f:
		f.write("**************************\n")
		if profile == config_path.config_dict['qct-parse']['fullTagList']:
			f.write("\nqct-parse evaluation of user specified tags summary:\n")
		elif set(profile.keys()) == set(color_bar_keys):
			f.write("\nqct-parse color bars evaluation summary:\n")
		else:
			f.write("\nqct-parse profile results summary:\n")
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
			if set(profile.keys()) == set(color_bar_keys):
				f.write("\nFrames Within MAX and MIN of YUV and SAT of Color Bars:\t" + str(overallFrameFail) + "\t" + percentOverallString + "\t% of the total # of frames")
			else:
				f.write("\nFrames With At Least One Fail:\t" + str(overallFrameFail) + "\t" + percentOverallString + "\t% of the total # of frames")
			f.write("\n**************************")
	return

def print_bars_durations(qctools_check_output,barsStartString,barsEndString):
	with open(qctools_check_output, 'a') as f:
		f.write("**************************\n")
		f.write("\nqct-parse color bars found:\n")
		f.write(barsStartString)
		f.write("\n")
		f.write(barsEndString)
		f.write("\n**************************")

def run_qctparse(video_path, qctools_output_path, qctools_check_output):
	"""
    Executes the qct-parse analysis on a given video file, exporting relevant data and thumbnails based on specified thresholds and profiles.

    Parameters:
        video_path (str): Path to the video file being analyzed.
        qctools_output_path (str): Path to the QCTools XML report output.
        qctools_check_output (str): Path where the summary of the qct-parse results will be written.

    """
	logger.info("Starting qct-parse\n")
	
	###### Initialize variables ######
	qct_parse = command_config.command_dict['tools']['qct-parse']
	
	startObj = qctools_output_path
	
	# Set thumbExport delay
	if qct_parse['thumbExportDelay']:
		thumbDelay = int(qct_parse['thumbExportDelay'])	# get a seconds number for the delay in the original file btw exporting tags
	else:
		thumbDelay = 9000
	thumbExportDelay = thumbDelay
	
	# Set parentDir and baseName
	parentDir = os.path.dirname(startObj)
	baseName = os.path.basename(startObj)
	baseName = baseName.replace(".qctools.xml.gz", "")

	# initialize the start and end duration times variables
	durationStart = 0
	durationEnd = 99999999

	# Initialize counts
	overcount = 0	# init count of overs
	undercount = 0	# init count of unders
	count = 0		# init total frames counter
	buffSize = 11
	framesList = collections.deque(maxlen=buffSize)		# init holding object for holding all frame data in a circular buffer. 
	bdFramesList = collections.deque(maxlen=buffSize) 	# init holding object for holding all frame data in a circular buffer. 

	# set the path for the thumbnail export
	metadata_dir = os.path.dirname(qctools_output_path)
	thumbPath = os.path.join(metadata_dir, "ThumbExports")
	
	if qct_parse['thumbExport']:
		if not os.path.exists(thumbPath):
			os.makedirs(thumbPath)
	
	profile = {} # init a dictionary where we'll store reference values from config.yaml file
	
	# init a list of every tag available in a QCTools Report from the fullTagList in the config.yaml
	tagList = list(config_path.config_dict['qct-parse']['fullTagList'].keys())
	
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

	######## Iterate Through the XML for content detection ########
	if qct_parse['detectContent'] and qct_parse['contentFilter'] != None:
		logger.debug(f"Checking for segments of {os.path.basename(video_path)} that match the content filter {qct_parse['contentFilter']}\n")
		duration_str = get_duration(video_path)
		contentFilter_name = qct_parse['contentFilter']
		detectContentFilter(startObj,pkt,contentFilter_name,qctools_check_output,framesList)
	elif qct_parse['detectContent'] and qct_parse['contentFilter'] == None:
		logger.error(f"Cannot run detectContent, no content filter specified in config.yaml\n")

	######## Iterate Through the XML for General Analysis ########
	if qct_parse['profile']:
		template = qct_parse['profile'] # get the profile/ section name from the command config
		if template in config_path.config_dict['qct-parse']['profiles']:
		# If the template matches one of the profiles
			for t in tagList:
				if t in config_path.config_dict['qct-parse']['profiles'][template]:
					profile[t] = config_path.config_dict['qct-parse']['profiles'][template][t]
		logger.debug(f"Starting qct-parse analysis against {qct_parse['profile']} thresholds on {baseName}\n")
		kbeyond, frameCount, overallFrameFail = analyzeIt(qct_parse,video_path,profile,startObj,pkt,durationStart,durationEnd,thumbPath,thumbDelay,thumbExportDelay,framesList)
		printresults(qct_parse,profile,kbeyond,frameCount,overallFrameFail, qctools_check_output)
		logger.debug(f"qct-parse summary written to {qctools_check_output}\n")
	if qct_parse['tagname']:
		logger.debug(f"Starting qct-parse analysis against user input tag thresholds on {baseName}\n")
		profile = config_path.config_dict['qct-parse']['fullTagList']
		kbeyond, frameCount, overallFrameFail = analyzeIt(qct_parse,video_path,profile,startObj,pkt,durationStart,durationEnd,thumbPath,thumbDelay,thumbExportDelay,framesList)
		printresults(qct_parse,profile,kbeyond,frameCount,overallFrameFail, qctools_check_output)
		logger.debug(f"qct-parse summary written to {qctools_check_output}\n")
	
	######## Iterate Through the XML for Bars detection ########
	if qct_parse['barsDetection']:
		durationStart = ""						# if bar detection is turned on then we have to calculate this
		durationEnd = ""						# if bar detection is turned on then we have to calculate this
		duration_str = get_duration(video_path)
		ffprobe_duration = float(duration_str)
		logger.debug(f"\nStarting Bars Detection on {baseName}")
		durationStart, durationEnd, barsStartString, barsEndString = detectBars(startObj,pkt,durationStart,durationEnd,framesList)
		if durationStart == "" and durationEnd == "":
			logger.error("No color bars detected")
		if barsStartString and barsEndString:
			print_bars_durations(qctools_check_output,barsStartString,barsEndString)

	######## Iterate Through the XML for Bars Evaluation ########
	if qct_parse['evaluateBars']:
		evalBars(startObj,pkt,durationStart,durationEnd,framesList)
		# Define the keys for which you want to calculate the average
		keys_to_average = ['YMAX', 'YMIN', 'UMIN', 'UMAX', 'VMIN', 'VMAX', 'SATMIN', 'SATMAX']
		# Initialize a dictionary to store the average values
		average_dict = {key: median([float(frameDict[key]) for frameDict in framesList if key in frameDict]) for key in keys_to_average}
		if average_dict is None:
			logger.critical(f"\nCannot run evaluate color bars\n")
		else:
			logger.debug(f"\nStarting qct-parse color bars evaluation on {baseName}")
			durationStart = 0
			durationEnd = 99999999
			profile = average_dict
			kbeyond, frameCount, overallFrameFail = analyzeIt(qct_parse,video_path,profile,startObj,pkt,durationStart,durationEnd,thumbPath,thumbDelay,thumbExportDelay,framesList)
			printresults(qct_parse,profile,kbeyond,frameCount,overallFrameFail, qctools_check_output)
			logger.debug(f"\nqct-parse bars evaluation complete. \nqct-parse summary written to {qctools_check_output}\n")
			
	logger.info(f"\nqct-parse finished processing file: {baseName}.qctools.xml.gz")
	
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