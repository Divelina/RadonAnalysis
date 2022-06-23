import os
import matplotlib.pyplot as plt
import numpy as np

from datetime import datetime

from math import sqrt

from scipy.optimize import curve_fit
from scipy.stats import chi2

PLOTSAVE_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output_files/plots')


# A lot of plot function are left for now, so that each plot can be specific
# They can be optimized when we know what we want
# Maybe I should change to subfigures


def func_linear(x, a, b):
    return a * x + b


def func_parabolic(x, a, c):
    return a * (x ** 2) + c


def func_exponential(x, a, b):
    return a*np.exp(b*x)


# Compare two values with errorbars and fit linear
def compare_plot_fit(det_couple, value, unit, detector_couple, short_title, saving):
    # Prepare data
    filtered_data = [dc for dc in det_couple if dc.ref_value_unc and dc.cmp_value_unc]
    y = [dc.ref_value for dc in filtered_data]
    y_unc = [dc.ref_value_unc for dc in filtered_data]
    x = [dc.cmp_value for dc in filtered_data]
    x_unc = [dc.cmp_value_unc for dc in filtered_data]

    # Choose plot type
    plt.errorbar(x, y, xerr=x_unc, yerr=y_unc, color='blue', linestyle=None, fmt='.')

    # Fit - take care if errors are none
    if min(x_unc) == 0 or min(y_unc) == 0:
        popt, pcov = curve_fit(func_linear, x, y, p0=None)
    else:
        popt, pcov = curve_fit(func_linear, x, y, p0=None, sigma=y_unc, absolute_sigma=True)
    a, b = popt
    a_unc = sqrt(pcov[0][0])
    b_unc = sqrt(pcov[1][1])
    xx = np.arange(np.min(x), np.max(x))

    # Calculate R-squared and chi-squared
    residuals = []
    chi_squared = 0.0
    dof = len(y) - 2
    for i in range(0, len(y)):
        residual = y[i] - func_linear(x[i], a, b)
        residuals.append(residual)
        chi_squared += (residual/y_unc[i])**2
    p_val = chi2.sf(chi_squared, dof)
    res_squared = [v ** 2 for v in residuals]
    ss_res = sum(res_squared)
    avg_y = sum(y) / len(y)
    av_diff = [v - avg_y for v in y]
    av_diff_squared = [v ** 2 for v in av_diff]
    ss_tot = sum(av_diff_squared)
    r_squared = 1 - (ss_res / ss_tot)

    # Plot and plot settings
    plt.plot(xx, func_linear(xx, a, b), 'k--', label=f'fit: a*x + b \n'
                                                     f'a = {a:.5e} +/- {a_unc:.5e},\n b = {b:.5e} +/- {b_unc:.5e} \n'
                                                     f'r-squared = {r_squared:.3e} \n'
                                                     f'chi-squared = {chi_squared:.3e} for {dof} dof, p = {p_val:.5}')

    plt.title(f'{value.capitalize()}: ({detector_couple[0]} versus {detector_couple[1]})')
    plt.ylabel(f'{value.capitalize()}, {unit}')
    plt.xlabel(f'{value.capitalize()}, {unit}')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    if saving:
        file_name = f'{detector_couple[0]}_{detector_couple[1]}_{short_title}_{datetime.now().strftime("%y%m%d%H%M")}'
        path = os.path.join(PLOTSAVE_DIRECTORY, file_name)
        plt.savefig(path)
    else:
        plt.show()

    plt.close()

    # Return parameter info for saving
    fit_param_line = f'{detector_couple[0]}, {detector_couple[1]}, {a}, {a_unc}, {b}, {b_unc},' \
                     f'{chi_squared}, {dof}, {p_val}\n'

    return fit_param_line


# Plots two functions of time - used for raw data from two detectors
def double_time_plot(ref_data, cmp_data, detector_couple, value, unit, title, short_title, saving):
    plt.plot([dt.meas_time for dt in ref_data], [dt.value for dt in ref_data],
             color='blue', marker='.',
             label=detector_couple[0])
    plt.plot([dt.meas_time for dt in cmp_data], [dt.value for dt in cmp_data],
             color='red', marker='.',
             label=detector_couple[1])
    plt.title(title)
    plt.ylabel(f'{value.capitalize()}, {unit}')
    plt.xlabel(f'Time')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    if saving:
        file_name = f'{detector_couple[0]}_{detector_couple[1]}_{short_title}_{datetime.now().strftime("%y%m%d%H%M")}'
        path = os.path.join(PLOTSAVE_DIRECTORY, file_name)
        plt.savefig(path)
    else:
        plt.show()

    plt.close()


def double_time_unc_plot(ref_data, cmp_data, detector_couple, value, unit, title, short_title, saving):
    plt.errorbar([dt.meas_time for dt in ref_data], [dt.value for dt in ref_data],
                 yerr=[dt.value_unc for dt in ref_data], color='red',
                 label=detector_couple[0], linestyle=None, fmt='.')
    plt.errorbar([dt.meas_time for dt in cmp_data], [dt.value for dt in cmp_data],
                 yerr=[dt.value_unc for dt in cmp_data], color='blue',
                 label=detector_couple[1], linestyle=None, fmt='.')

    plt.title(title)
    plt.ylabel(f'{value.capitalize()}, {unit}')
    plt.xlabel(f'Time')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    if saving:
        file_name = f'{detector_couple[0]}_{detector_couple[1]}_{short_title}_{datetime.now().strftime("%y%m%d%H%M")}'
        path = os.path.join(PLOTSAVE_DIRECTORY, file_name)
        plt.savefig(path)
    else:
        plt.show()

    plt.close()


# Plots the ratio of two compared values as a function of one of the compared values
# Fits with an exponential function
def ratio_value_plot(det_couple, value, unit, detector_type, detector_couple, short_title, saving, fit_type):
    filtered_data = [dc for dc in det_couple if dc.ratio_ref_cmp and dc.ratio_unc]

    # Prepare data
    if detector_type == 'referent':
        x = [dp.ref_value for dp in filtered_data]
        title = f'Ratio of ref to compared {value} versus {detector_couple[0]} {value} ({unit})'
    else:
        x = [dp.cmp_value for dp in filtered_data]
        title = f'Ratio of ref to compared {value} versus {detector_couple[1]} {value} ({unit})'

    y = [dp.ratio_ref_cmp for dp in filtered_data]
    y_unc = [dp.ratio_unc for dp in filtered_data]

    # Chooses fit function
    if fit_type == 'exponential':
        func = func_exponential
        fit_equation = 'a*exp(xb)'
        a_guess = 0.9
        b_guess = 0.00003
    else:
        func = func_parabolic
        fit_equation = 'a*x^2 + b'
        a_guess = 0.00000004
        b_guess = 0.9

    plt.errorbar(x, y, yerr=y_unc, color='blue', linestyle=None, fmt='.')

    # Fit
    popt, pcov = curve_fit(func, x, y, p0=(a_guess, b_guess), sigma=y_unc)
    a, b = popt
    a_unc = sqrt(pcov[0][0])
    b_unc = sqrt(pcov[1][1])
    xx = np.arange(np.min(x), np.max(x))

    # Calculate chi_squared
    chi_squared = 0.0
    dof = len(y) - 2
    for i in range(0, len(y)):
        residual = y[i] - func(x[i], a, b)
        chi_squared += (residual / y_unc[i]) ** 2
    p_val = chi2.sf(chi_squared, dof)

    # Plot and plot settings
    plt.plot(xx, func(xx, a, b), 'k--',
             label=f'fit: {fit_equation}\n'
                   f'a = {a:.5e} +/- {a_unc:.5e},\n'
                   f'b = {b:.5e} +/- {b_unc:.5e}\n'
                   f'chi-squared = {chi_squared:.3e} for {dof} dof, p = {p_val:.7}')

    plt.title(title)
    plt.ylabel(f'Ratio ({detector_couple[0]} over {detector_couple[1]})')
    plt.xlabel(f'{value.capitalize()}, {unit}')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    if saving:
        file_name = f'{detector_couple[0]}_{detector_couple[1]}_{short_title}_{datetime.now().strftime("%y%m%d%H%M")}'
        path = os.path.join(PLOTSAVE_DIRECTORY, file_name)
        plt.savefig(path)
    else:
        plt.show()

    plt.close()

    # Return parameter info for saving
    fit_param_line = f'{detector_couple[0]}, {detector_couple[1]}, {a}, {a_unc}, {b}, {b_unc},' \
                     f'{chi_squared}, {dof}, {p_val}\n'

    return fit_param_line
