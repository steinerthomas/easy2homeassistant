# easy2homeassistant [![codecov](https://codecov.io/github/steinerthomas/easy2homeassistant/graph/badge.svg)](https://codecov.io/github/steinerthomas/easy2homeassistant)
This python script parses a KNX easy configuration and converts it to a [HomeAssistant KNX Integration](https://www.home-assistant.io/integrations/knx) yaml configuration.

HomeAssistant [covers](https://www.home-assistant.io/integrations/knx/#cover), [lights](https://www.home-assistant.io/integrations/knx/#light), (temperature) [sensors](https://www.home-assistant.io/integrations/knx/#sensor), [climate](https://www.home-assistant.io/integrations/knx/#climate) and [weather](https://www.home-assistant.io/integrations/knx/#weather) are supported.

**Next steps / TODOs:**

- [ ] Improve entity kind parsing (do not use icons?)
- [ ] Handle Timer addresses for lights?
- [ ] Switches ("inputs") in general, e.g. "Central off"

## Prerequisites
Use pre-built binary or setup following software/packages on your environment:
- Python >= 3.9 and PATH variable set
- Python requirements: `pip3 install -r requirements.txt`
- HomeAssistant setup and KNX integration installed
- connection to Hager TJA670/TJA470 domovea Basic Server/Expert Server configured

## Usage
`python easy2homeassistant.py -i <project-name>.txa -o <output-filename>.yaml`

`easy2homeassistant.exe -i <project-name>.txa -o <output-filename>.yaml`

### Parameters
| Flag | Name       | Description                        | Examples                                                        |
| ---- | ---------- | ---------------------------------- | --------------------------------------------------------------- |
| -i   | --input    | KNX easy installation export (txa) | easy-project.txa                                                |
| -o   | --output   | HomeAssistant KNX config (yaml)    | knx.yaml                                                        |
| -l   | --loglevel | Logging level                      | defaults to INFO, levels: DEBUG, INFO, WARNING, ERROR, CRITICAL |

## Export easy project
easy2homeassistant uses the easy instatallation export (txa). Channels which should be available for HomeAssistant, must have a name and the flag "Export to domovea" set.

1. Open your local domovea installation in your browser
2. Go to easytool > DETAIL
3. Export > Save installation

### Group addresses
KNX easy automatically assigns group addresses in a proprietary order. In the installation document (pdf) they are are represented as 3-level and in the installation export as 1-level (decimal) group addresses.

#### Sensors - "inputs"
Addresses: 24/4/* (>= 50176)

Also used for status variables

#### Actors - "outputs"
Addresses: 2/4/* (>= 5120)

Alternative addresses: 6/0/* (redefinition, maybe for groups)

Link to sensor: 24/4/*

The lowest group address (2/4/*) is used for the HomeAssistant configuration.

### Mappings
A list of currently supported variables parsed from the easy installation export.

#### Cover: Shutter/Blind
| easy installation export name (all languages) | HomeAssistant variable |
| --------------------------------------------- | ---------------------- |
| Up/Down                                       | move_long_address      |
| Step/Stop                                     | stop_address           |
| Stop                                          | -                      |
| Position control                              | position_address       |
| Slat angle control                            | angle_address          |
| Automatism deactivation                       | -                      |
| Position control status                       | position_state_address |
| Slat angle control status                     | angle_state_address    |
| Top position                                  | -                      |
| Bottom position                               | -                      |
| Automatism deactivation status                | -                      |

#### Light (dimmable)
| easy installation export name (all languages) | HomeAssistant variable   |
| --------------------------------------------- | ------------------------ |
| On/Off                                        | address                  |
| Timer                                         | -                        |
| Dim up/down                                   | -                        |
| Dim value                                     | brightness_address       |
| Automatism deactivation                       | -                        |
| Automatism deactivation status                | -                        |
| On/Off status                                 | state_address            |
| Dim value status                              | brightness_state_address |

#### Temperature Sensors
| easy installation export name (all languages) | HomeAssistant variable |
| --------------------------------------------- | ---------------------- |
| Indoor temperature                            | state_address          |

#### Climate: Temperature controller
| easy installation export name (all languages) | HomeAssistant variable           |
| --------------------------------------------- | -------------------------------- |
| Window                                        | -                                |
| Room temperature                              | target_temperature_state_address |
| Mode status                                   | operation_mode_state_address     |
| Priority                                      | -                                |
| Mode for automatism                           | -                                |
| Setpoint shift                                | setpoint_shift_address           |
| Mode                                          | operation_mode_address           |
| Automatism deactivation                       | -                                |
| Position valve                                | -                                |
| Outdoor temperature                           | -                                |
| Automatism deactivation status                | -                                |
| Indoor temperature                            | -                                |
| Setpoint shift status                         | setpoint_shift_state_address     |
| Scene                                         | -                                |
| Priority status                               | -                                |
| Heat/Cool                                     | heat_cool_address                |
| On/Off                                        | on_off_address                   |
| Combined setpoints heat status                | -                                |
| Heat/Cool status                              | heat_cool_state_address          |
| Combined setpoints cool status                | -                                |
| Energy alarm status                           | -                                |
| Combined setpoints cool                       | -                                |
| Combined setpoints heat                       | -                                |
| Floor temperature                             | -                                |
| Indoor temperature                            | temperature_address              |

The `Indoor temperature` is used from the [Temperature Sensors](#Temperature-Sensors)

#### Weather station
| easy installation export name (all languages) | HomeAssistant variable      |
| --------------------------------------------- | --------------------------- |
| Luminosity                                    | - (address_brightness_*)    |
| Wind alarm 1                                  | address_wind_alarm          |
| Wind alarm 2                                  | - (address_wind_alarm list) |
| Wind alarm 3                                  | - (address_wind_alarm list) |
| Frost alarm                                   | address_frost_alarm         |
| Rain alarm                                    | address_rain_alarm          |
| Day/Night                                     | address_day_night           |
| Wind speed                                    | address_wind_speed          |
| Outdoor temperature                           | address_temperature         |

### Configure HomeAssistant
Include generated HomeAssistant configuration to your HomeAssistant installation. Now all entities should show up in the Overview Dashboard. Create your own Dashboards to group your entities.

#### Example generated knx.yaml
```yaml
cover:
- name: "Kitchen blinds"
  move_long_address: 5122 # 2/4/2 - Up/Down
  stop_address: 5124 # 2/4/5 - Step/Stop
  position_address: 5124 # 2/4/4 - Position control
  angle_address: 5121 # 2/4/1 - Slat angle control
  position_state_address: 50179 # 24/4/3 - Position control status
  angle_state_address: 50177 # 24/4/1 - Slat angle control status
  #travelling_time_down: 120 # not parsed
  #travelling_time_up: 120 # not parsed
# ...
light:
- name: "Living room light dimmable"
  address: 5220 # 2/4/100 - On/Off
  brightness_address: 5222 # 2/4/102 - Dim value (optional)
  state_address: 50262 # 24/4/86 - On/Off status
  brightness_state_address: 50261 # 24/4/85 - Dim value status (optional)
# ...
sensor:
- name: "Bathroom"
  state_address: 50376 # 24/4/200 - Indoor temperature
  type: "temperature"
  state_class: "measurement"
- name: "Office temperature"
  state_address: 50789 # Indoor temperature
  type: "temperature"
  state_class: "measurement"
# ...
climate:
- name: "Office temperature controller"
  temperature_address: 50789 # Indoor temperature (from sensor)
  target_temperature_state_address: 50548 # Room temperature
  setpoint_shift_address: 5418 # Setpoint shift
  setpoint_shift_state_address: 50544 # Setpoint shift status
  operation_mode_address: 5417 # Mode
  operation_mode_state_address: 50547 # Mode Status
  heat_cool_address: 5419 # Heat/Cool
  heat_cool_state_address: 50543 # Heat/Cool status
  on_off_address: 50578 # On/Off
# ...
weather:
- name: "Weather"
  address_temperature: 61440 # Outdoor temperature
  #address_brightness_south: 61442 # Luminosity - not parsed/implemented
  #address_brightness_west: 61442 # Luminosity - not parsed/implemented
  #address_brightness_east: 61442 # Luminosity - not parsed/implemented
  #address_brightness_north: 61442 # Luminosity - not parsed/implemented
  address_wind_speed: 61441 # Wind speed
  address_rain_alarm: 61451 # Rain alarm
  address_frost_alarm: 61452 # Frost alarm
  address_wind_alarm: 61448 # Wind alarm 1
  #- 61448 # Wind alarm 1 - could be a list, not implemented
  #- 61449 # Wind alarm 2 - not parsed/implemented
  #- 61450 # Wind alarm 3 - not parsed/implemented
  address_day_night: 61443 # Day/Night
```

#### configuration.yaml
```yaml
knx: !include knx.yaml
```
