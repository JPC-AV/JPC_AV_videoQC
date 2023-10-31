def parse_mediainfo(file_path):
    expected_general = {
        "File extension": "mkv",
        "Format": "Matroska",
        "Overall bit rate mode": "VBR",
    }
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
        lines = file.readlines()

    current_section = None
    section_data = {}

    for line in lines:
        line = line.strip()
        if line.startswith("General"):
            current_section = "General"
            section_data[current_section] = {}
        elif line.startswith("Video"):
            current_section = "Video"
            section_data[current_section] = {}
        elif line.startswith("Audio"):
            current_section = "Audio"
            section_data[current_section] = {}
        elif line:
            key, value = [x.strip() for x in line.split(":", 1)]
            if current_section and key in section_data[current_section]:
                section_data[current_section][key] = value

    # Check for differences and print both expected and actual values
    differences = []
    for key, expected_value in expected_general.items():
        if key in section_data["General"]:
            actual_value = section_data["General"][key]
            if actual_value != expected_value:
                differences.append(f"General: {key}\nExpected: {expected_value}\nActual: {actual_value}\n")
    
    for key, expected_value in expected_video.items():
        if key in section_data["Video"]:
            actual_value = section_data["Video"][key]
            if actual_value != expected_value:
                differences.append(f"Video: {key}\nExpected: {expected_value}\nActual: {actual_value}\n")

    for key, expected_value in expected_audio.items():
        if key in section_data["Audio"]:
            actual_value = section_data["Audio"][key]
            if actual_value != expected_value:
                differences.append(f"Audio: {key}\nExpected: {expected_value}\nActual: {actual_value}\n")

    if not differences:
        print("All specified fields and values found in the MediaInfo output.")
    else:
        print("Some specified fields or values are missing or don't match:")
        for diff in differences:
            print(diff)

file_path = "JPCspecs_mi.txt"
parse_mediainfo(file_path)
