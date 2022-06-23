from configMock import ConfigMock
from manage_data import services

import fit_services

# The code is simply meant to read a detector file in a given interval, average over equidistant intervals
# and fit the data by exponential function
# The aim is to estimate the half-time for decrease of activity in some interval
# It uses the functionality already developed in the manage_data module
# but that's why some parameters might look unnecessary or redundant

configuration = ConfigMock('activity', 'Bq/m3', '07/22/2021 18:00', '07/22/2021 23:00',
                           60, [], [1.0, 1.0, 1.0, 1.0], [0, 100000, 0, 100000],
                           'alphae', ';', [0], [6, 7], '%Y-%m-%d %H:%M:%S', [0, 0], 'UTF16', 60,
                           'inside', 'stdev')

intervals = services.prepare_intervals(configuration)
all_raw_data = services.read_files('compared', configuration)
det_serials = services.search_detector_serial(configuration.compared_detector, 'compared')

if not det_serials:
    det_serials = [configuration.compared_detector for det in all_raw_data]

all_av_data = []
for data in all_raw_data:
    av_intervals_data, non_empty_intervals_both = \
        services.ref_average_intervals(intervals, data, configuration, 'compared')
    all_av_data.append(av_intervals_data)

unit = configuration.unit

# Do and save exponential fits
exponential_param_lines = ['Exponential fit of type a*exp(-bx) + c\n', f'Detector, a ({unit}), a uncertainty ({unit}), '
                                                           f'T - effective time for half (min),  T uncertainty (min), '
                                                           f'c ({unit}), c uncertainty ({unit}), '
                                                           f'chi-squared, degrees of freedom, p-value \n']
for i in range(0, len(all_raw_data)):
    params = fit_services.fit_exponential_decrease(all_raw_data[i], configuration.start_time,
                                                   configuration.compared_value,
                                                   configuration.unit, det_serials[i], True)
    exponential_param_lines.append(params)

fit_services.save_param_file(exponential_param_lines, 'exponential', configuration.start_time, configuration.end_time)

# Do and save linear fits
linear_param_lines = ['Linear fit ax + b\n', f'Detector, a ({unit}), a uncertainty ({unit}), '
                                                        f'T - effective time for half (min),  T uncertainty (min), '
                                                        f'c ({unit}), c uncertainty ({unit}), R-squared, '
                                                        f'chi-squared, degrees of freedom, p-value \n']
for i in range(0, len(all_raw_data)):
    params = fit_services.fit_log_linear(all_raw_data[i], configuration.start_time,
                                         configuration.compared_value,
                                         configuration.unit, det_serials[i], True)
    linear_param_lines.append(params)

fit_services.save_param_file(linear_param_lines, 'linear', configuration.start_time, configuration.end_time)
