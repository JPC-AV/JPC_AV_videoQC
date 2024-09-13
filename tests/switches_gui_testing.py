from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO
from nicegui import ui, app
from nicegui.events import ValueChangeEventArguments

yaml = YAML()
yaml.preserve_quotes = True

with open('/Users/eddycolloton/git/JPC_AV/JPC_AV_videoQC/tests/command_config.yaml', "r") as f:
    command_dict = yaml.load(f)

# Function to apply profile changes
def apply_profile(dict):
    with open('/Users/eddycolloton/git/JPC_AV/JPC_AV_videoQC/tests/command_config.yaml', "w") as f:
        yaml.dump(dict, f)

with ui.row():
    with ui.column():
        ui.label('outputs:') # Section header
        with ui.row():
            s1 = ui.switch(value=command_dict['outputs']['access_file'])
            s1.bind_value(command_dict['outputs'], 'access_file')  # Bind to dictionary
            ui.button('access file', on_click=lambda: s1.set_value(not s1.value))

        with ui.row():
            s2 = ui.switch(value=command_dict['outputs']['report'])
            s2.bind_value(command_dict['outputs'], 'report')  
            ui.button('report', on_click=lambda: s2.set_value(not s2.value))

        ui.label('fixity:')  # Section header
        with ui.row():
            s3 = ui.switch(value=command_dict['outputs']['fixity']['check_fixity'])
            s3.bind_value(command_dict['outputs']['fixity'], 'check_fixity')  
            ui.button('check fixity', on_click=lambda: s3.set_value(not s3.value))

        with ui.row():
            s4 = ui.switch(value=command_dict['outputs']['fixity']['check_stream_fixity'])
            s4.bind_value(command_dict['outputs']['fixity'], 'check_stream_fixity')  
            ui.button('check stream fixity', on_click=lambda: s4.set_value(not s4.value))

        with ui.row():
            s5 = ui.switch(value=command_dict['outputs']['fixity']['embed_stream_fixity'])
            s5.bind_value(command_dict['outputs']['fixity'], 'embed_stream_fixity')  
            ui.button('embed stream fixity', on_click=lambda: s5.set_value(not s5.value))

        with ui.row():
            s6 = ui.switch(value=command_dict['outputs']['fixity']['output_fixity'])
            s6.bind_value(command_dict['outputs']['fixity'], 'output_fixity')  
            ui.button('output fixity', on_click=lambda: s6.set_value(not s6.value))

        with ui.row():
            s7 = ui.switch(value=command_dict['outputs']['fixity']['overwrite_stream_fixity'])
            s7.bind_value(command_dict['outputs']['fixity'], 'overwrite_stream_fixity')  
            ui.button('overwrite stream fixity', on_click=lambda: s7.set_value(not s7.value))

    with ui.column():
        ui.label('tools:')  # Section header

        with ui.card():
            ui.label('Exiftool')
            with ui.row():
                s8 = ui.switch(value=command_dict['tools']['exiftool']['check_exiftool'])
                s8.bind_value(command_dict['tools']['exiftool'], 'check_exiftool')  # Bind to dictionary
                ui.button('check exiftool', on_click=lambda: s8.set_value(not s8.value))
            with ui.row():
                s9 = ui.switch(value=command_dict['tools']['exiftool']['run_exiftool'])
                s9.bind_value(command_dict['tools']['exiftool'], 'run_exiftool')  
                ui.button('run exiftool', on_click=lambda: s9.set_value(not s9.value))

        with ui.card():
            ui.label('FFprobe')
            with ui.row():
                s10 = ui.switch(value=command_dict['tools']['ffprobe']['check_ffprobe'])
                s10.bind_value(command_dict['tools']['ffprobe'], 'check_ffprobe')  
                ui.button('check ffprobe', on_click=lambda: s10.set_value(not s10.value))
            with ui.row():
                s11 = ui.switch(value=command_dict['tools']['ffprobe']['run_ffprobe'])
                s11.bind_value(command_dict['tools']['ffprobe'], 'run_ffprobe')  
                ui.button('run ffprobe', on_click=lambda: s11.set_value(not s11.value))

        with ui.card():
            ui.label('Mediaconch')
            with ui.row():
                s12 = ui.switch(value=command_dict['tools']['mediaconch']['run_mediaconch'])
                s12.bind_value(command_dict['tools']['mediaconch'], 'run_mediaconch')  
                ui.button('run_mediaconch', on_click=lambda: s12.set_value(not s12.value))
            ui.label('mediaconch policy:')
            with ui.row():
                t2 = ui.input(value=command_dict['tools']['mediaconch']['mediaconch_policy'])
                t2.bind_value(command_dict['tools']['mediaconch'], 'mediaconch_policy')

        with ui.card():
            ui.label('MediaInfo')
            with ui.row():
                s13 = ui.switch(value=command_dict['tools']['mediainfo']['check_mediainfo'])
                s13.bind_value(command_dict['tools']['mediainfo'], 'check_mediainfo')  
                ui.button('check mediainfo', on_click=lambda: s13.set_value(not s13.value))
            with ui.row():
                s14 = ui.switch(value=command_dict['tools']['mediainfo']['run_mediainfo'])
                s14.bind_value(command_dict['tools']['mediainfo'], 'run_mediainfo')  
                ui.button('run mediainfo', on_click=lambda: s14.set_value(not s14.value))

        with ui.card():
            ui.label('Mediatrace')
            with ui.row():
                s15 = ui.switch(value=command_dict['tools']['mediatrace']['check_mediatrace'])
                s15.bind_value(command_dict['tools']['mediatrace'], 'check_mediatrace')  
                ui.button('check mediatrace', on_click=lambda: s15.set_value(not s15.value))
            with ui.row():
                s16 = ui.switch(value=command_dict['tools']['mediatrace']['run_mediatrace'])
                s16.bind_value(command_dict['tools']['mediainfo'], 'run_mediatrace')  
                ui.button('run mediatrace', on_click=lambda: s16.set_value(not s16.value))

        with ui.card():
            ui.label('QCTools')
            with ui.row():
                s17 = ui.switch(value=command_dict['tools']['qctools']['check_qctools'])
                s17.bind_value(command_dict['tools']['qctools'], 'check_qctools')  
                ui.button('check qctools', on_click=lambda: s17.set_value(not s17.value))
            with ui.row():
                s18 = ui.switch(value=command_dict['tools']['qctools']['run_qctools'])
                s18.bind_value(command_dict['tools']['qctools'], 'run_qctools')  
                ui.button('run qctools', on_click=lambda: s18.set_value(not s18.value))
            ui.label('qctools extension:')
            with ui.row():
                t1 = ui.input(value=command_dict['outputs']['qctools_ext'])
                t1.bind_value(command_dict['outputs'], 'qctools_ext')

    with ui.column():
        ui.button('update yaml', on_click=lambda: apply_profile(command_dict))
        ui.button('shutdown', on_click=app.shutdown)

ui.run(reload=False)