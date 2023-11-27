# Roadmap

The following improvements are planned for JPC_AV_videoQC:

- Config
  - Pull expected fields from config.yaml, instead of functions inside python scripts
- Restructure
  - Combine metadata checks into metadata_checks.py to facilitate simpler importing into process_file.py
- Additional functionality
  - ffprobe checks (including encoder settings)
  - qctools
  - md5 checksum       
- Install
  - Run checks to see if dependencies are alreadyed installed
  - Run `pip install` on all required tools
