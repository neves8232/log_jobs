import tkinter as tk
from tkinter import ttk, messagebox
from utils import *
import os
from datetime import datetime, timedelta
import calendar

class CalendarWidget(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.selected_date = None
        self._create_calendar()

    def _create_calendar(self):
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=5)

        self.current_date = datetime.now()
        self.year = self.current_date.year
        self.month = self.current_date.month

        ttk.Button(control_frame, text="<", width=5,
                  command=self._previous_month).pack(side="left")
        self.header_label = ttk.Label(control_frame, text="")
        self.header_label.pack(side="left", expand=True)
        ttk.Button(control_frame, text=">", width=5,
                  command=self._next_month).pack(side="right")

        main_calendar_frame = ttk.Frame(self)
        main_calendar_frame.pack(fill="both", expand=True)

        for i in range(7):
            main_calendar_frame.grid_columnconfigure(i, weight=1)

        for i, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            ttk.Label(main_calendar_frame, text=day, anchor="center").grid(
                row=0, column=i, sticky="nsew", padx=1, pady=1)

        self.calendar_frame = main_calendar_frame
        self._update_calendar()

    def _update_calendar(self):
        self.header_label.config(text=f"{calendar.month_name[self.month]} {self.year}")

        for widget in self.calendar_frame.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.destroy()

        cal = calendar.monthcalendar(self.year, self.month)

        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                if day != 0:
                    date = datetime(self.year, self.month, day)
                    is_weekend = col_idx >= 5
                    is_future = date > datetime.now()
                    
                    btn = ttk.Button(self.calendar_frame, text=str(day),
                                   command=lambda d=date: self._select_date(d))
                    
                    if is_weekend or is_future:
                        btn.state(['disabled'])
                        style = ttk.Style()
                        style.configure('Disabled.TButton', foreground='gray')
                        btn.configure(style='Disabled.TButton')
                    
                    btn.grid(row=row_idx + 1, column=col_idx, padx=1, pady=1, sticky="nsew")

    def _previous_month(self):
        self.month -= 1
        if self.month < 1:
            self.month = 12
            self.year -= 1
        self._update_calendar()

    def _next_month(self):
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self._update_calendar()

    def _select_date(self, date):
        self.selected_date = date
        self.event_generate("<<DateSelected>>")

    def get_date(self):
        return self.selected_date

class LogJobsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Log Jobs Processor")
        self.root.geometry("500x500")
        
        self.sysa_env = ["PR1", "QA2"]
        self.sysb_env = ["PA1", "DE1"]
        self.user_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.system_var = tk.StringVar(value="both")
        self.selected_date = None
        
        self.create_widgets()
        
    def create_widgets(self):
        input_frame = ttk.LabelFrame(self.root, text="Login Details", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(input_frame, text="User SYSA:").grid(row=0, column=0, sticky="w")
        ttk.Entry(input_frame, textvariable=self.user_var).grid(row=0, column=1, padx=5)
        
        ttk.Label(input_frame, text="Password SYSA:").grid(row=1, column=0, sticky="w")
        ttk.Entry(input_frame, textvariable=self.password_var, show="*").grid(row=1, column=1, padx=5)

        system_frame = ttk.LabelFrame(self.root, text="System Selection", padding=10)
        system_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Radiobutton(system_frame, text="SYSA", value="sysa",
                       variable=self.system_var).pack(side="left", padx=10)
        ttk.Radiobutton(system_frame, text="SYSB", value="sysb",
                       variable=self.system_var).pack(side="left", padx=10)
        ttk.Radiobutton(system_frame, text="Both", value="both",
                       variable=self.system_var).pack(side="left", padx=10)
        
        calendar_frame = ttk.LabelFrame(self.root, text="Select Date", padding=10)
        calendar_frame.pack(fill="x", padx=10, pady=5)
        
        self.cal = CalendarWidget(calendar_frame)
        self.cal.pack(pady=10)
        
        ttk.Button(self.root, text="Process Files", 
                  command=self.process_files).pack(pady=10)

    def get_datasets(self):
        if not self.selected_date:
            return []
            
        julian_date = ordinal_date(self.selected_date)
        datasets = []
        
        system_choice = self.system_var.get()
        if system_choice in ["sysa", "both"]:
            datasets.append(f"PR1.T.LOG.DIARIO.SYSA.{julian_date}")
        if system_choice in ["sysb", "both"]:
            datasets.append(f"PR1.T.LOG.DIARIO.SYSB.{julian_date}")
            
        return datasets

    def process_files(self):
        self.selected_date = self.cal.get_date()
        if not self.selected_date:
            messagebox.showwarning("Warning", "Please select a date first")
            return
            
        user = self.user_var.get()
        password = self.password_var.get()
        
        if not user or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
            
        try:
            datasets = self.get_datasets()
            for dataset in datasets:
                output_file, date = get_file_from_ftp(user, password, dataset)
                
                if output_file:
                    cleaned_file = output_file.split(".")[0] + "_cleaned.txt"
                    clean_log_file(output_file, cleaned_file)
                    
                    if "sysa" in dataset.lower():
                        for env in self.sysa_env:
                            output_filename = date[2:] + '_' + env + '.txt'
                            output_path = rf"Data\{output_filename}"
                            filtered_sorted_lines = filter_sort_and_save(env, cleaned_file, output_path)
                    
                    elif "sysb" in dataset.lower():
                        for env in self.sysb_env:
                            output_filename = date[2:] + '_' + env + '.txt'
                            output_path = rf"Data\{output_filename}"
                            filtered_sorted_lines = filter_sort_and_save(env, cleaned_file, output_path)
                    
                    else:
                        messagebox.showerror("Error", "Error occurred, report to GMN")
                        return
                        
                    os.remove(cleaned_file)
                    os.remove(output_file)
                    
                else:
                    messagebox.showerror("Error", "ERROR, check if user and password are correct")
                    return
                    
            messagebox.showinfo("Success", "Processing completed successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}") 