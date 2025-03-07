from AV_Spex.utils import dir_setup
from AV_Spex.processing import avspex_processor

def test_log_overall_time():
    assert avspex_processor.log_overall_time(1733854413.191993, 1733854426.615125) == '00:00:13'

def test_check_directory_matches():
    source_directory = "/Users/eddycolloton/git/JPC_AV/sample_files/jpc/JPC_AV_01709"
    video_id = "JPC_AV_01709"

    # Test only the return value
    assert dir_setup.check_directory(source_directory, video_id) is True