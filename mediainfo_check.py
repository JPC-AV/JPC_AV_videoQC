## creates the function "parse_mediainfo" which takes the argument "file_path" which is intended to be a mediainfo -f text file
# the majority of this script is defining this function. But the function is not run until the last line fo the script
def parse_mediainfo(file_path):
    # creates a dictionary of expected keys and values for the mediainfo output section "General"
    expected_general = {
        "File extension": "mkv",
        "Format": "Matroska",
        "Overall bit rate mode": "VBR",
    }
    # creates a dictionary of expected keys and values for the mediainfo output section "Video"
    expected_video = {
        "Format": "FFV1",
        "Format settings, GOP": "N=1",
        "Codec ID": "V_MS/VFW/FOURCC / FFV1",
        "Width": "720",
        "Height": "486",
        "Pixel aspect ratio": "0.900",
        "Display aspect ratio": "1.333",
        "Frame rate mode": "CFR",
        "Frame rate": "29.970",
        "Standard": "NTSC",
        "Color space": "YUV",
        "Chroma subsampling": "4:2:2",
        "Bit depth": "10",
        "Scan type": "Interlaced",
        "Scan order": "Bottom Field First",
        "Compression mode": "Lossless",
        "Color primaries": "BT.601 NTSC",
        "colour_primaries_Source": "Container",
        "Transfer characteristics": "BT.709",
        "transfer_characteristics_Source": "Container",
        "Matrix coefficients": "BT.601",
        "MaxSlicesCount": "24",
        "ErrorDetectionType": "Per slice",
    }
    # creates a dictionary of expected keys and values for the mediainfo output section "Audio"
    expected_audio = {
        "Format": "FLAC",
        "Channel(s)": "2 channels",
        "Channel positions": "Front: L R",
        "Sampling rate": "48000",
        "Bit depth": "24",
        "Compression mode": "Lossless",
        "Writing library": "Lavc59.37.100 flac",
    }

    with open(file_path, 'r') as file:
    # open mediainfo text file as variable "file"
        lines = file.readlines()
        # define variable 'lines' as all individual lines in file (to be parsed in next "for loop")

    current_section = None
    # creates empty variable "current_section"
    section_data = {}
    # creates empty dictionary "section_data"
    # this dictionary will actually store 3 separate dictionaries inside of it, one for each section

    ## Explination of for loop below:
    # The 'for loop' below goes through the mediainfo text file line by line, one at a time
    # if the line matches one of the 3 sections, it assigns the section to the variable "current_section" 
    # and creates a new dictionary within the "section_data" dictionary named after the section: General, Video or Audio
    # if the line does not match one of the 3 sections, it is a line with a mediainfo field and corresponding value
    # a line that does not match one of the 3 sections will be below one fo the 3 section headers, and therefore the "current_section" variable will be assigned
    # the mediainfo field and value are then assigned to the current section's dictionary, which is stored within the section_data dictionary
    
    for line in lines:
    # for each line in mediainfo text file
        line = line.strip()
        # strips line of blank space with python function strip()
        if line.startswith("General"):
            current_section = "General"
            # if line starts with "General", assigns variable current_section to "General"
            section_data[current_section] = {}
            # creates new "General" dictionary within "section_data" dictionary
        elif line.startswith("Video"):
            current_section = "Video"
            # if line starts with "Video", assigns variable current_section to "Video"
            section_data[current_section] = {}
            # creates new "Video" dictionary within "section_data" dictionary
        elif line.startswith("Audio"):
            current_section = "Audio"
            # if line starts with "Audio", assigns variable current_section to "Audio"
            section_data[current_section] = {}
            # creates new "Audio" dictionary within "section_data" dictionary
        elif line:
        # if line does not start with General, Video, or Audio, then:
            key, value = [x.strip() for x in line.split(":", 1)]
            #assign variable "key" to string before ":" and variable "value" to string after ":"
            if current_section and key in section_data[current_section]:
                # if the variable "current_section" is assigned and matches one of the new dictionaries
                # and if the variable "key" is assigned, then:
                section_data[current_section][key] = value
                # key is a key in the new dictionary (General, Video, or Audio) and value is matched to the key, in a key:value pair

    ## Explination of the loops below:
    # The loops below assign the variables "expected_key" and "expected_value" to the key:value pairs in the "expected" dictionaries defined at the beginning of the function
    # the variable "actual_value" is used to define the value to the key matching the "expected_yey" in the section_data[current_section] dictionary (defined in the loop above)
    # if the actual_value variable and the expected_valu variable don't match, then a string stating both values is appened to a list called "differences"

    differences = []
    # Create empty list, "differences"
    for expected_key, expected_value in expected_general.items():
    # defines variables "expected_key" and "expected_value" to the dictionary "expected_general"
        if expected_key in section_data["General"]:
        # if the key in the dictionary "General"
            actual_value = section_data["General"][expected_key]
            # assigns the variable "actual_value" to the value that matches the key in the dictionary "General"
            # I'm not sure if this should be "key" or "expected_key" honestly. Perhaps there should be an additional line for if key = expected_key or something?
            if actual_value != expected_value:
            # if variable "actual_value" does not match "expected value" defined in first line as the values from the dictionary expected_general, then
                differences.append(f"General: {expected_key}\nExpected: {expected_value}\nActual: {actual_value}\n")
                # append this string to the list "differences"
    
    for expected_key, expected_value in expected_video.items():
    # defines variables "expected_key" and "expected_value" to the dictionary "expected_video"
        if expected_key in section_data["Video"]:
        # if the key in the dictionary "Video"
            actual_value = section_data["Video"][expected_key]
            # assigns the variable "actual_value" to the value that matches the key in the dictionary "Video"
            # I'm not sure if this should be "key" or "expected_key" honestly. Perhaps there should be an additional line for if key = expected_key or something?
            if actual_value != expected_value:
            # if variable "actual_value" does not match "expected value" defined in first line as the values from the dictionary expected_video, then
                differences.append(f"Video: {expected_key}\nExpected: {expected_value}\nActual: {actual_value}\n")
                # append this string to the list "differences"

    for expected_key, expected_value in expected_audio.items():
    # defines variables "expected_key" and "expected_value" to the dictionary "expected_audio"
        if expected_key in section_data["Audio"]:
        # if the key in the dictionary "Audio"
            actual_value = section_data["Audio"][expected_key]
            # assigns the variable "actual_value" to the value that matches the key in the dictionary "Audio"
            # I'm not sure if this should be "key" or "expected_key" honestly. Perhaps there should be an additional line for if key = expected_key or something?
            if actual_value != expected_value:
                differences.append(f"Audio: {expected_key}\nExpected: {expected_value}\nActual: {actual_value}\n")
                # append this string to the list "differences"

    if not differences:
    # if the list "differences" is empty, then
        print("All specified fields and values found in the MediaInfo output.")
    else:
    # if the list "differences" is not empty, then
        print("Some specified fields or values are missing or don't match:")
        for diff in differences:
            print(diff)

file_path = "JPCspecs_mi.txt"
# assigns variable "file_path" to the text file "JPCspecs_mi.txt"
# This part of the script is for testing purposes and it will need to change to assign file_path programatically when run on a directory or something... TBD

parse_mediainfo(file_path)
#runs the function "parse_mediainfo" on the file assigned to the variable "file_path"