from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO
from nicegui import ui, app

yaml = YAML()
yaml.preserve_quotes = True

with open('/Users/eddycolloton/git/JPC_AV/JPC_AV_videoQC/tests/command_config.yaml', "r") as f:
    command_dict = yaml.load(f)

# Function to apply profile changes
def apply_profile(dict):
    with open('/Users/eddycolloton/git/JPC_AV/JPC_AV_videoQC/tests/command_config.yaml', "w") as f:
        yaml.dump(dict, f)

ui.label('outputs:')

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

ui.button('update yaml', on_click=lambda: apply_profile(command_dict))

ui.button('shutdown', on_click=app.shutdown)

ui.run()(reload=False)