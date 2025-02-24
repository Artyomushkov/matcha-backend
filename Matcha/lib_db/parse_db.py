import re

def split_string(input_string):
    # Define the regular expression pattern to match everything inside single quotes
    pattern = r"'(.*?)'"
    
    # Use re.findall() to find all occurrences of the pattern
    split_values = re.findall(pattern, input_string)
    
    return split_values

def put_in_brackets(values, i):
    # Put the 12th and 14th strings into brackets
    values[11] = '{' + values[11] + '}'
    values[13] = '{' + values[13] + '}'
    values[1] = values[1] + str(i)
    
    return values

def process_line(line, i):
    # Split the line into values
    values = split_string(line)
    
    # Put the 12th and 14th strings into brackets
    # values = put_in_brackets(values, i)
    values = values[0:22] + ["{}"] + values[22:]
    
    # Join the values back into a single string
    modified_string = "('" + "','".join(values) + "'),"
    
    return modified_string

def process_file(input_file, output_file):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        i = 0
        for line in infile:
            modified_line = process_line(line, i)
            outfile.write(modified_line + '\n')
            i += 1

# Example usage
input_file = 'data_final.sql'
output_file = 'data_final2.sql'
process_file(input_file, output_file)