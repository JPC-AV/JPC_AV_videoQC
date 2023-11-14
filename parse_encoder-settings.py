text = "TAG:ENCODER_SETTINGS=O=VHS, C=Color, S=Analog, VS= NTSC, F=24, A=4:3, R=640×480, T=Sony SVO-5800, O=FFV1mkv, C=Color, V=Composite, S=Analog Stereo, F=24, A=4:3, W=10-bit, R=640×480, M=YUV422p10, T=Blackmagic UltraStudio 4K Mini SN123456, ffmpeg vrecord; in-house, O=FFV1mkv, W=10-bit, R640x480, MYUV422p10 N=AJ Lawrence"

# Extracting the part after "TAG:ENCODER_SETTINGS="
settings_str = text.split("TAG:ENCODER_SETTINGS=")[1]

# Splitting the settings string into key-value pairs
settings_list = [pair.strip() for pair in settings_str.split(",")]

# Creating sublists based on 'O='
sublists = []
current_sublist = []
for pair in settings_list:
    if 'O=' in pair:
        if current_sublist:
            sublists.append(current_sublist)
        current_sublist = [pair]
    else:
        current_sublist.append(pair)

# Adding the last sublist
sublists.append(current_sublist)

# Creating dictionaries from sublists
dictionaries = []
for sublist in sublists:
    settings_dict = {}
    for pair in sublists[0]:
        key, value = pair.split("=")
        settings_dict[key] = value
    for pair in sublists[1]:
        if "=" in pair:
            key, value = pair.split("=")
            settings_dict[key] = value
        else:
            settings_dict['T'] = [settings_dict['T'], pair]
    for pair in sublists[2][:3]:
        if "=" in pair:
            key, value = pair.split("=")
            settings_dict[key] = value
        else:
            settings_dict['W'] = [settings_dict['W'], pair]
            if isinstance(settings_dict['W'], list):
                settings_dict['W'].extend(sublists[2][3].split(' ', 1)[0])
        for pair in (sublists[2][3].split(' ', 1)[1]):
            if "=" in pair:
                key, value = pair.split("=")
                settings_dict[key] = value
    dictionaries.append(settings_dict)

# Printing the result
for i, settings_dict in enumerate(dictionaries, start=1):
    print(f"Dictionary {i}: {settings_dict}")


# https://www.google.com/search?q=python+how+to+append+to+an+existing+value+in+dictionary&oq=&gs_lcrp=EgZjaHJvbWUqCQgCEEUYOxjCAzIJCAAQRRg7GMIDMgkIARBFGDsYwgMyCQgCEEUYOxjCAzIJCAMQRRg7GMIDMgkIBBBFGDsYwgMyCQgFEEUYOxjCAzIJCAYQRRg7GMIDMgkIBxBFGDsYwgPSAQo3NDI2MTNqMGo3qAIIsAIB&sourceid=chrome&ie=UTF-8#kpvalbx=_eslTZbzAMcCz0PEPpOCQ-Aw_27
# https://www.geeksforgeeks.org/python-split-list-into-lists-by-particular-value/#