import os
import datetime
import re

from math import sqrt
from statistics import stdev

from manage_data.data_classes import Datapoint, Datacouple, Interval

# file directories
main_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENT_DIRECTORY = os.path.join(main_directory, 'input_files/referent_file')
COMPARE_DIRECTORY = os.path.join(main_directory, 'input_files/compared_files')
SAVED_COUPLES_DIRECTORY = os.path.join(main_directory, 'input_files/coupled_data_files')
DATASAVE_DIRECTORY = os.path.join(main_directory, 'output_files/coupled_data')
PARAMSAVE_DIRECTORY = os.path.join(main_directory, 'output_files/fits_data')

CUSTOM_INTERVALS_PATH = os.path.join(main_directory, 'input_files/intervals.txt')

# value with or without decimal point and units regex
RE_VALUE = r'[0-9]+\.*[0-9]*'

# detector serial number format for regex
RADONEYE_SERIAL = r'PE[0-9]{11}'
RADONEYE_DATA = r'manual|auto'
ALPHAGUARD_SERIAL = r'AG[0-9]{4}'
ALPHAE_SERIAL = r'AE[0-9]{4}'
RAD7_SERIAL = r'RAD7'


# Calls the ref_average_intervals that:
# Prepares the intervals based on the configuration
# Clears data based on the configuration
# Calls the estimate_value to average values in the intervals
def average_over_intervals(intervals, referent_data, compared_data, configuration):

    ref_av_intervals, non_empty_intervals = \
        ref_average_intervals(intervals, referent_data[0], configuration, 'referent')

    cmp_av_intervals = []

    for data in compared_data:
        av_intervals_data, non_empty_intervals_both = \
            ref_average_intervals(non_empty_intervals, data, configuration, 'compared')
        cmp_av_intervals.append(av_intervals_data)

    return ref_av_intervals, cmp_av_intervals


# Estimates the average value and uncertainty in an interval, based on configurations
# called in ref_average_intervals
# returns a Datapoint instance with datetime at the middle of the interval
def estimate_value(interval, values_in_interval, configuration, det_type):

    clearing = configuration.clear_data

    if det_type == 'referent':
        background = configuration.referent_detector_bgn
        background_unc = configuration.referent_detector_bgn_unc
        uncertainty_type = configuration.referent_value_unc
        averaging = configuration.referent_interval_type
        min_threshold = configuration.value_thresholds[0]
        max_threshold = configuration.value_thresholds[1]
        interval_len = configuration.referent_meas_duration
    else:
        background = configuration.compared_detector_bgn
        background_unc = configuration.compared_detector_bgn_unc
        uncertainty_type = configuration.compared_value_unc
        averaging = configuration.compared_interval_type
        min_threshold = configuration.value_thresholds[2]
        max_threshold = configuration.value_thresholds[3]
        interval_len = configuration.compared_meas_duration

    # Applying filters - zero filter, thresholds, jumps (intervals with sharp changes in value)
    if 'zeros' in clearing:
        raw_values = [val.value for val in values_in_interval if val.value > 0]
    else:
        raw_values = [val.value for val in values_in_interval]

    raw_average = sum(raw_values) / len(raw_values)

    if raw_average < min_threshold or raw_average > max_threshold:
        return None

    if 'jumps' in clearing and max(raw_values) - min(raw_values) > raw_average:
        return None

    # Estimates the average value and the two types of uncertainty stdev and propagation
    if averaging == 'inside':
        values_in_interval.pop()
        raw_values.pop()
        value = (sum(raw_values) / len(raw_values)) - background
        unc_squared = [val.value_unc ** 2 for val in values_in_interval]
        unc_propagation = sqrt(sum(unc_squared)) / len(raw_values)
        stdev_single = stdev(raw_values) if len(raw_values) > 1 else 0
        stdev_av = stdev_single / sqrt(len(raw_values))

    # Estimates the 'weighted' average and its standard deviation and uncertainty by propagation
    else:
        start = interval.start_time
        end = interval.end_time
        weights = [(values_in_interval[0].meas_time - start).total_seconds()/60]
        for i in range(1, len(values_in_interval)-1):
            weight = (values_in_interval[i].meas_time - values_in_interval[i-1].meas_time).total_seconds() / 60
            weights.append(weight)
        weights.append((end - values_in_interval[len(values_in_interval) - 2].meas_time).total_seconds() / 60)
        if (values_in_interval[len(values_in_interval)-1].meas_time - end).total_seconds() / 60 \
                > interval_len:
            values_in_interval[len(values_in_interval) - 1] = values_in_interval[len(values_in_interval) - 2]
        value_sum = 0
        unc_squared = 0
        for i in range(len(weights)):
            value_sum += weights[i]*values_in_interval[i].value
            unc_squared += (weights[i]*values_in_interval[i].value_unc) ** 2
        value = (value_sum / sum(weights))
        unc_propagation = sqrt(unc_squared) / sum(weights)

        stdev_sum = 0
        for i in range(len(weights)):
            stdev_sum += weights[i]*((values_in_interval[i].value - value) ** 2)
        stdev_av = sqrt(stdev_sum / ((len(weights) - 1)*sum(weights)))
        stdev_single = stdev_av * sqrt(len(weights))

        value -= background

    # Removing negative values and applying background filter
    if value < 0:
        value = 0.0

    if 'bgn' in clearing and value < 3 * background_unc:
        return None

    # Generates an object with the estimated value, its measurement time and uncertainty
    estimated_value = Datapoint(interval.meas_time, value)

    # Chooses the specified uncertainty
    if uncertainty_type == 'stdevav':
        estimated_value.value_unc = sqrt((stdev_av ** 2) + (background_unc ** 2))
    elif uncertainty_type == 'stdev':
        estimated_value.value_unc = sqrt((stdev_single ** 2) + (background_unc ** 2))
    elif uncertainty_type == 'propagation':
        estimated_value.value_unc = sqrt((unc_propagation ** 2) + (background_unc ** 2))
    elif uncertainty_type == 'max':
        estimated_value.value_unc = sqrt((max(stdev_av, unc_propagation) ** 2) + (background_unc ** 2))

    return estimated_value


# The lists of both detectors should be sorted by the property datetime which is done in the readfile function
# The data of the two detectors should have matching intervals which is done by the prepare intervals function
# It's ok if some intervals might be missing in one of the cmp data
def join_detector_couple(ref_datapoints, cmp_datapoints):
    datacouples = []
    next_data = 0

    for datapoint in ref_datapoints:
        ref_datetime = datapoint.meas_time

        for j in range(next_data, len(cmp_datapoints)):
            if ref_datetime < cmp_datapoints[j].meas_time:
                break
            if cmp_datapoints[j].meas_time == ref_datetime:
                datacouple = Datacouple(ref_datetime, datapoint.value, cmp_datapoints[j].value)
                datacouple.ref_value_unc = datapoint.value_unc
                datacouple.cmp_value_unc = cmp_datapoints[j].value_unc

                if datacouple.ratio_ref_cmp:
                    ratio_rel_uncertainty = 0.0
                    if datapoint.value_unc:
                        ratio_rel_uncertainty = (datapoint.value_unc / datapoint.value)
                    if cmp_datapoints[j].value_unc:
                        ratio_rel_uncertainty = sqrt(ratio_rel_uncertainty ** 2 +
                                                     (cmp_datapoints[j].value_unc / cmp_datapoints[j].value) ** 2)
                    datacouple.ratio_unc = datacouple.ratio_ref_cmp * ratio_rel_uncertainty

                datacouples.append(datacouple)
                next_data = j+1
                break

    return datacouples


# Prepares the intervals over which values will be averaged
# Uses configuration file for equidistant intervals or input_files/intervals.txt for custom intervals
def prepare_intervals(configuration):

    intervals = []

    if configuration.is_custom_interval:
        intervals = read_intervals()
    else:
        start_time = configuration.start_time
        while start_time < configuration.end_time:
            end_time = start_time + datetime.timedelta(minutes=configuration.interval)
            interval = Interval(start_time, end_time)
            intervals.append(interval)
            start_time = end_time

    return intervals


# reads data for each file of detector couple
def read_detector_couple_data():
    detectorcouples_data = []
    directory = SAVED_COUPLES_DIRECTORY
    for file_name in [name for name in os.listdir(directory)
                      if os.path.isfile(os.path.join(directory, name))]:
        file_path = os.path.join(directory, file_name)
        with open(file_path, 'r') as current_file:
            detector_couples = []
            lines = current_file.readlines()
            for line in lines:
                info = line.split(',')
                if len(info) == 7:
                    try:
                        datetime_value = datetime.datetime.strptime(info[0], '%m/%d/%Y %H:%M')
                        ref_value = float(info[1])
                        cmp_value = float(info[3])
                        data_couple = Datacouple(datetime_value, ref_value, cmp_value)
                        data_couple.ratio_ref_cmp = float(info[5])
                        data_couple.ref_value_unc = float(info[2])
                        data_couple.cmp_value_unc = float(info[4])
                        data_couple.ratio_unc = float(info[6])
                        detector_couples.append(data_couple)
                    except ValueError:
                        continue
            detectorcouples_data.append(detector_couples)

    return detectorcouples_data


# reads the saved_data file names and extracts the names of detector couples
def read_detector_couple_names():
    detector_couples = []
    for file_name in [name for name in os.listdir(SAVED_COUPLES_DIRECTORY)
                      if os.path.isfile(os.path.join(SAVED_COUPLES_DIRECTORY, name))]:
        name_tokens = file_name.split('_')
        if len(name_tokens) > 1:
            detector_couple = (name_tokens[0], name_tokens[1])
        else:
            detector_couple = ['unknown', 'unknown']
        detector_couples.append(detector_couple)

    return detector_couples


def read_intervals():
    intervals = []
    with open(CUSTOM_INTERVALS_PATH, 'r') as intervals_file:
        lines = intervals_file.readlines()
        for line in lines:
            tokens = line.split('-')
            if len(tokens) == 2:
                try:
                    start = datetime.datetime.strptime(tokens[0].strip(), '%m/%d/%Y %H:%M')
                    end = datetime.datetime.strptime(tokens[1].strip(), '%m/%d/%Y %H:%M')
                    interval = Interval(start, end)
                    intervals.append(interval)
                except ValueError:
                    continue
    if not intervals:
        raise Exception('No intervals were found in file intervals.txt. Check format!')
    return intervals


# reads the detector files and creates datapoints with datetime, compared value and compared value uncertainty
# datetime is between start and end if specified by the config file
def read_files(file_type, configuration):
    all_files_data = []

    if file_type == 'referent':
        directory = REFERENT_DIRECTORY
        separator = configuration.referent_file_separator
        multiplier, unc_multiplier = configuration.value_multipliers[0], configuration.value_multipliers[1]
        shift = configuration.time_shift[0]
        datetime_format = configuration.referent_file_datetime_format
        datetime_index = configuration.referent_datetime_index
        value_index = configuration.referent_value_index
        encoding = configuration.referent_file_encoding
    else:
        directory = COMPARE_DIRECTORY
        separator = configuration.compared_file_separator
        multiplier, unc_multiplier = configuration.value_multipliers[2], configuration.value_multipliers[3]
        shift = configuration.time_shift[1]
        datetime_format = configuration.compared_file_datetime_format
        datetime_index = configuration.compared_datetime_index
        value_index = configuration.compared_value_index
        encoding = configuration.compared_file_encoding

    for file_name in [name for name in os.listdir(directory) if os.path.isfile(os.path.join(directory, name))]:
        data_points = []
        file_path = os.path.join(directory, file_name)
        with open(file_path, 'r', encoding=encoding, errors='ignore') as current_file:
            lines = current_file.readlines()
            for line in lines:
                line = line.strip("\n")
                line = line.strip('\"')
                line = line.strip(separator)
                info = line.split(separator)
                if len(info) - 1 < max(datetime_index) or len(info)-1 < max(value_index):
                    continue
                date_info = info[datetime_index[0]].strip()
                if len(datetime_index) > 1:
                    for next_index in range(1, len(datetime_index)):
                        date_info += ' ' + info[datetime_index[next_index]]

                value_info = info[value_index[0]]
                value_info = value_info.replace(',', '')
                value_match = re.search(RE_VALUE, value_info)
                if not value_match:
                    continue
                num_value = value_match.group(0)
                unc_match = None
                if len(value_index) > 1:
                    uncertainty_info = info[value_index[1]]
                    uncertainty_info = uncertainty_info.replace(',', '')
                    unc_match = re.search(RE_VALUE, uncertainty_info)

                try:
                    datetime_value \
                        = datetime.datetime.strptime(date_info, datetime_format) + datetime.timedelta(hours=shift)
                    if configuration.start_time and (datetime_value < configuration.start_time):
                        continue
                    if configuration.end_time and (datetime_value > configuration.end_time):
                        continue
                    value = float(num_value)
                    value = value * multiplier
                    data_point = Datapoint(datetime_value, value)
                    if unc_match:
                        value_unc = float(unc_match.group(0))
                        data_point.value_unc = value_unc * unc_multiplier
                except ValueError:
                    continue

                data_points.append(data_point)

            data_points.sort(key=lambda x: x.meas_time)
            all_files_data.append(data_points)

    return all_files_data


def ref_average_intervals(intervals, data_list, configuration, det_type):
    datapoints = []
    non_empty_intervals = []
    next_data_index = 0
    for i in range(len(intervals)):
        start = intervals[i].start_time
        end = intervals[i].end_time
        values_in_interval = []
        for j in range(next_data_index, len(data_list)):
            if data_list[j].meas_time < start:
                continue
            elif data_list[j].meas_time >= end or j == len(data_list) - 1:
                if values_in_interval:
                    values_in_interval.append(data_list[j])
                    datapoint = estimate_value(intervals[i], values_in_interval, configuration, det_type)
                    if datapoint:
                        datapoints.append(datapoint)
                        non_empty_intervals.append(intervals[i])
                next_data_index = j
                break
            else:
                values_in_interval.append(data_list[j])

    return datapoints, non_empty_intervals


def save_datacouples_file(datacouples, detector_names, value, unit):

    file_name = f'{detector_names[0]}_{detector_names[1]}_' \
                f'{datetime.datetime.now().strftime("%y%m%d%H%M%S")}'
    file_name += '.csv'
    path = os.path.join(DATASAVE_DIRECTORY, file_name)

    if os.path.exists(path):
        raise FileExistsError

    f = open(path, "w")

    column_names = f'Interval middle, Referent {value} ({unit}), Referent {value} uncertainty ({unit}), ' \
                   f'Compared {value} ({unit}), Compared {value} uncertainty ({unit}), ' \
                   f'Referent/Compared ratio, Ratio uncertainty\n'

    f.write(column_names)

    for entry in datacouples:
        line = f'{entry.meas_time}, {entry.ref_value}, {entry.ref_value_unc}'
        line += f', {entry.cmp_value}, {entry.cmp_value_unc}'
        line += f', {entry.ratio_ref_cmp}' if entry.ratio_ref_cmp else ', -'
        line += f', {entry.ratio_unc}' if entry.ratio_unc else ', 0'
        f.write(line)
        f.write("\n")

    f.close()


def save_param_file(lines, func_type, y_axis, x_axis):
    file_name = f'{func_type}_fit_params_{y_axis}_versus_{x_axis}_' \
                f'{datetime.datetime.now().strftime("%y%m%d%H%M%S")}'
    file_name += '.csv'
    path = os.path.join(PARAMSAVE_DIRECTORY, file_name)

    with open(path, 'w') as current_file:
        current_file.writelines(lines)


def search_detector_serial(detector, detector_type):
    data_gen_match = ''
    if detector.lower() == 'alphaguard':
        reg_serial = ALPHAGUARD_SERIAL
    elif detector.lower() == 'radoneye':
        reg_serial = RADONEYE_SERIAL
        data_gen_match = RADONEYE_DATA
    elif detector.lower() == 'alphae':
        reg_serial = ALPHAE_SERIAL
    elif detector.lower() == 'rad7':
        reg_serial = RAD7_SERIAL
    else:
        reg_serial = ''

    detector_serials = []
    if reg_serial:
        detector_serials = search_serial(detector_type, reg_serial)

    if data_gen_match:
        gen_type = search_serial(detector_type, data_gen_match)
        for i in range(0, len(gen_type)):
            detector_serials[i] += gen_type[i]

    return detector_serials


def search_serial(file_type, searched_regex):

    if file_type == 'referent':
        directory = REFERENT_DIRECTORY
    else:
        directory = COMPARE_DIRECTORY

    detector_serials = []

    for file_name in [name for name in os.listdir(directory)
                      if os.path.isfile(os.path.join(directory, name))]:

        detector_serials.append('')

        serial_match = re.search(searched_regex, file_name)
        if serial_match:
            detector_serials[len(detector_serials) - 1] = serial_match.group(0)
            continue

        file_path = os.path.join(directory, file_name)
        with open(file_path, 'r') as current_file:
            lines = current_file.readlines()

            for line in lines:
                serial_match = re.search(searched_regex, line)
                if serial_match:
                    detector_serials[len(detector_serials) - 1] = serial_match.group(0)
                    break

    return detector_serials
