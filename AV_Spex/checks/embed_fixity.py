import xml.etree.ElementTree as ET
import subprocess
import tempfile
import os
import sys
import logging
from utils.log_setup import logger

def get_total_frames(video_path):
    command = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-count_packets',
        '-show_entries', 'stream=nb_read_packets',
        '-of', 'csv=p=0',
        video_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE)
    total_frames = int(result.stdout.decode().strip())
    return total_frames

def make_stream_hash(video_path):
    """Calculate MD5 checksum of video and audio streams using ffmpeg."""
    
    total_frames = get_total_frames(video_path)
    video_hash = None
    audio_hash = None
    
    ffmpeg_command = [
        'ffmpeg',
        '-hide_banner', '-progress', '-', '-nostats', '-loglevel', 'error',
        '-i', video_path,
        '-map', '0',
        '-f', 'streamhash',
        '-hash', 'md5',
        '-'
    ]
    
    ffmpeg_process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    while True:
        ff_output = ffmpeg_process.stdout.readline()
        if not ff_output:
            break
        frame_prefix = 'frame='
        video_hash_prefix = '0,v,MD5'
        audio_hash_prefix = '1,a,MD5'
        for line in ff_output.split('\n'):
            if line.startswith(frame_prefix):
                current_frame = int(line[len(frame_prefix):])
                percent_complete = (current_frame / total_frames) * 100
                print(f"\rFFmpeg 'streamhash' Progress: {percent_complete:.2f}%", end='', flush=True)
            if line.startswith(video_hash_prefix) or line.startswith(audio_hash_prefix):
                # Split each line by comma
                parts = line.split(',')
                # Extract type and hash
                type_, hash_ = parts[1], parts[2].split('=')[1]
                # Check type and assign hash to appropriate variable
                if type_ == 'v':
                    video_hash = hash_
                elif type_ == 'a':
                    audio_hash = hash_

    return video_hash, audio_hash

def extract_tags(video_path):
    command = f"mkvextract tags {video_path}"
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    return result.stdout

def add_stream_hash_tag(xml_tags, video_hash, audio_hash):
    root = ET.fromstring(xml_tags)

    # Find 'Tag' elements
    tags = root.findall('.//Tag')

    # The tag describing the whole file do not contain the element "Targets", loop through tags to find whole file <Tag>
    tags_without_target = []
    for tag in tags:
        if tag.find('Targets'):
            continue
        else:
            tags_without_target.append(tag)

    # Assigns last_tag to last tag not containing element "Targets"
    last_tag = tags_without_target[-1]

    # Create a new 'Simple' element
    video_md5_tag = ET.Element("Simple")
    name = ET.SubElement(video_md5_tag, "Name")
    name.text = "VIDEO_STREAM_HASH"
    string = ET.SubElement(video_md5_tag, "String")
    string.text = video_hash
    tag_language = ET.SubElement(video_md5_tag, "TagLanguageIETF")
    tag_language.text = "und"

    # Create a new 'Simple' element
    audio_md5_tag = ET.Element("Simple")
    name = ET.SubElement(audio_md5_tag, "Name")
    name.text = "AUDIO_STREAM_HASH"
    string = ET.SubElement(audio_md5_tag, "String")
    string.text = audio_hash
    tag_language = ET.SubElement(audio_md5_tag, "TagLanguageIETF")
    tag_language.text = "und"

    # insert new stream_hash subelement into last_tag
    last_tag.insert(-1, video_md5_tag)
    # insert new stream_hash subelement into last_tag
    last_tag.insert(-1, audio_md5_tag)
    # remove last tag from XML
    root.remove(last_tag)
    # insert last_tag to top of <Tags> tree
    root.insert(0, last_tag)

    return ET.tostring(root, encoding="unicode")

def write_tags_to_temp_file(xml_tags):
    # Create a temporary XML file
    with tempfile.NamedTemporaryFile(mode='w+', suffix=".xml", delete=False) as temp_file:
        temp_file.write(xml_tags)
        temp_file_path = temp_file.name
    return temp_file_path

def write_tags_to_mkv(mkv_file, temp_xml_file):
    command = f'mkvpropedit --tags "global:{temp_xml_file}" "{mkv_file}"'
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    # Check if there's any output
    if stdout:
        # Modify the output as needed
        modified_output = stdout.decode('utf-8').replace('Done.', '')
        logger.info(f'Running mkvpropedit:\n{modified_output}')  # Or do something else with the modified output
    if stderr:
        logger.critical(f"Running mkvpropedit:\n{stderr.decode('utf-8')}")  # Print any errors if they occur

def extract_hashes(xml_tags):
    video_hash = None
    audio_hash = None

    root = ET.fromstring(xml_tags)

    # Find 'video_stream_hash' element
    v_stream_element = root.find('.//Simple[Name="VIDEO_STREAM_HASH"]/String')
    if v_stream_element is not None:
        # Assign MD5 in VIDEO_STREAM_HASH to video_hash
        video_hash = v_stream_element.text
    else:
        logger.warning(f'No video stream hash found')

    # Find 'video_stream_hash' element
    a_stream_element = root.find('.//Simple[Name="AUDIO_STREAM_HASH"]/String')
    if a_stream_element is not None:
        # Assign MD5 in AUDIO_STREAM_HASH to audio_hash
        audio_hash = a_stream_element.text
    else:
        logger.warning(f'No audio stream hash found')

    return video_hash, audio_hash

def compare_hashes(existing_video_hash, existing_audio_hash, video_hash, audio_hash):
    if existing_video_hash == video_hash:
        logger.info("Video hashes match.")
    else:
        logger.critical(f"Video hashes do not match. \nMD5 stored in MKV file: {video_hash} \nGenerated MD5: {existing_video_hash}")

    if existing_audio_hash == audio_hash:
        logger.info("Audio hashes match.")
    else:
        logger.critical(f"Audio hashes do not match. \nMD5 stored in MKV file: {video_hash} \nGenerated MD5: {existing_video_hash}")

def embed_fixity(video_path):

    # Make md5 of video/audio stream
    logger.debug(f'\nGenerating video and audio stream hashes. This may take a moment...')
    video_hash, audio_hash = make_stream_hash(video_path)
    logger.info(f'\nVideo hash = {video_hash}\nAudio hash = {audio_hash}\n')

    # Extract existing tags
    existing_tags = extract_tags(video_path)

    # Add stream_hash tag
    updated_tags = add_stream_hash_tag(existing_tags, video_hash, audio_hash)

    # Write updated tags to a temporary XML file
    temp_xml_file = write_tags_to_temp_file(updated_tags)

    # Write updated tags back to MKV file
    logger.debug('Embedding video and audio stream hashes to XML in MKV file')
    write_tags_to_mkv(video_path, temp_xml_file)

    # Remove the temporary XML file
    os.remove(temp_xml_file)

def validate_embedded_md5(video_path):

    logger.debug(f'Extracting existing video and audio stream hashes')
    existing_tags = extract_tags(video_path)
    existing_video_hash, existing_audio_hash = extract_hashes(existing_tags)
    # Print result of extracting hashes:
    if existing_video_hash is not None:
        logger.info(f'Video stream md5 found: {existing_video_hash}')
    else:
        logger.warning(f'No video stream hash found')

    if existing_audio_hash is not None:
        logger.info(f'Audio stream md5 found: {existing_audio_hash}')
    else:
        logger.warning(f'No audio stream hash found')

    logger.debug(f'\nGenerating video and audio stream hashes. This may take a moment...')
    video_hash, audio_hash = make_stream_hash(video_path)

    logger.debug(f'\n\nValidating stream fixity')
    compare_hashes(existing_video_hash, existing_audio_hash, video_hash, audio_hash)

if __name__ == "__main__":
    if len(sys.argv) != 2:
            print("Usage: python embed_fixity.py <mkv_file>")
            sys.exit(1)
    file_path = sys.argv[1]
    if not os.path.isfile(file_path):
        print(f"Error: {file_path} is not a valid file.")
        sys.exit(1)
    embed_fixity(file_path)