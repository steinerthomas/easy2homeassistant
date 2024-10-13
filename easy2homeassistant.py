from enum import Enum

import argparse
import tempfile
import zipfile
import os

import xml.etree.ElementTree as ET
import yaml
import logging
import sys
import colorlog

# logging
log_colors = {
    'DEBUG': 'light_black',
    'INFO': 'black',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'bold_red',
}

logger_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
console_handler = colorlog.StreamHandler(sys.stdout)
console_formatter = colorlog.ColoredFormatter(
    f"%(log_color)s{logger_format}",
    log_colors=log_colors
)
console_handler.setFormatter(console_formatter)

log_file_path = "easy2homeassistant.log"
file_handler = logging.FileHandler(log_file_path)
file_formatter = logging.Formatter(logger_format)
file_handler.setFormatter(file_formatter)

logger = logging.getLogger(__name__)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# yaml serialization
class StringValue(str):
    pass

def quoted_str_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')

yaml.add_representer(StringValue, quoted_str_representer)

def object_to_dict(obj):
    if isinstance(obj, list):
        return [object_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: object_to_dict(value) for key, value in obj.items() if value is not None}
    elif hasattr(obj, '__dict__'):
        return {key: object_to_dict(value) for key, value in obj.__dict__.items() if value is not None}
    elif isinstance(obj, str):
        return StringValue(obj)
    else:
        return obj

def generic_representer(dumper, data):
    return dumper.represent_dict(object_to_dict(data))

yaml.add_multi_representer(object, generic_representer)

# data structures
class EntityKind(Enum):
    UNDEFINED = 0
    LIGHT = 1
    COVER = 2

    def __str__(self):
        return f"{self.name} ({self.value})"

class Light:
    def __init__(self, name, address=None, brightness_address=None, state_address=None, brightness_state_address=None):
        self.name = name
        self.address = address
        self.brightness_address = brightness_address
        self.state_address = state_address
        self.brightness_state_address = brightness_state_address

class Cover:
    def __init__(self, name, address=None, move_long_address=None, stop_address=None, position_address=None, angle_address=None, position_state_address=None, angle_state_address=None):
        self.name = name
        self.move_long_address = move_long_address
        self.stop_address = stop_address
        self.position_address = position_address
        self.angle_address = angle_address
        self.position_state_address = position_state_address
        self.angle_state_address = angle_state_address

class Entities:
    def __init__(self, light=None, cover=None):
        self.light = light if light is not None else []
        self.cover = cover if cover is not None else []
    
    def addEntity(self, entity):
        if type(entity) is Light:
            self.light.append(entity)
        elif type(entity) is Cover:
            self.cover.append(entity)
        else:
            logger.critical(f"Invalid entity '{entity}'")

# xml parsing
class XMLParser:
    ADDRESS_MAP = {
        # light
        'On/Off': 'address',
        'Dim value': 'brightness_address',
        'On/Off status': 'state_address',
        'Dim value status': 'brightness_state_address',
        # cover
        'Up/Down': 'move_long_address',
        'Step/Stop': 'stop_address',
        'Position control': 'position_address',
        'Slat angle control': 'angle_address',
        'Position control status': 'position_state_address',
        'Slat angle control status': 'angle_state_address',
    }

    def __init__(self):
        self.entities = Entities()
        self.entity = None # currently parsed entity
        self.address_attribute_name = None # currently parsed address
    
    def addEntity(self):
        if self.entity is not None:
            self.entities.addEntity(self.entity)
            self.entity = None
        else:
            logger.error('Empty entity occurred!')

    def parse_group_addresses(self, groupAddresses):
        lowestAddress = float('inf')
        for config in groupAddresses.findall('config'):
            address = config.get('name')
            logger.debug(f"Parse group address '{address}'")
            try:
                lowestAddress = min(lowestAddress, int(address))
            except ValueError:
                logger.warning(f"Skip invalid groupAddress '{address}'")
        
        if lowestAddress != float('inf'):
            setattr(self.entity, self.address_attribute_name, lowestAddress)
            logger.info(f"'{self.entity.name}': Set attribute '{self.address_attribute_name}' to '{lowestAddress}'")
        else:
            logger.error('No group address found!')

    def parse_datapoints(self, datapoints):
        for config in datapoints.findall('config'):
            for property in config.findall('property'):
                if property.get('key') == 'name':
                    datapoint_name = property.get('value')
                    if datapoint_name in self.ADDRESS_MAP:
                        # set attribute name and search for group addresses
                        self.address_attribute_name = self.ADDRESS_MAP[datapoint_name]
                        if hasattr(self.entity, self.address_attribute_name):
                            self.parse_config(config)
                        else:
                            logger.error(f"'{self.entity.name}' has no attribute '{self.address_attribute_name}'!")
                    else:
                        logger.info(f"'{self.entity.name}': Skip unmapped datapoint '{datapoint_name}'")

    def parse_config(self, config):
        if config is None:
            logger.error('Unexpected empty config!')
            return

        name = config.get('name')
        if name == 'Context' or name == 'Parameters':
            logger.debug(f"Skip '{name}'")
            return
        elif name == 'datapoints':
            self.parse_datapoints(config)
            return
        elif name == 'groupAddresses':
            self.parse_group_addresses(config)
            return
        elif name == 'FunctionalBlocks' or name.lstrip("-").isdigit():
            logger.debug(f"Handle known config '{name}'")
        else:
            logger.warning(f"Skip unhandled config '{name}'")
            return

        self.parse_configs(config)

    def parse_configs(self, configs):
        for config in configs.findall('config'):
            self.parse_config(config)

    def parse_channel(self, channel):
        name = ''
        kind = EntityKind.UNDEFINED

        for property in channel.findall('property'):
            if property.get('key') == 'Name':
                name = property.get('value')
                if name == '':
                    logger.debug(f"Skip unnamed channel: {channel.get('name')}")
            elif property.get('key') == 'Icon':
                if property.get('value') == 'icon-shutter':
                    kind = EntityKind.COVER
                else:
                    kind = EntityKind.LIGHT

        if name != '' and kind != EntityKind.UNDEFINED:
            # create entity and search for attributes
            if kind is EntityKind.COVER:
                self.entity = Cover(name)
            elif kind is EntityKind.LIGHT:
                self.entity = Light(name)

            logger.info(f"Found entity '{name}' of kind {kind}")
            for config in channel.findall('config'):
                self.parse_config(config)
            self.addEntity()
            

    def parse_channel_xml(self, channelsXml): 
        logger.info(f"Parsing xml file '{channelsXml}'")

        tree = ET.parse(channelsXml) 
        root = tree.getroot() 

        for channel in root.findall('config'):
            self.parse_channel(channel)

        return self.entities


def main():
    arg_parser = argparse.ArgumentParser(description="Process an easy project and export data to YAML.")
    arg_parser.add_argument('-i', '--input', required=True, help='Path to the input easy project (txa) file.')
    arg_parser.add_argument('-o', '--output', required=True, help='Path to the output HomeAssistant yaml file.')
    arg_parser.add_argument('-l', '--loglevel', default='INFO', help='Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).')
    
    args = arg_parser.parse_args()

    logger.setLevel(args.loglevel.upper())

    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"Extracting files to temporary directory '{temp_dir}'")
        
        with zipfile.ZipFile(args.input, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        channels_xml_file = os.path.join(temp_dir, 'configuration', 'Channels.xml')
        if not os.path.exists(channels_xml_file):
            logger.error(f"{channels_xml_file} not found in the extracted files.")
            return

        parser = XMLParser()
        entities = parser.parse_channel_xml(channels_xml_file)

        yaml_configuration = args.output
        logger.info(f"Exporting entities to '{yaml_configuration}'")
        with open(yaml_configuration, 'w', encoding='utf-8') as yaml_file:
            yaml_file.write(yaml.dump(entities, sort_keys=False, allow_unicode=True))

        logger.info(f"Data exported to '{yaml_configuration}' successfully.")
      
if __name__ == "__main__":
    main() 