import datetime
import re

# constants used for regex
RE_INPUT = r'input_data\s+([a-zA-Z]+)'
RE_SAVE = r'\s+([a-zA-Z])'
RE_PLOTS = r'plots\s+(.+)\#'
RE_FIT = r'ratio_fit\s+(parabolic|exponential)'
RE_VALUE = r'compared_value\s+([a-zA-Z]+)'
RE_UNIT = r'compared_value_unit\s+(.+)\#'
RE_MULTIPLIERS = r'value_multipliers\s+([0-9]+\.[0-9]+\s[0-9]+\.[0-9]+\s[0-9]+\.[0-9]+\s[0-9]+\.[0-9]+)'
RE_THRESHOLDS = r'value_thresholds\s+([0-9]+\s[0-9]+\s[0-9]+\s[0-9]+)'
RE_SHIFTS = r'time_shift_hours\s+(-?[0-9]+)\s+(-?[0-9]+)#'
RE_UNCERTAINTY = r'unc_type\s+([a-zA-Z]+)'
RE_CUSTOM = r'custom_intervals\s+([a-zA-Z])'
RE_TIME = r'datetime\s+([0-9]+/[0-9]+/[0-9]{4}\s[0-9]{2}:[0-9]{2})'
RE_INTERVAL = r'interval_min\s+([0-9]+)'
RE_MATCH_TYPE = r'interval_match\s+([a-zA-Z]+)'
RE_DURATION = r'meas_duration\s+([0-9]+)'
RE_CLEAR = r'clear_data\s+(.+)\#'
RE_DETECTOR = r'detector\s+([\S]+)'
RE_SEPARATOR = r'file_separator\s+([\S]+)'
RE_ENCODING = r'file_encoding\s+([a-zA-Z0-9]+)'
RE_DATETIME_FORMAT = r'file_datetime_format\s+(.+)\#'
RE_INDEX = r'index\s+(.+)\#'
RE_BACKGROUND = r'detector_background\s+([0-9]+)\s([0-9]+)'


class Configuration:
    def __init__(self, config_path):
        config_file = open(config_path, 'r')
        self.config_lines = config_file.read()
        config_file.close()

        self._input_data = self._set_input_data()
        self._save_files = self._set_save_options('data')
        self._plots = self._set_plots()
        self._fit = self._set_fit()
        self._save_plots = self._set_save_options('plots')

        self._compared_value = self._set_compared_value()
        self._unit = self._set_unit()

        self.compared_det_serials = []

        if self.input_data == 'separate':

            self._value_multipliers = self._set_multipliers()
            self._value_thresholds = self._set_thresholds()
            self._time_shift = self._set_shift()

            self._is_custom_interval = self._set_custom_int()
            self.start_time = self._set_time('start')
            self.end_time = self._set_time('end')
            self._interval = self._set_interval()
            self._clear_data = self._set_clear_data()

            self.referent_detector = self._set_detector('referent')
            self.compared_detector = self._set_detector('compared')
            self._referent_file_separator = self._set_separator('referent')
            self._compared_file_separator = self._set_separator('compared')
            self._referent_file_datetime_format = self._set_datetime_format('referent')
            self._referent_datetime_index = self._set_index('referent_datetime')
            self._compared_datetime_index = self._set_index('compared_datetime')
            self._referent_value_index = self._set_index('referent_value')
            self._compared_value_index = self._set_index('compared_value')
            self._compared_file_datetime_format = self._set_datetime_format('compared')
            self._referent_detector_bgn, self._referent_detector_bgn_unc = self._set_background('referent')
            self._compared_detector_bgn, self._compared_detector_bgn_unc = self._set_background('compared')
            self._referent_file_encoding = self._set_encoding('referent')
            self._compared_file_encoding = self._set_encoding('compared')
            self._referent_interval_type = self._set_interval_type('referent')
            self._compared_interval_type = self._set_interval_type('compared')
            self._referent_meas_duration = self._set_duration('referent')
            self._compared_meas_duration = self._set_duration('compared')
            self._referent_value_unc = self._set_uncertainty('referent')
            self._compared_value_unc = self._set_uncertainty('compared')

# Most properties are private and are meant to be set only through the config file

    @property
    def input_data(self):
        return self._input_data

    @property
    def save_files(self):
        return self._save_files

    @property
    def plots(self):
        return self._plots

    @property
    def fit(self):
        return self._fit

    @property
    def save_plots(self):
        return self._save_plots

    @property
    def compared_value(self):
        return self._compared_value

    @property
    def unit(self):
        return self._unit

    @property
    def value_multipliers(self):
        return self._value_multipliers

    @property
    def value_thresholds(self):
        return self._value_thresholds

    @property
    def time_shift(self):
        return self._time_shift

    @property
    def is_custom_interval(self):
        return self._is_custom_interval

    @property
    def interval(self):
        return self._interval

    @property
    def clear_data(self):
        return self._clear_data

    @property
    def referent_file_separator(self):
        return self._referent_file_separator

    @property
    def referent_file_encoding(self):
        return self._referent_file_encoding

    @property
    def referent_file_datetime_format(self):
        return self._referent_file_datetime_format

    @property
    def compared_file_datetime_format(self):
        return self._compared_file_datetime_format

    @property
    def referent_datetime_index(self):
        return self._referent_datetime_index

    @property
    def referent_value_index(self):
        return self._referent_value_index

    @property
    def referent_detector_bgn(self):
        return self._referent_detector_bgn

    @property
    def referent_detector_bgn_unc(self):
        return self._referent_detector_bgn_unc

    @property
    def referent_interval_type(self):
        return self._referent_interval_type

    @property
    def referent_meas_duration(self):
        return self._referent_meas_duration

    @property
    def referent_value_unc(self):
        return self._referent_value_unc

    @property
    def compared_file_separator(self):
        return self._compared_file_separator

    @property
    def compared_file_encoding(self):
        return self._compared_file_encoding

    @property
    def compared_datetime_index(self):
        return self._compared_datetime_index

    @property
    def compared_value_index(self):
        return self._compared_value_index

    @property
    def compared_detector_bgn(self):
        return self._compared_detector_bgn

    @property
    def compared_detector_bgn_unc(self):
        return self._compared_detector_bgn_unc

    @property
    def compared_interval_type(self):
        return self._compared_interval_type

    @property
    def compared_meas_duration(self):
        return self._compared_meas_duration

    @property
    def compared_value_unc(self):
        return self._compared_value_unc

    def _set_input_data(self):
        input_match = re.search(RE_INPUT, self.config_lines)
        if input_match and input_match.group(1) == 'coupled':
            return 'coupled'

        return 'separate'

    def _set_save_options(self, saved_type):
        save_options = 'save_' + saved_type + RE_SAVE
        save_match = re.search(save_options, self.config_lines)
        if save_match and save_match.group(1) == 'y':
            return True

        return False

    def _set_plots(self):
        plot_match = re.search(RE_PLOTS, self.config_lines)
        if plot_match:
            return plot_match.group(1).split()

        return None

    def _set_fit(self):
        fit_match = re.search(RE_FIT, self.config_lines)
        if fit_match:
            return fit_match.group(1).strip()

        return 'parabolic'

    def _set_compared_value(self):
        compared_match = re.search(RE_VALUE, self.config_lines)
        if not compared_match:
            return 'activity'
        return compared_match.group(1)

    def _set_unit(self):
        unit_match = re.search(RE_UNIT, self.config_lines)
        if not unit_match:
            return 'relative unit'
        return unit_match.group(1).strip()

    def _set_multipliers(self):
        multipliers_match = re.search(RE_MULTIPLIERS, self.config_lines)
        if not multipliers_match:
            return [1.0, 1.0, 1.0, 1.0]
        return [float(mult) for mult in multipliers_match.group(1).split()]

    def _set_thresholds(self):
        thresholds_match = re.search(RE_THRESHOLDS, self.config_lines)
        if not thresholds_match:
            return [0, 1000000000, 0, 1000000000]
        return [int(thr) for thr in thresholds_match.group(1).split()]

    def _set_shift(self):
        shift_match = re.search(RE_SHIFTS, self.config_lines)
        error_message = f'Shift time should be positive or negative integer'
        if shift_match:
            try:
                shifts = [int(shift_match.group(1)), int(shift_match.group(2))]
                return shifts
            except ValueError:
                raise ValueError(error_message)
        return [0,0]

    def _set_custom_int(self):
        custom_int_match = re.search(RE_CUSTOM, self.config_lines)
        if custom_int_match and custom_int_match.group(1) == 'y':
            return True
        return False

    def _set_time(self, label):
        datetime_string = label + '_' + RE_TIME
        time_match = re.search(datetime_string, self.config_lines)
        if not time_match:
            return None
        return datetime.datetime.strptime(time_match.group(1), "%m/%d/%Y %H:%M")

    def _set_interval(self):
        interval_match = re.search(RE_INTERVAL, self.config_lines)
        if not interval_match:
            raise ValueError("Interval line is missing or interval is not a number")
        return float(interval_match.group(1))

    def _set_interval_type(self, detector_role):
        interval_type_re = detector_role + '_' + RE_MATCH_TYPE
        interval_type_match = re.search(interval_type_re, self.config_lines)
        if not interval_type_match:
            raise ValueError("Interval matching type line is missing or interval is not a number")
        int_type = interval_type_match.group(1)
        if int_type not in ['weighted', 'inside']:
            raise ValueError("Wrong interval matching type - should be weighted or inside")
        return int_type

    def _set_clear_data(self):
        clear_data_match = re.search(RE_CLEAR, self.config_lines)
        if clear_data_match:
            test = clear_data_match.group(1).split()
            return clear_data_match.group(1).split()
        return []

    def _set_detector(self, detector_role):
        det_string = detector_role + '_' + RE_DETECTOR
        det_match = re.search(det_string, self.config_lines)
        if not det_match:
            return 'unknown'
        return det_match.group(1)

    def _set_separator(self, detector_role):
        det_sep_string = detector_role + '_' + RE_SEPARATOR
        sep_match = re.search(det_sep_string, self.config_lines)
        if not sep_match:
            raise ValueError(f"{detector_role.capitalize()} file separator line is missing or not in required format")
        separator = sep_match.group(1)

        if separator == 'tab':
            return '\t'
        elif separator == 'space':
            return ''
        else:
            return separator

    def _set_encoding(self, detector_role):
        encoding_string = detector_role + '_' + RE_ENCODING
        encoding_match = re.search(encoding_string, self.config_lines)
        if not encoding_match:
            return 'cp1252'
        return encoding_match.group(1)

    def _set_datetime_format(self, detector_role):
        format_string = detector_role + '_' + RE_DATETIME_FORMAT
        format_match = re.search(format_string, self.config_lines)
        if not format_match:
            raise ValueError(f"{detector_role.capitalize()} datetime format must be specified as in python")
        return format_match.group(1).strip()

    def _set_index(self, index_type):
        index_string = index_type + '_' + RE_INDEX
        index_match = re.search(index_string, self.config_lines)
        error_message = f'{index_type.capitalize()} is missing or not in required format'
        if not index_match:
            raise ValueError(error_message)
        index_values = index_match.group(1).split()
        try:
            indexes = [int(index) for index in index_values]
            return indexes
        except ValueError:
            raise ValueError(error_message)

    def _set_background(self, detector_role):
        background = detector_role + '_' + RE_BACKGROUND
        bgn_match = re.search(background, self.config_lines)
        (bgn, bgn_unc) = (0.0, 0.0)
        if bgn_match:
            (bgn, bgn_unc) = float(bgn_match.group(1)), float(bgn_match.group(2))
        return bgn, bgn_unc

    def _set_duration(self, detector_role):
        duration = detector_role + '_' + RE_DURATION
        duration_match = re.search(duration, self.config_lines)
        if duration_match:
            return int(duration_match.group(1))
        return 10

    def _set_uncertainty(self, detector_role):
        uncertainty_re = detector_role + '_' + RE_UNCERTAINTY
        unc_match = re.search(uncertainty_re, self.config_lines)
        if not unc_match or unc_match.group(1) not in ['stdevav', 'propagation', 'max', 'stdev']:
            return 'stdevav'
        return unc_match.group(1)

