#!/user/bin/python

class Statuses():
    OK = 0 
    WARNING = 1
    ALERT = 2
    CRITICAL = 3
    UNDEFINED = 4

    codes = {OK:'OK',
             WARNING:'WARNING',
             ALERT:'ALERT',
             CRITICAL:'CRITICAL',
             UNDEFINED:'UNDEFINED'}
        
class Devices():
    STATUS_LED_RED = 'STATUS_LED_RED'
    STATUS_LED_YELLOW = 'STATUS_LED_YELLOW'
    STATUS_LED_GREEN = 'STATUS_LED_GREEN'
    HEARTBEAT = 'HEARTBEAT'
    HEATER_1 = 'HEATER_1'
    HEATER_2 = 'HEATER_2'
    FAN_DISPLAY = 'FAN_DISPLAY'
    FAN_SUMP = 'FAN_SUMP'
    WAVEMAKER_FR = 'WAVEMAKER_FR'
    WAVEMAKER_FL = 'WAVEMAKER_FL'
    WAVEMAKER_RR = 'WAVEMAKER_RR'
    WAVEMAKER_RL = 'WAVEMAKER_RL'
    DISPLAY_LIGHTING_MOONLIGHT = 'DISPLAY_LIGHTING_MOONLIGHT'
    DISPLAY_LIGHTING_PRIMARY = 'DISPLAY_LIGHTING_PRIMARY'
    DISPLAY_LIGHTING_SECONDARY = 'DISPLAY_LIGHTING_SECONDARY'
    DISPLAY_LIGHTING_RED = 'DISPLAY_LIGHTING_RED'
    SUMP_LIGHTING = 'SUMP_LIGHTING'
    FAN_LIGHTING_DISPLAY = 'FAN_LIGHTING_DISPLAY'
    FAN_LIGHTING_SUMP = 'FAN_LIGHTING_SUMP'
    PROTEIN_SKIMMER = 'PROTEIN_SKIMMER'
    RETURN_PUMP = 'RETURN_PUMP'

    friendlyNames = {STATUS_LED_RED: 'Red Status LED',
                     STATUS_LED_YELLOW: 'Yellow Status LED',
                     STATUS_LED_GREEN: 'Green Status LED',
                     HEARTBEAT: 'Heartbeat',
                     HEATER_1: 'Heater 1',
                     HEATER_2: 'Heater 2',
                     FAN_DISPLAY: 'Display Fan',
                     FAN_SUMP: 'Refugium Fan',
                     WAVEMAKER_FR: 'Wavemaker (front right)',
                     WAVEMAKER_FL: 'Wavemaker (front left)',
                     WAVEMAKER_RR: 'Wavemaker (rear right)',
                     WAVEMAKER_RL: 'Wavemaker (rear left)',
                     DISPLAY_LIGHTING_MOONLIGHT: 'Moonlight',
                     DISPLAY_LIGHTING_PRIMARY: 'Display Lights (primary)',
                     DISPLAY_LIGHTING_SECONDARY: 'Display Lights (secondary)',
                     DISPLAY_LIGHTING_RED: 'Night Viewing Lights',
                     FAN_LIGHTING_DISPLAY: 'Display Lighting Fans',
                     FAN_LIGHTING_SUMP: 'Refugium Lighting Fans',
                     SUMP_LIGHTING: 'Refugium Lights',
                     PROTEIN_SKIMMER: 'Protein Skimmer',
                     RETURN_PUMP: 'Return Pump'}

class MessageTypes():
    CAPABILITIES_REQUEST = 'CAPABILITIES_REQUEST'
    CAPABILITIES_RESPONSE = 'CAPABILITIES_RESPONSE'
    DEVICE_OUTPUT = 'DEVICE_OUTPUT'
    DEVICE_OUTPUT_RESPONSE = 'DEVICE_OUTPUT_RESPONSE'
    DEVICE_STATUSES_REQUEST = 'DEVICE_STATUSES_REQUEST'
    DEVICE_STATUSES_RESPONSE = 'DEVICE_STATUSES_RESPONSE'
    EXCEPTION = 'EXCEPTION'
    HEARTBEAT = 'HEARTBEAT'
    INDICATE_STATUS = 'INDICATE_STATUS'
    LIST_WORKERS = 'LIST_WORKERS'
    PROGRAM_REQUEST = 'PROGRAM_REQUEST'
    PROGRAM_RESPONSE = 'PROGRAM_RESPONSE'
    REBOOT_REQUEST = 'REBOOT_REQUEST'
    SAFE_MODE = 'SAFE_MODE'
    SENSOR_REQUEST = 'SENSOR_REQUEST'
    SENSOR_RESPONSE = 'SENSOR_RESPONSE'
    STATUS_REQUEST = 'STATUS_REQUEST'
    STATUS_RESPONSE = 'STATUS_RESPONSE'
    SENSOR_READINGS_REQUEST = 'SENSOR_READINGS_REQUEST'
    SENSOR_READINGS_RESPONSE = 'SENSOR_READINGS_RESPONSE'
    TERMINATE = 'TERMINATE'
    WEB_STATUS_REQUEST = 'WEB_STATUS_REQUEST'
    
class MessageCodes():
    CODE = 'CODE'
    CALLER = 'CALLER'
    DEVICE = 'DEVICE'
    DEVICE_STATUSES = 'DEVICE_STATUSES'
    FRIENDLY_NAME = 'FRIENDLY_NAME'
    FRIENDLY_VALUE = 'FRIENDLY_VALUE'
    INFORMATION = 'INFORMATION'
    IP_ADDRESS = 'IP_ADDRESS'
    MAX_AGE = 'MAX_AGE'
    MESSAGE = 'MESSAGE'
    PROGRAMS = 'PROGRAMS'
    RESPONSE_QUEUE = 'RESPONSE_QUEUE'
    SENSOR = 'SENSOR'
    SENSOR_READINGS = 'SENSOR_READINGS'
    STATUS = 'STATUS'
    STATUS_CODE = 'STATUS_CODE'
    TIME = 'TIME'
    TIMEOUT = 'TIMEOUT'
    USERNAME = 'USERNAME'
    VALUE = 'VALUE'
    WORKER = 'WORKER'
    NAME = 'NAME'
    
class Sensors():
    DISPLAY_TEMP = 'DISPLAY_TEMP'
    SUMP_TEMP = 'SUMP_TEMP'
    DISPLAY_LIGHTING_TEMP = 'DISPLAY_LIGHTING_TEMP'
    SUMP_LIGHTING_TEMP = 'SUMP_LIGHTING_TEMP'
    AMBIENT_TEMP = 'AMBIENT_TEMP'
    AMBIENT_HUMIDITY = 'AMBIENT_HUMIDITY'
    DISK_SPACE = 'DISK_SPACE'
    AVAILABLE_MEMORY = 'AVAILABLE_MEMORY'
    CPU_TEMP = 'CPU_TEMP'

    friendlyNames = {DISPLAY_TEMP:"Display Temp",
                     SUMP_TEMP:"Refugium Temp",
                     DISPLAY_LIGHTING_TEMP:"Display Lighting Temp",
                     SUMP_LIGHTING_TEMP:"Refugium Lighting Temp",
                     AMBIENT_TEMP:"Ambient Temp",
                     AMBIENT_HUMIDITY:"Ambient Humidity",
                     DISK_SPACE:"Disk Space",
                     AVAILABLE_MEMORY:"Available Memory",
                     CPU_TEMP:"CPU Temp"}

class DebugLevels():
    NONE = 0
    SCREEN = 1
    DB = 2
    ALL = 3
	
class EventLevels():
    DEBUG = 0
    AUDIT = 1
    INFORMATION = 2
    WARNING = 3
    ALERT = 4
    EXCEPTION = 5
	
