import xml.etree.ElementTree as ET
import subprocess
import tempfile
import os
import logging
from log_setup import logger

def make_stream_hash(video_path):
    """Calculate MD5 checksum of video and audio streams using ffmpeg."""
    command = [
        'ffmpeg',
        '-hide_banner', '-loglevel', 'error',
        '-i', video_path,
        '-map', '0',
        '-f', 'streamhash',
        '-hash', 'md5',
        '-'
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, text=True)
    logger.info(f'FFmpeg streamhashing process complete\n')
    # Parse the output to get the MD5 checksum
    stream_hashes = result.stdout.strip().split('\n')
    video_hash = None
    audio_hash = None
    for line in stream_hashes:
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

def embed_fixity(video_path):

    # Make md5 of video/audio stream
    logger.debug(f'\nGenerating video and audio stream hashes. This may take a moment...')
    video_hash, audio_hash = make_stream_hash(video_path)

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

#if __name__ == "__main__":
 #   main()
