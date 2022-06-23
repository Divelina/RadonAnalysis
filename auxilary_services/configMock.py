from datetime import datetime


class ConfigMock:
    def __init__(self, value, unit, start, end, interval, clear, multipliers, thresholds,
                 detector, separator, datetime_index, value_index, datetime_format, bgn, file_encoding, meas_duration,
                 average_type, unc_type):
        self.compared_value = value
        self.unit = unit
        self.start_time = datetime.strptime(start, '%m/%d/%Y %H:%M')
        self.end_time = datetime.strptime(end, '%m/%d/%Y %H:%M')
        self.interval = interval
        self.clear_data = clear
        self.value_multipliers = [float(mult) for mult in multipliers]
        self.value_thresholds = [int(thr) for thr in thresholds]
        self.is_custom_interval = False

        self.compared_detector = detector
        self.compared_file_separator = separator
        self.compared_datetime_index = datetime_index
        self.compared_value_index = value_index
        self.compared_file_datetime_format = datetime_format
        self.compared_detector_bgn, self.compared_detector_bgn_unc = bgn
        self.compared_file_encoding = file_encoding
        self.compared_meas_duration = meas_duration
        self.compared_interval_type = average_type
        self.compared_value_unc = unc_type
