from manage_data import services


def get_data_separate_files(configuration):
    intervals = services.prepare_intervals(configuration)

    # For custom intervals start and end time are set as the start and end the union of all intervals
    # In read_files data is saved only for datetime between the start and end time
    if configuration.is_custom_interval:
        configuration.start_time = intervals[0].start_time
        configuration.end_time = intervals[len(intervals) - 1].end_time

    # A list of data for each file as a list of data points in each line is returned
    # Each data point is in format object with datetime, compared value and value uncertainty if provided
    referent_data = services.read_files('referent', configuration)
    if len(referent_data[0]) == 0:
        raise Exception('Check referent detector configuration - indexes, separator or encoding')

    # if not set in configuration start and end time are set as start and end of the referent_data
    if not configuration.start_time:
        configuration.start_time = referent_data[0][0].meas_time
    if not configuration.end_time:
        configuration.end_time = referent_data[0][len(referent_data) - 1].meas_time

    compared_data = services.read_files('compared', configuration)
    if len(compared_data[0]) == 0:
        raise Exception('Check compared detector configuration - indexes, separator or encoding')

    # Attempts to find the detectors' serials in the files and includes them in the configuration object
    # Currently works for AlphaGuard, RadonEYE and AlphaE
    referent_serials = services.search_detector_serial(configuration.referent_detector, 'referent')
    if referent_serials:
        configuration.referent_detector += referent_serials[0]
    compared_det_serials = services.search_detector_serial(configuration.compared_detector, 'compared')
    if compared_det_serials:
        configuration.compared_det_serials = \
            [(configuration.referent_detector, cmp)
             if cmp
             else (configuration.referent_detector, configuration.compared_detector)
             for cmp in compared_det_serials]

    # Averages over the intervals
    # Returns a list of datapoints for the referent and each compared file
    ref_data_av_intervals, cmp_data_av_intervals = \
        services.average_over_intervals(intervals, referent_data, compared_data, configuration)

    # In each interval makes an object for each couple - time, referent and compared detector values, ratio,
    # uncertainties
    # Returns a list of datacouples for each ref-cmp detector couple
    det_couples = []
    for cmp_data in cmp_data_av_intervals:
        det_couple = services.join_detector_couple(ref_data_av_intervals, cmp_data)
        det_couples.append(det_couple)

    # Files cannot be overwritten, so an error might arise if the same detector file is written at the same time
    if configuration.save_files:
        for i in range(0, len(det_couples)):
            services.save_datacouples_file(det_couples[i], configuration.compared_det_serials[i],
                                           configuration.compared_value, configuration.unit)

    return referent_data[0], compared_data, ref_data_av_intervals, cmp_data_av_intervals, det_couples


def manage_data(configuration):
    # If referent and compared data are in separate files, all data is read and filtered and returned for plotting
    if configuration.input_data == 'separate':
        return get_data_separate_files(configuration)

    # If pre-saved files for detector couples is used, only the coupled data is read and returned for plotting
    elif configuration.input_data == 'coupled':
        if 'original' in configuration.plots:
            configuration.plots.remove('original')
        if 'averaged_time' in configuration.plots:
            configuration.plots.remove('averaged_time')

        configuration.compared_det_serials = services.read_detector_couple_names()
        detector_couples = services.read_detector_couple_data()

        if detector_couples:
            return [], [], [], [], detector_couples
        else:
            raise Exception('Check coupled_data_files - no data or lines are in wrong format')
    else:
        raise ValueError("Wrong input type - should be separate or coupled")
