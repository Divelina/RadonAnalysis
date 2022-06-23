import logging
from datetime import datetime

import plot_services
from manage_data.services import save_param_file


# All plots are either saved or shown,depending on the configuration.save_plots True = saved, False = shown
def manage_plots(configuration, referent_raw_data, compared_raw_data,
                 referent_avrg_data, compared_avrg_data, detector_couples_data):
    if configuration.plots:
        detector_couple_names = configuration.compared_det_serials
        value = configuration.compared_value
        unit = configuration.unit
        save_plots = configuration.save_plots

        logging.basicConfig(filename='output_files/plots/exception.log', level=logging.ERROR)

        if 'original' in configuration.plots:
            title = 'Raw no background corrected'
            short_title = 'raw'
            for i in range(0, len(compared_raw_data)):
                plot_services.double_time_plot(referent_raw_data, compared_raw_data[i], detector_couple_names[i],
                                               value, unit, title, short_title, save_plots)

        if 'averaged_time' in configuration.plots:
            title = 'Averaged over intervals'
            short_title = 'averaged'
            for i in range(0, len(compared_avrg_data)):
                plot_services.double_time_unc_plot(referent_avrg_data, compared_avrg_data[i], detector_couple_names[i],
                                                   value, unit, title, short_title, save_plots)

        if 'value_value' in configuration.plots:
            short_title = f'{value}'
            param_file_lines = [f'Referent {value} as a function of compared {value}\n',
                                'Linear fit of type ax+ b\n',
                                f'Referent detector, Compared detector, a, a uncertainty, '
                                f'b ({unit}), b uncertainty ({unit}), '
                                f'chi-squared, degrees of freedom, p-value \n']
            for i in range(0, len(detector_couples_data)):
                try:
                    param_line = plot_services.compare_plot_fit(detector_couples_data[i], value, unit, detector_couple_names[i],
                                                   short_title, save_plots)
                    param_file_lines.append(param_line)
                except TypeError as e:
                    logging.error(msg=f'{datetime.now()} Plot skipped {short_title} {detector_couple_names[i][1]}'
                                      f'Check coupled data - points might be insufficient',
                                  exc_info=True)
                    continue
            save_param_file(param_file_lines, 'linear', 'referent', 'compared')

        if 'ratio_ref_activity' in configuration.plots:
            short_title = 'ratio_referent'
            param_file_lines = [f'Ratio of ref to compared {value} as a function of ref {value}\n',
                                f'{configuration.fit} fit \n',
                                f'Referent detector, Compared detector, a, a uncertainty, '
                                f'b, b uncertainty, '
                                f'chi-squared, degrees of freedom, p-value \n']
            for i in range(0, len(detector_couples_data)):
                try:
                    param_line = plot_services.ratio_value_plot(detector_couples_data[i], value, unit, 'referent',
                                                                detector_couple_names[i], short_title, save_plots,
                                                                configuration.fit)
                    param_file_lines.append(param_line)
                except TypeError as e:
                    logging.error(msg=f'{datetime.now()} Plot skipped {short_title} {detector_couple_names[i][1]}'
                                      f'Check coupled data - points might be insufficient',
                                  exc_info=True)
                    continue

            save_param_file(param_file_lines, configuration.fit, 'ratio', 'referent')

        if 'ratio_cmp_activity' in configuration.plots:
            short_title = 'ratio_compared'
            param_file_lines = [f'Ratio of ref to compared {value} as a function of compared {value}\n',
                                f'{configuration.fit} fit \n',
                                f'Referent detector, Compared detector, a, a uncertainty, '
                                f'b, b uncertainty, '
                                f'chi-squared, degrees of freedom, p-value \n']
            for i in range(0, len(detector_couples_data)):
                try:
                    param_line = plot_services.ratio_value_plot(detector_couples_data[i], value, unit, 'compared',
                                                                detector_couple_names[i], short_title, save_plots,
                                                                configuration.fit)
                    param_file_lines.append(param_line)
                except TypeError as e:
                    logging.error(msg=f'{datetime.now()} Plot skipped {short_title} {detector_couple_names[i][1]}'
                                      f'Check coupled data - points might be insufficient',
                                  exc_info=True)
                    continue

            save_param_file(param_file_lines, configuration.fit, 'ratio', 'compared')
