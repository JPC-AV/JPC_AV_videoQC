from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO
from nicegui import ui

yaml = YAML()
yaml.preserve_quotes = True


with open('/Users/eddycolloton/git/JPC_AV/JPC_AV_videoQC/tests/command_config.yaml', "r") as f:
    command_dict = yaml.load(f)

print(f"The command_dict is {command_dict}\n")

# Function to update command_config
def gui_selection(checkbox):
    section, option = checkbox.id.split('.')  # Assuming checkbox IDs are "section.option"
    print(f"the section is {section} and the option is {option}")
    if checkbox.value:
        print("checkbox value found, changing command_dict")
        command_dict[section][option] = 'yes'
    else:
        command_dict[section][option] = 'no'

# Function to apply profile changes
def apply_profile(dict):
    with open('/Users/eddycolloton/git/JPC_AV/JPC_AV_videoQC/tests/command_config.yaml', "w") as f:
        yaml.dump(dict, f)

ui.label('outputs:')

with ui.column():  # Group checkboxes under "outputs"
    ui.checkbox('access_file')
    ui.checkbox('report')

ui.label('fixity:')  # Section header, no checkbox

# Create checkboxes and bind them to the gui_selection function
with ui.column():
    for option in ['access_file', 'report']:
        checkbox = ui.checkbox(option, value=command_dict['outputs'][option] == 'yes')
        checkbox.id = f'outputs.{option}'  # Set checkbox ID
        checkbox.bind_value(gui_selection)

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
        checkbox.bind_value(gui_selection)

print(f"the new command_dict values is {command_dict}\n")

ui.button('update yaml', on_click=lambda: apply_profile(command_dict))

ui.run()    