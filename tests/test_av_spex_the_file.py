from AV_Spex import av_spex_the_file

def test_log_overall_time():
    assert av_spex_the_file.log_overall_time(1733854413.191993, 1733854426.615125) == '00:00:13'

def test_check_directory_matches():
    source_directory = "/Users/eddycolloton/git/JPC_AV/sample_files/jpc/JPC_AV_01709"
    video_id = "JPC_AV_01709"

    # Test only the return value
    assert av_spex_the_file.check_directory(source_directory, video_id) is True