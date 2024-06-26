import datetime
import re


def extract_time_string(time_str):
    # Use regular expression to find time string
    match = re.search(r"(\d{1,2}:\d{1,2}:\d{1,2})", time_str)
    if match:
        return match.group(1)
    else:
        return None


def replace_special_characters(time_str):
    # Define a regular expression pattern to match special characters
    pattern = r"[^a-zA-Z0-9\s:]"  # Matches any character that is not alphanumeric, whitespace, or colon

    # Replace special characters with a colon
    cleaned_time_str = re.sub(pattern, ":", time_str)

    return cleaned_time_str


def convert_time_format(time_str, output_format="%H:%M:%S"):
    # Extract the time string from input

    time_str = replace_special_characters(time_str)

    extracted_time_str = extract_time_string(time_str)

    if extracted_time_str:
        # Determine if the time is positive or negative
        is_negative = False
        if extracted_time_str.startswith("-"):
            is_negative = True
            extracted_time_str = extracted_time_str[1:]
        elif extracted_time_str.startswith("+"):
            extracted_time_str = extracted_time_str[1:]

        # Split the time string into its components
        time_parts = extracted_time_str.split(":")

        # Fill missing components with zeros
        while len(time_parts) < 3:
            time_parts.append("0")

        # Convert components to integers
        hours, minutes, seconds = map(int, time_parts)

        # Create a timedelta object
        time_delta = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)

        # Format the timedelta object using the desired format
        formatted_time = (datetime.datetime.min + time_delta).time()

        return formatted_time.strftime(output_format)
    else:
        return None


# Test cases
time_strs = ["(hello) -04:23.2 (hello)", "12:45:23", "-03:23:44", "-3:2.23","-02:09:02","-02;07:50","-02:05:15"]

for time_str in time_strs:

    formatted_time = convert_time_format(time_str)
    print(f"Original: {time_str}, Formatted: {formatted_time}")
