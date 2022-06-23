import os

from config import Configuration
from manage_data.data_manager import manage_data
from plot_manager import manage_plots

# Reads the config file and makes a configuration object
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.txt')
configuration = Configuration(CONFIG_PATH)

referent_raw_data, compared_raw_data, referent_avrg_data, compared_avrg_data, detector_couples_data = \
    manage_data(configuration)

manage_plots(configuration, referent_raw_data, compared_raw_data, referent_avrg_data,
             compared_avrg_data, detector_couples_data)
