import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pymavlink import mavutil
from datetime import datetime
import xml.etree.ElementTree as ET

class MavlinkPlotterGUI:
    def __init__(self, master):
        self.master = master
        master.title("MAVLink Data Plotter")
        master.geometry("1000x800")
        master.grid_rowconfigure(1, weight=1)
        master.grid_columnconfigure(0, weight=1)

        # Control Panel
        self.control_frame = ttk.Frame(master, padding=10)
        self.control_frame.grid(row=0, column=0, sticky='ew', padx=10)

        for i in range(12):
            self.control_frame.grid_columnconfigure(i, weight=1)

        try:
            self.dev_icon = tk.PhotoImage(file="dev.png")
            self.dev_icon = self.dev_icon.subsample(
                max(1, self.dev_icon.width() // 50),
                max(1, self.dev_icon.height() // 50)
            )
            self.dev_label = ttk.Label(self.control_frame, image=self.dev_icon)
            self.dev_label.grid(row=0, column=0, padx=(0, 5))
            ttk.Label(self.control_frame, text="Developed by Sam", font=('Arial', 8, 'italic')).grid(row=0, column=1, sticky='w')
        except Exception as e:
            print(f"Error loading icon: {e}")

        self.load_button = ttk.Button(self.control_frame, text="Load Log", command=self.load_log)
        self.load_button.grid(row=0, column=2, padx=5, pady=5)

        self.msg_label = ttk.Label(self.control_frame, text="Message Type:")
        self.msg_label.grid(row=0, column=3, padx=5, pady=5)

        self.msg_combobox = ttk.Combobox(self.control_frame, state="readonly", width=20)
        self.msg_combobox.grid(row=0, column=4, padx=5, pady=5)
        self.msg_combobox.bind("<<ComboboxSelected>>", self.update_id_fields)

        self.id_label = ttk.Label(self.control_frame, text="Instance ID:")
        self.id_label.grid(row=0, column=5, padx=5, pady=5)

        self.id_combobox = ttk.Combobox(self.control_frame, state="readonly", width=8)
        self.id_combobox.grid(row=0, column=6, padx=5, pady=5)
        self.id_combobox.bind("<<ComboboxSelected>>", self.update_field_options)

        self.field_label = ttk.Label(self.control_frame, text="Field:")
        self.field_label.grid(row=0, column=7, padx=5, pady=5)

        self.field_combobox = ttk.Combobox(self.control_frame, state="readonly", width=15)
        self.field_combobox.grid(row=0, column=8, padx=5, pady=5)

        self.plot_button = ttk.Button(self.control_frame, text="Plot", command=self.plot_data)
        self.plot_button.grid(row=0, column=9, padx=5, pady=5)

        self.plot_all_button = ttk.Button(self.control_frame, text="Plot All", command=self.plot_all_data)
        self.plot_all_button.grid(row=0, column=10, padx=5, pady=5)

        self.export_button = ttk.Button(self.control_frame, text="Export", command=self.export_xml)
        self.export_button.grid(row=0, column=11, padx=5, pady=5)

        # Matplotlib Figure
        self.figure = plt.Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=master)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky='nsew')

        # Navigation Frame for Paging
        self.nav_frame = ttk.Frame(master)
        self.nav_frame.grid(row=3, column=0, sticky='ew', pady=5)
        self.nav_frame.grid_columnconfigure(1, weight=1)

        self.prev_button = ttk.Button(self.nav_frame, text="Previous", command=self.prev_page)
        self.prev_button.grid(row=0, column=0, padx=5)

        self.page_label = ttk.Label(self.nav_frame, text="Page 1/1")
        self.page_label.grid(row=0, column=1)

        self.next_button = ttk.Button(self.nav_frame, text="Next", command=self.next_page)
        self.next_button.grid(row=0, column=2, padx=5)

        self.prev_button.grid_remove()
        self.page_label.grid_remove()
        self.next_button.grid_remove()

        self.grid_frame = ttk.Frame(self.control_frame)
        self.grid_frame.grid(row=1, column=0, columnspan=12, pady=5)

        ttk.Label(self.grid_frame, text="Grid Layout:").pack(side='left', padx=5)

        self.rows_var = tk.StringVar(value="3")
        self.cols_var = tk.StringVar(value="3")

        ttk.Label(self.grid_frame, text="Rows:").pack(side='left', padx=5)
        self.rows_spinbox = ttk.Spinbox(
            self.grid_frame, from_=1, to=5, width=5,
            textvariable=self.rows_var, command=self.update_grid_layout)
        self.rows_spinbox.pack(side='left', padx=5)

        ttk.Label(self.grid_frame, text="Columns:").pack(side='left', padx=5)
        self.cols_spinbox = ttk.Spinbox(
            self.grid_frame, from_=1, to=5, width=5,
            textvariable=self.cols_var, command=self.update_grid_layout)
        self.cols_spinbox.pack(side='left', padx=5)

        # Plot canvas and nav frame
        self.figure = plt.Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=master)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky='nsew')

        self.nav_frame = ttk.Frame(master)
        self.nav_frame.grid(row=3, column=0, sticky='ew', pady=5)
        self.nav_frame.grid_columnconfigure(1, weight=1)

        self.prev_button = ttk.Button(self.nav_frame, text="Previous", command=self.prev_page)
        self.page_label = ttk.Label(self.nav_frame, text="Page 1/1")
        self.next_button = ttk.Button(self.nav_frame, text="Next", command=self.next_page)

        self.prev_button.grid(row=0, column=0, padx=5)
        self.page_label.grid(row=0, column=1)
        self.next_button.grid(row=0, column=2, padx=5)
        self.prev_button.grid_remove()
        self.page_label.grid_remove()
        self.next_button.grid_remove()

        # Status bar
        self.status_frame = ttk.Frame(master)
        self.status_frame.grid(row=4, column=0, sticky='sw', padx=10, pady=5)
        self.log_date_label = ttk.Label(self.status_frame, text="Log date: Not loaded")
        self.log_date_label.pack(side='left')

        self.cursor_label = ttk.Label(self.status_frame, text="")
        self.cursor_label.pack(side='right', padx=10)

        # Internal state variables
        self.log_file = None
        self.message_data = {}
        self.current_ids = []
        self.current_fields = []
        self.start_time = None
        self.export_all_mode = False

        self.all_plots_data = []
        self.current_page = 0
        self.total_pages = 0

        # Grid layout state
        self.grid_rows = 3
        self.grid_cols = 3
        self.plots_per_page = 9

    def update_grid_layout(self, *args):
        try:
            self.grid_rows = int(self.rows_var.get())
            self.grid_cols = int(self.cols_var.get())
            self.plots_per_page = self.grid_rows * self.grid_cols

            if self.all_plots_data:
                self.total_pages = (len(self.all_plots_data) + self.plots_per_page - 1) // self.plots_per_page
                self.current_page = min(self.current_page, self.total_pages - 1)
                self.plot_current_page()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for rows and columns")

    def plot_all_data(self):
        self.export_all_mode = True
        msg_type = self.msg_combobox.get()
        if not msg_type or msg_type not in self.message_data:
            return

        self.all_plots_data = []
        for msg_id in sorted(self.message_data[msg_type].keys(), key=int):
            data = self.message_data[msg_type][msg_id]
            times = data['times']
            for field in sorted(data['data'].keys()):
                values = data['data'][field]
                if len(times) == len(values):
                    self.all_plots_data.append({
                        'times': times,
                        'values': values,
                        'field': field,
                        'msg_id': msg_id
                    })

        self.total_pages = (len(self.all_plots_data) + self.plots_per_page - 1) // self.plots_per_page
        self.current_page = 0

        if self.total_pages > 1:
            self.prev_button.grid()
            self.page_label.grid()
            self.next_button.grid()
        else:
            self.prev_button.grid_remove()
            self.page_label.grid_remove()
            self.next_button.grid_remove()

        self.plot_current_page()

    def plot_current_page(self):
        self.figure.clear()
        start_idx = self.current_page * self.plots_per_page
        end_idx = min(start_idx + self.plots_per_page, len(self.all_plots_data))
        current_plots = self.all_plots_data[start_idx:end_idx]

        fig_width = max(3 * self.grid_cols, 10)
        fig_height = max(2 * self.grid_rows, 6)
        self.figure.set_size_inches(fig_width, fig_height)

        for i, plot_data in enumerate(current_plots):
            ax = self.figure.add_subplot(self.grid_rows, self.grid_cols, i + 1)
            ax.plot(plot_data['times'], plot_data['values'])
            ax.set_title(f"{plot_data['field']} (ID {plot_data['msg_id']})", fontsize=8)
            ax.set_xlabel("Time (s)", fontsize=8)
            ax.set_ylabel(plot_data['field'], fontsize=8)
            ax.tick_params(labelsize=6)
            ax.grid(True)
            ax.format_coord = lambda x, y: f'Time: {x:.2f}s, Value: {y:.2f}'

        self.figure.tight_layout()
        self.page_label.config(text=f"Page {self.current_page + 1}/{self.total_pages}")
        self.prev_button["state"] = "normal" if self.current_page > 0 else "disabled"
        self.next_button["state"] = "normal" if self.current_page < self.total_pages - 1 else "disabled"
        self.canvas.mpl_connect('motion_notify_event', self.update_cursor_position)
        self.canvas.draw()
        self.canvas.get_tk_widget().update_idletasks()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.plot_current_page()

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.plot_current_page()
            
    def update_cursor_position(self, event):
        if event.inaxes:
            x, y = event.xdata, event.ydata
            if x is not None and y is not None:
                self.cursor_label.config(text=f'Time: {x:.2f}s, Value: {y:.2f}')
        else:
            self.cursor_label.config(text="")


    def export_xml(self):
        if self.export_all_mode:
            # Export all data for current message type
            msg_type = self.msg_combobox.get()
            if not msg_type:
                messagebox.showerror("Error", "Please select a Message Type.")
                return
                
            data_for_msg = self.message_data.get(msg_type)
            if not data_for_msg:
                messagebox.showerror("Error", "No data available for selected message type.")
                return
                
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xml",
                filetypes=[("XML Files", "*.xml"), ("All Files", "*.*")],
                title="Save XML File"
            )
            if not file_path:
                return
                
            root = ET.Element("MAVLinkData")
            msg_element = ET.SubElement(root, "Message", type=msg_type)
            
            for msg_id in sorted(data_for_msg.keys(), key=int):
                id_data = data_for_msg[msg_id]
                times = id_data['times']
                fields = id_data['data']
                
                # Validate field lengths
                valid = True
                for field in fields:
                    if len(fields[field]) != len(times):
                        valid = False
                        break
                if not valid:
                    continue
                
                instance_element = ET.SubElement(msg_element, "Instance", ID=str(msg_id))
                all_fields = sorted(fields.keys())
                
                for i in range(len(times)):
                    record = ET.SubElement(instance_element, "Record")
                    ET.SubElement(record, "Time").text = str(int(times[i]))
                    for field in all_fields:
                        safe_field = field.replace(' ', '_').replace('[', '').replace(']', '')
                        ET.SubElement(record, safe_field).text = str(fields[field][i])
            
            tree = ET.ElementTree(root)
            tree.write(file_path, encoding='utf-8', xml_declaration=True)
            # messagebox.showinfo("Success", f"All data exported to:\n{file_path}")
            self.export_all_mode = False  # Reset flag
        else:
            # Original single-field export
            msg_type = self.msg_combobox.get()
            msg_id = self.id_combobox.get()
            field = self.field_combobox.get()
            
            if not all([msg_type, msg_id, field]):
                messagebox.showerror("Error", "Please select Message Type, Instance ID, and Field.")
                return
                
            data = self.message_data.get(msg_type, {}).get(msg_id)
            if not data or field not in data['data']:
                messagebox.showerror("Error", "No data available for selected parameters.")
                return
                
            times = data['times']
            values = data['data'][field]
            
            if len(times) != len(values):
                messagebox.showerror("Error", f"Data length mismatch between time and {field}.")
                return
                
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xml",
                filetypes=[("XML Files", "*.xml"), ("All Files", "*.*")],
                title="Save XML File"
            )
            if not file_path:
                return
                
            root = ET.Element("MAVLinkData")
            for time, value in zip(times, values):
                record = ET.SubElement(root, "Record")
                ET.SubElement(record, "Time").text = str(int(time))
                safe_field = field.replace(' ', '_').replace('[', '').replace(']', '')
                ET.SubElement(record, safe_field).text = str(value)
            
            tree = ET.ElementTree(root)
            tree.write(file_path, encoding='utf-8', xml_declaration=True)
            messagebox.showinfo("Success", f"Data exported to:\n{file_path}")

    def load_log(self):
        self.export_all_mode = False  # Reset export mode
        self.log_file = filedialog.askopenfilename(
            title="Select MAVLink log file",
            filetypes=(("TLOG files", "*.tlog"), ("All files", "*.*")))
        if self.log_file:
            self.message_data.clear()
            self.msg_combobox['values'] = self.get_message_types()
            if self.msg_combobox['values']:
                self.msg_combobox.current(0)
                self.update_id_fields()
                self.log_date_label.config(text="Log date: Not available")
            else:
                self.log_date_label.config(text="Log date: No valid data found")

    def plot_data(self):
        self.export_all_mode = False  # Reset export mode
        msg_type = self.msg_combobox.get()
        msg_id = self.id_combobox.get()
        field = self.field_combobox.get()
        
        if not all([msg_type, msg_id, field]):
            return
        
        data = self.message_data[msg_type][msg_id]
        times = data['times']
        values = data['data'].get(field, [])
        
        if len(times) != len(values):
            print(f"Data length mismatch: times({len(times)}) vs values({len(values)})")
            return
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(times, values)
        ax.set_xlabel("Time (seconds from start)")
        ax.set_ylabel(field)
        ax.set_title(f"{msg_type} (ID {msg_id}) - {field}")
        ax.grid(True)
        self.figure.tight_layout()
        self.canvas.draw()

    def get_message_types(self):
        mlog = mavutil.mavlink_connection(self.log_file)
        message_types = set()
        while True:
            msg = mlog.recv_match(blocking=False)
            if msg is None:
                break
            message_types.add(msg.get_type())
        return sorted(message_types)

    def update_id_fields(self, event=None):
        msg_type = self.msg_combobox.get()
        if not msg_type:
            return
        
        # Parse all messages of this type
        mlog = mavutil.mavlink_connection(self.log_file)
        ids = set()
        self.message_data[msg_type] = {}
        self.start_time = None
        
        while True:
            msg = mlog.recv_match(type=msg_type, blocking=False)
            if msg is None:
                break
            
            # Get timestamp from log
            timestamp = msg._timestamp
            if self.start_time is None:
                self.start_time = timestamp
                try:
                    dt = datetime.fromtimestamp(self.start_time)
                    self.log_date_label.config(text=f"Log date: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                except:
                    self.log_date_label.config(text="Log date: Invalid timestamp")
            
            # Get ID if exists
            msg_id = str(getattr(msg, 'id', '0'))
            if msg_id not in self.message_data[msg_type]:
                self.message_data[msg_type][msg_id] = {
                    'times': [],
                    'data': {}
                }
            
            # Store relative time
            rel_time = timestamp - self.start_time
            self.message_data[msg_type][msg_id]['times'].append(rel_time)
            
            # Store fields
            for field in msg._fieldnames:
                if field in ['time_boot_ms', 'time_usec', 'id']:
                    continue
                
                value = getattr(msg, field)
                if isinstance(value, (list, tuple)):
                    for idx, val in enumerate(value):
                        if isinstance(val, (int, float)):
                            field_name = f"{field}[{idx}]"
                            if field_name not in self.message_data[msg_type][msg_id]['data']:
                                self.message_data[msg_type][msg_id]['data'][field_name] = []
                            self.message_data[msg_type][msg_id]['data'][field_name].append(val)
                elif isinstance(value, (int, float)):
                    if field not in self.message_data[msg_type][msg_id]['data']:
                        self.message_data[msg_type][msg_id]['data'][field] = []
                    self.message_data[msg_type][msg_id]['data'][field].append(value)
            
            ids.add(msg_id)
        
        # Update ID combobox
        self.current_ids = sorted(ids, key=int)
        self.id_combobox['values'] = self.current_ids
        self.id_combobox.current(0 if self.current_ids else -1)
        self.update_field_options()

    def update_field_options(self, event=None):
        msg_type = self.msg_combobox.get()
        msg_id = self.id_combobox.get()
        
        if msg_type and msg_id and msg_id in self.message_data.get(msg_type, {}):
            fields = sorted(self.message_data[msg_type][msg_id]['data'].keys())
            self.field_combobox['values'] = fields
            self.field_combobox.current(0 if fields else -1)

    def plot_data(self):
        msg_type = self.msg_combobox.get()
        msg_id = self.id_combobox.get()
        field = self.field_combobox.get()
        
        if not all([msg_type, msg_id, field]):
            return
        
        data = self.message_data[msg_type][msg_id]
        times = data['times']
        values = data['data'].get(field, [])
        
        if len(times) != len(values):
            print(f"Data length mismatch: times({len(times)}) vs values({len(values)})")
            return
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(times, values)
        ax.set_xlabel("Time (seconds from start)")
        ax.set_ylabel(field)
        ax.set_title(f"{msg_type} (ID {msg_id}) - {field}")
        ax.grid(True)
        self.figure.tight_layout()
        self.canvas.draw()

# if __name__ == "__main__":
#     root = tk.Tk()
#     app = MavlinkPlotterGUI(root)
#     root.mainloop()

def run_plotter():
    root = tk.Tk()
    app = MavlinkPlotterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_plotter()