import re
import subprocess
import os
from datetime import datetime, timedelta

def pad(number, width):
    """Pad the number with leading zeros to ensure it has the specified width."""
    return str(number).zfill(width)

def ordinal_date(date):
    """Return the Julian date for the given date with age suffix."""
    today = datetime.now()
    age_days = (today - date).days  # Calculate the age of the date in days

    # Determine the suffix based on the age of the date
    if age_days <= 5:
        suffix = "G0"
    elif age_days <= 10:
        suffix = "GZ"
    else:
        suffix = "GY"
    
    year = date.year % 100  # Get last two digits of the year
    # Calculate the Julian date (day of the year)
    julian_date = (date - datetime(date.year, 1, 1)).days + 1
    # Format the Julian date
    od = f"{suffix}{year:02d}{pad(julian_date, 3)}"
    return od

def get_dataset(env_list):
    """Get a dataset string based on user input date."""
    while True:
        dataset = []
        user_input = input("Enter Q to quit\nPlease enter a date in the format YYYY-MM-DD just make sure it's not a bank holiday (e.g., 2023-10-01): ")
        if user_input.lower() == "q":
            return False
        try:
            selected_date = datetime.strptime(user_input, "%Y-%m-%d")
            
            # Check if the selected date is a weekend
            if selected_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                print("Error: The selected date falls on a weekend. Please choose a weekday.")
                continue
            
            julian_date = ordinal_date(selected_date)
            for env in env_list:
                dataset.append(f"PR1.T.LOG.DIARIO.SYS{env}.{julian_date}")

            return dataset
        
        except ValueError:
            print("Invalid date format. Please try again.")

def get_file_from_ftp(MOVEitUser, MOVEitPassword, dataset_name):
    MOVEitIP = "192.168.103.13"  
    MOVEitPort = "1021"          

    date = dataset_name.split(".")[5]

    local_file = '_'.join(dataset_name.replace(".","_").split("_")[4:]) + '.txt'


    script_file = "moveit_commands.txt"
    with open(script_file, 'w') as f:
        f.write("prompt\n")  
        f.write(f"get '{dataset_name}' {local_file}\n")  
        f.write("quit\n") 


    get_command = (
        f'"C:\\Program Files\\MOVEit-Freely\\ftps" -e:on '
        f'-user:{MOVEitUser} -password:{MOVEitPassword} -s:{script_file} -z {MOVEitIP} {MOVEitPort}'
    )

    try:
        
        result = subprocess.run(get_command, shell=True, check=True, text=True, capture_output=True)
        print("File retrieved successfully.")
        print("Output:", result.stdout)
        os.remove(script_file)
        return local_file, date
    
    except subprocess.CalledProcessError as e:
        print("An error occurred while executing the command.")
        print("Error:", e.stderr)
        os.remove(script_file)
        return False
    
def clean_log_file(input_path, output_path):

    pattern = re.compile(r'(\d{2}:\d{2}:\d{2}).*?\.HASP373\s+(\w+)')


    with open(input_path, 'r') as infile, open(output_path, 'w') as outfile:
        
        for line in infile:
            
            match = pattern.search(line)
            if match:
                
                new_line = match.group(1) + ' ' + match.group(2) + '\n'
                
                outfile.write(new_line)           

def filter_sort_and_save(env, input_filename, output_filename):
    env_to_idms_map = {
        "PR1": "IDMS40",
        "QA2": "IDMS32",
        "PA1": "IDMS20",
        "DE1": "IDMS10"
    }

    with open(input_filename, 'r') as file:
        lines = file.readlines()

    env_lines = []
    for line in lines:
        parts = line.strip().split()
        job_name = parts[1]
        if job_name.startswith(env) or job_name == env_to_idms_map[env]:
            env_lines.append(line.strip())

    env_lines.sort(key=lambda x: x[:8])  

    with open(output_filename, 'w') as output_file:
        for line in env_lines:
            output_file.write(line + '\n')

'''def filter_sort_and_save(env, input_filename, output_filename):
    env_to_idms_map = {
        "PR1": "IDMS40",
        "QA2": "IDMS32",
        "PA1": "IDMS20",
        "DE1": "IDMS10"
    }

    with open(input_filename, 'r') as file:
        lines = file.readlines()

    env_lines = []
    for line in lines:
        parts = line.strip().split()
        job_name = parts[2]
        if job_name.startswith(env) or job_name == env_to_idms_map[env]:
            env_lines.append(line.strip())

    env_lines.sort(key=lambda x: (x[:5], x[6:14]))

    with open(output_filename, 'w') as output_file:
        for line in env_lines:
            parts = line.split()
            job_name = parts[2]
            new_line = f"{parts[1]} {job_name}"
            output_file.write(new_line + "\n")
'''
def choose_environment():
    while True:
        print("Choose an environment:")
        print(f"1. SYSA")
        print(f"2. SYSB")
        print("3. Both")
        print("Q. Quit")

        choice = input("Enter 1, 2 or 3 to choose: ")

        if choice == '1': 
            dataset = get_dataset(["A"]) 
            return dataset

        elif choice == '2':
            dataset = get_dataset(["B"]) 
            return dataset
        elif choice == '3':
            dataset = get_dataset(["A", "B"]) 
            return dataset
        elif choice.lower() == 'q':
            return False
        else:
            print("Invalid choice. Please select 1, 2, 3 or Q.")
            
    

        