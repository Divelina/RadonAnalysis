import os
import numpy as np
import matplotlib.pyplot as plt

from datetime import datetime
from math import sqrt
from scipy.optimize import curve_fit
from scipy.stats import chi2

FITSAVE_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fit_files')


def func_exponential(x, a, b, c):
    return a*np.exp(b*x) + c


def func_linear(x, a, b):
    return a * x + b


def fit_exponential_decrease(datapoints, start_time, value, unit, detector, has_uncertainty):

    # Prepare data
    x = [(dp.meas_time - start_time).total_seconds()/60 for dp in datapoints]

    y = [dp.value for dp in datapoints]
    y_unc = [dp.value_unc for dp in datapoints]

    title = f'{detector}'
    plt.errorbar(x, y, yerr=y_unc, color='blue', linestyle=None, fmt='.')

    # Chooses function parameters initial guess
    a_guess = datapoints[0].value
    b_guess = -0.01
    c_guess = datapoints[len(datapoints) - 1].value

    # Fit
    if has_uncertainty:
        popt, pcov = curve_fit(func_exponential, x, y, p0=(a_guess, b_guess, c_guess), sigma=y_unc)
    else:
        popt, pcov = curve_fit(func_exponential, x, y, p0=(a_guess, b_guess, c_guess))

    a, b, c = popt
    t_half = -np.log(2)/b
    a_unc = sqrt(pcov[0][0])
    b_unc = sqrt(pcov[1][1])
    c_unc = sqrt(pcov[2][2])
    t_half_unc = t_half*b_unc/(-b)
    xx = np.arange(np.min(x), np.max(x))
    label = f'fit: a*exp(-ln(2)*x/T_eff)+c\n' \
            f'a = {a:.5e} +/- {a_unc:.5e},\n'\
            f'T_eff = {t_half:.5e} +/- {t_half_unc:.5e}\n'\
            f'c = {c:.5e} +/- {c_unc:.5e}\n'
    param_line = ''

    # Calculate chi_squared
    if has_uncertainty:
        chi_squared = 0.0
        dof = len(y) - 2
        for i in range(0, len(y)):
            residual = y[i] - func_exponential(x[i], a, b, c)
            chi_squared += (residual / y_unc[i]) ** 2
        p_val = chi2.sf(chi_squared, dof)
        label += f'chi-squared = {chi_squared:.3e} for {dof} dof, p = {p_val:.7}'
        param_line = f'{chi_squared}, {dof}, {p_val}\n'

    # Plot and plot settings
    plt.plot(xx, func_exponential(xx, a, b, c), 'k--', label=label)

    plt.title(title)
    plt.ylabel(f'{value.capitalize()}, {unit}')
    plt.xlabel('Time since start, min')
    plt.legend()
    plt.tight_layout()

    file_name = f'{detector}_exponential_decrease_{datetime.now().strftime("%y%m%d%H%M%S")}'
    path = os.path.join(FITSAVE_DIRECTORY, file_name)
    plt.savefig(path)

    plt.close()

    # Return parameter info for saving
    fit_param_line = f'{detector}, {a}, {a_unc}, {t_half}, {t_half_unc}, {c}, {c_unc}, {param_line}\n'

    return fit_param_line


def fit_log_linear(datapoints, start_time, value, unit, detector, has_uncertainty):

    # Prepare data
    end_plateau = datapoints.pop(len(datapoints) - 1)
    raw_values = [dp for dp in datapoints if dp.value > end_plateau.value]
    x = [(dp.meas_time - start_time).total_seconds() / 60 for dp in raw_values]
    y = [np.log(dp.value) for dp in raw_values]
    y_unc = [sqrt(dp.value_unc**2 + end_plateau.value_unc**2)/(dp.value - end_plateau.value) for dp in raw_values]

    title = f'{detector}'
    plt.errorbar(x, y, yerr=y_unc, color='blue', linestyle=None, fmt='.')

    # Chooses function parameters initial guess
    a_guess = np.log(datapoints[0].value - end_plateau.value)
    b_guess = -0.01

    # Fit
    if has_uncertainty:
        popt, pcov = curve_fit(func_linear, x, y, p0=(a_guess, b_guess), sigma=y_unc)
    else:
        popt, pcov = curve_fit(func_linear, x, y, p0=(a_guess, b_guess))

    a, b = popt
    t_half = -np.log(2)/a
    a_unc = sqrt(pcov[0][0])
    t_half_unc = t_half*a_unc/(-a)

    # Calculate R-squared and chi-squared
    residuals = []
    dof = len(y) - 2
    for i in range(0, len(y)):
        residual = y[i] - func_linear(x[i], a, b)
        residuals.append(residual)
    res_squared = [v ** 2 for v in residuals]
    ss_res = sum(res_squared)
    avg_y = sum(y) / len(y)
    av_diff = [v - avg_y for v in y]
    av_diff_squared = [v ** 2 for v in av_diff]
    ss_tot = sum(av_diff_squared)
    r_squared = 1 - (ss_res / ss_tot)

    xx = np.arange(np.min(x), np.max(x))
    label = f'fit: a*x + b, T_eff = ln(2)/a\n' \
            f'a = {a:.5e} +/- {a_unc:.5e},\n'\
            f'T_eff = {t_half:.5e} +/- {t_half_unc:.5e}\n'\
            f'r-squared = {r_squared:.3e}\n'
    param_line = ''

    # Calculate chi_squared
    if has_uncertainty:
        chi_squared = 0.0
        dof = len(y) - 2
        for i in range(0, len(y)):
            chi_squared += (residuals[i] / y_unc[i]) ** 2
        p_val = chi2.sf(chi_squared, dof)
        label += f'chi-squared = {chi_squared:.3e} for {dof} dof, p = {p_val:.7}'
        param_line = f'{chi_squared}, {dof}, {p_val}\n'

    # Plot and plot settings
    plt.plot(xx, func_linear(xx, a, b), 'k--', label=label)

    plt.title(title)
    plt.ylabel(f'Ln({value.capitalize()})')
    plt.xlabel('Time since start, min')
    plt.legend()
    plt.tight_layout()

    file_name = f'{detector}_linear_{datetime.now().strftime("%y%m%d%H%M%S")}'
    path = os.path.join(FITSAVE_DIRECTORY, file_name)
    plt.savefig(path)

    plt.close()

    # Return parameter info for saving
    fit_param_line = f'{detector}, {a}, {a_unc}, {t_half}, {t_half_unc}, {r_squared}, {param_line}\n'

    return fit_param_line


def save_param_file(lines, func_type, start_time, end_time):
    file_name = f'{func_type}_fit_params_{start_time.strftime("%y%m%d%H%M")}_{end_time.strftime("%y%m%d%H%M")}'
    file_name += '.csv'
    path = os.path.join(FITSAVE_DIRECTORY, file_name)

    with open(path, 'w') as current_file:
        current_file.writelines(lines)
