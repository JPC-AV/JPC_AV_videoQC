from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO
from nicegui import ui

yaml = YAML()
yaml.preserve_quotes = True

with open('/Users/eddycolloton/git/JPC_AV/JPC_AV_videoQC/tests/command_config.yaml', "r") as f:
    command_dict = yaml.load(f)

# Function to apply profile changes
def apply_profile(dict):
    with open('/Users/eddycolloton/git/JPC_AV/JPC_AV_videoQC/tests/command_config.yaml', "w") as f:
        yaml.dump(dict, f)

ui.label('outputs:')

with ui.column():  # Group checkboxes under "outputs"
    ui.checkbox('access_file')
    ui.checkbox('report')

ui.label('fixity:')  # Section header, no checkbox

# Create checkboxes and bind them to command_dict
with ui.column():
    for option in ['access_file', 'report']:
        checkbox = ui.checkbox(option, value=command_dict['outputs'][option] == 'yes')
        checkbox.id = f'outputs.{option}'
        # Bind checkbox value to command_dict
        checkbox.bind_value(command_dict['outputs'], option, forward=lambda val: 'yes' if val else 'no') 

# Fixity options
with ui.column():
    ui.checkbox('check_fixity')
    ui.checkbox('check_stream_fixity')
    ui.checkbox('embed_stream_fixity')
    ui.checkbox('output_fixity')
    ui.checkbox('overwrite_stream_fixity')

with ui.column():
    for option in ['check_fixity', 'check_stream_fixity', 'embed_stream_fixity', 'output_fixity', 'overwrite_stream_fixity']:
        checkbox = ui.checkbox(option, value=command_dict['outputs']['fixity'][option] == 'yes')
        checkbox.id = f'fixity.{option}'
        # Bind checkbox value to command_dict
        checkbox.bind_value(command_dict['outputs']['fixity'], option, forward=lambda val: 'yes' if val else 'no')

ui.button('update yaml', on_click=lambda: apply_profile(command_dict))

ui.run()