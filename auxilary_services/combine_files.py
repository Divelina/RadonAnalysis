import os

current_directory = os.path.dirname(os.path.abspath(__file__))


# The second file is appended line by one to the first
def simple_combine(first_file_name, second_file_name, new_file_name):
    first_file_path = os.path.join(current_directory, first_file_name)
    second_file_path = os.path.join(current_directory, second_file_name)
    new_file_path = os.path.join(current_directory, new_file_name)

    if os.path.exists(new_file_path):
        os.remove(new_file_path)

    with open(new_file_path, 'w') as new_file:
        with open(first_file_path, 'r', errors='ignore') as first_file:
            first_lines = first_file.readlines()
        new_file.writelines(first_lines)
        with open(second_file_path, 'r', errors='ignore') as second_file:
            second_lines = second_file.readlines()
        new_file.writelines(second_lines)

    return None


simple_combine('RAD7_first_exp.txt', 'RAD7_2nd_3rd_exp.txt', 'RAD7_all_exp.txt')
