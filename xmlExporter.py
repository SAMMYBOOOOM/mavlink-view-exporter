import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pymavlink import mavutil
import xml.etree.ElementTree as ET
import os
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class XmlExporterGUI:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, master=None):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.master = master if master else tk.Toplevel()
            self.master.title("XML Exporter")
            self.master.geometry("600x600")
            self.master.protocol("WM_DELETE_WINDOW", self._on_close)
            
            self.log_file = None
            self.message_data = {}
            self.selected_fields = set()
            
            self.create_widgets()
            self.load_log()

    def _on_close(self):
        XmlExporterGUI._instance = None
        self.master.destroy()

    def create_widgets(self):
        main_frame = ttk.Frame(self.master, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Developer info
        dev_frame = ttk.Frame(main_frame)
        dev_frame.pack(fill=tk.X, pady=(0, 10))
        
        try:
            self.dev_icon = tk.PhotoImage(file="dev.png")
            self.dev_icon = self.dev_icon.subsample(
                max(1, self.dev_icon.width() // 50),
                max(1, self.dev_icon.height() // 50)
            )
            dev_label = ttk.Label(dev_frame, image=self.dev_icon)
            dev_label.pack(side='left', padx=(0, 5))
            ttk.Label(dev_frame, text="Developed by Sam", font=('Arial', 8, 'italic')).pack(side='left')
        except Exception as e:
            print(f"Error loading icon: {e}")

        # Split into left (tree) and right (selected fields) panels
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left panel with TreeView
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=2)

        # Create TreeView
        self.tree = ttk.Treeview(left_frame, selectmode='none')
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # Add scrollbar to TreeView
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Right panel with selected fields
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)

        ttk.Label(right_frame, text="Selected Fields:").pack(pady=(0, 10))
        
        # Selected fields listbox
        self.selected_listbox = tk.Listbox(right_frame, selectmode=tk.EXTENDED)
        self.selected_listbox.pack(fill=tk.BOTH, expand=True)

        # Buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        self.export_btn = ttk.Button(
            btn_frame, 
            text="Export XML", 
            command=self.export_xml,
            state=tk.DISABLED
        )
        self.export_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame, 
            text="Reupload Log", 
            command=self.upload_new_log
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Clear Selection",
            command=self.clear_selection
        ).pack(side=tk.LEFT, padx=5)

        # New buttons
        ttk.Button(
            btn_frame,
            text="Preview",
            command=self.show_preview
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Export Favorite",
            command=self.export_favorite
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Import Favorite",
            command=self.import_favorite
        ).pack(side=tk.LEFT, padx=5)

        self.tree.tag_configure('checked', image=self.create_checkmark())
        self.tree.tag_configure('unchecked', image=self.create_empty_checkmark())
        
        self.tree.bind('<Button-1>', self.on_tree_click)

    def create_checkmark(self):
        checkbox = tk.PhotoImage(width=16, height=16)
        checkbox.put(('black',), to=(3, 7, 12, 8))
        checkbox.put(('black',), to=(3, 8, 12, 9))
        checkbox.put(('black',), to=(3, 9, 12, 10))
        checkbox.put(('black',), to=(7, 3, 8, 7))
        return checkbox

    def create_empty_checkmark(self):
        checkbox = tk.PhotoImage(width=16, height=16)
        checkbox.put(('gray',), to=(3, 3, 12, 12))
        return checkbox

    def on_tree_click(self, event):
        item = self.tree.identify('item', event.x, event.y)
        if not item:
            return

        # Get the full path to this item
        field_node = item
        instance_node = self.tree.parent(field_node)
        msg_type_node = self.tree.parent(instance_node)
        
        if not msg_type_node:  # Invalid structure
            return

        msg_type = self.tree.item(msg_type_node)['text']
        instance_id = self.tree.item(instance_node)['text']
        field = self.tree.item(field_node)['text']
        full_path = f"{msg_type}/{instance_id}/{field}"

        if full_path in self.selected_fields:
            self.selected_fields.remove(full_path)
            self.tree.item(field_node, tags=('unchecked',))
        else:
            self.selected_fields.add(full_path)
            self.tree.item(field_node, tags=('checked',))

        self.update_selected_listbox()
        self.export_btn['state'] = tk.NORMAL if self.selected_fields else tk.DISABLED

    def update_selected_listbox(self):
        self.selected_listbox.delete(0, tk.END)
        for field in sorted(self.selected_fields):
            self.selected_listbox.insert(tk.END, field)

    def clear_selection(self):
        self.selected_fields.clear()
        for item in self.tree.get_children():
            for msg_type in self.tree.get_children(item):
                for field in self.tree.get_children(msg_type):
                    self.tree.item(field, tags=('unchecked',))
        self.update_selected_listbox()
        self.export_btn['state'] = tk.DISABLED

    def load_log(self):
        self.log_file = filedialog.askopenfilename(
            title="Select MAVLink log file",
            filetypes=(("TLOG files", "*.tlog"), ("All files", "*.*"))
        )
        if self.log_file:
            self.parse_log_file()
            self.populate_tree()

    def upload_new_log(self):
        new_file = filedialog.askopenfilename(
            title="Select New MAVLink log file",
            filetypes=(("TLOG files", "*.tlog"), ("All files", "*.*"))
        )
        if new_file:
            self.log_file = new_file
            self.parse_log_file()
            self.populate_tree()
            messagebox.showinfo("Info", "New log file loaded successfully")

    def parse_log_file(self):
        self.message_data.clear()
        mlog = mavutil.mavlink_connection(self.log_file)
        start_time = None
        
        while True:
            msg = mlog.recv_match(blocking=False)
            if msg is None:
                break
            
            msg_type = msg.get_type()
            if msg_type not in self.message_data:
                self.message_data[msg_type] = {}
            
            timestamp = msg._timestamp
            if start_time is None:
                start_time = timestamp
            
            msg_id = str(getattr(msg, 'id', '0'))
            if msg_id not in self.message_data[msg_type]:
                self.message_data[msg_type][msg_id] = {
                    'times': [],
                    'data': {}
                }
            
            rel_time = timestamp - start_time
            self.message_data[msg_type][msg_id]['times'].append(rel_time)
            
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

    def populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        
        for msg_type in sorted(self.message_data.keys()):
            msg_type_node = self.tree.insert('', 'end', text=msg_type)
            
            for instance_id, data in sorted(self.message_data[msg_type].items(), key=lambda x: int(x[0])):
                instance_node = self.tree.insert(msg_type_node, 'end', text=instance_id)
                
                for field in sorted(data['data'].keys()):
                    self.tree.insert(instance_node, 'end', text=field, tags=('unchecked',))

        # Validate selected fields against current data
        valid_paths = set()
        for msg_type_node in self.tree.get_children():
            msg_type = self.tree.item(msg_type_node)['text']
            for instance_node in self.tree.get_children(msg_type_node):
                instance_id = self.tree.item(instance_node)['text']
                for field_node in self.tree.get_children(instance_node):
                    field = self.tree.item(field_node)['text']
                    valid_paths.add(f"{msg_type}/{instance_id}/{field}")

        # Update selected fields and checkboxes
        self.selected_fields = {path for path in self.selected_fields if path in valid_paths}
        for path in self.selected_fields:
            msg_type, instance_id, field = path.split('/')
            for msg_type_node in self.tree.get_children():
                if self.tree.item(msg_type_node)['text'] == msg_type:
                    for instance_node in self.tree.get_children(msg_type_node):
                        if self.tree.item(instance_node)['text'] == instance_id:
                            for field_node in self.tree.get_children(instance_node):
                                if self.tree.item(field_node)['text'] == field:
                                    self.tree.item(field_node, tags=('checked',))
                                    break
                            break
                    break
        
        self.update_selected_listbox()
        self.export_btn['state'] = tk.NORMAL if self.selected_fields else tk.DISABLED

    def export_xml(self):
        if not self.selected_fields:
            messagebox.showerror("Error", "Please select at least one field")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xml",
            filetypes=[("XML Files", "*.xml"), ("All Files", "*.*")],
            title="Save XML File"
        )
        if not file_path:
            return
        
        root = ET.Element("MAVLinkData")
        field_data = {}
        min_length = float('inf')
        
        for path in self.selected_fields:
            msg_type, instance_id, field = path.split('/')
            data = self.message_data[msg_type][instance_id]
            times = data['times']
            values = data['data'][field]
            field_data[field] = values
            min_length = min(min_length, len(times))
        
        for i in range(min_length):
            record = ET.SubElement(root, "Record")
            ET.SubElement(record, "Time").text = f"{int(data['times'][i])}"
            for field, values in field_data.items():
                safe_field = field.replace(' ', '_').replace('[', '').replace(']', '')
                ET.SubElement(record, safe_field).text = str(values[i])
        
        tree = ET.ElementTree(root)
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
        messagebox.showinfo("Success", f"XML exported to:\n{file_path}")

    def show_preview(self):
        if not self.selected_fields:
            messagebox.showwarning("No Selection", "Please select fields to preview.")
            return

        # Create preview window
        preview_win = tk.Toplevel(self.master)
        preview_win.title("Data Preview")
        preview_win.geometry("1000x800")
        
        # Configure grid layout
        preview_win.grid_rowconfigure(1, weight=1)
        preview_win.grid_columnconfigure(0, weight=1)

        # Navigation Frame
        nav_frame = ttk.Frame(preview_win)
        nav_frame.grid(row=0, column=0, sticky='ew', pady=5)
        nav_frame.grid_columnconfigure(1, weight=1)

        prev_button = ttk.Button(nav_frame, text="Previous", command=lambda: prev_page())
        page_label = ttk.Label(nav_frame, text="Page 1/1")
        next_button = ttk.Button(nav_frame, text="Next", command=lambda: next_page())

        prev_button.grid(row=0, column=0, padx=5)
        page_label.grid(row=0, column=1)
        next_button.grid(row=0, column=2, padx=5)

        # Matplotlib Figure
        fig = plt.Figure(figsize=(10, 6), dpi=100)
        canvas = FigureCanvasTkAgg(fig, master=preview_win)
        canvas.get_tk_widget().grid(row=1, column=0, sticky='nsew')

        # Data preparation
        plot_data = []
        for path in self.selected_fields:
            msg_type, instance_id, field = path.split('/')
            data = self.message_data[msg_type][instance_id]
            times = data['times']
            values = data['data'][field]
            if len(times) == len(values):
                plot_data.append({
                    'times': times,
                    'values': values,
                    'title': f"{msg_type} (ID {instance_id})\n{field}"
                })

        # Pagination variables
        grid_rows = 3
        grid_cols = 3
        plots_per_page = grid_rows * grid_cols
        total_pages = (len(plot_data) + plots_per_page - 1) // plots_per_page
        current_page = 0

        def plot_page():
            nonlocal current_page
            fig.clear()
            start_idx = current_page * plots_per_page
            end_idx = min(start_idx + plots_per_page, len(plot_data))
            current_plots = plot_data[start_idx:end_idx]

            for i, plot in enumerate(current_plots):
                ax = fig.add_subplot(grid_rows, grid_cols, i+1)
                ax.plot(plot['times'], plot['values'], 'b-')
                ax.set_title(plot['title'], fontsize=8)
                ax.set_xlabel("Time (s)", fontsize=6)
                ax.grid(True)
                ax.tick_params(labelsize=6)
                ax.format_coord = lambda x, y: f'Time: {x:.2f}s, Value: {y:.2f}'

            fig.tight_layout()
            canvas.draw()
            page_label.config(text=f"Page {current_page+1}/{total_pages}")
            prev_button["state"] = "normal" if current_page > 0 else "disabled"
            next_button["state"] = "normal" if current_page < total_pages-1 else "disabled"

        def prev_page():
            nonlocal current_page
            if current_page > 0:
                current_page -= 1
                plot_page()

        def next_page():
            nonlocal current_page
            if current_page < total_pages - 1:
                current_page += 1
                plot_page()

        # Initial plot
        plot_page()
        if total_pages <= 1:
            prev_button.grid_remove()
            page_label.grid_remove()
            next_button.grid_remove()

        # Cursor coordinates
        def update_cursor(event):
            if event.inaxes:
                x, y = event.xdata, event.ydata
                if x and y:
                    preview_win.cursor_label.config(text=f'Time: {x:.2f}s, Value: {y:.2f}')
            else:
                preview_win.cursor_label.config(text="")

        preview_win.cursor_label = ttk.Label(preview_win, text="")
        preview_win.cursor_label.grid(row=2, column=0, sticky='se', padx=10, pady=5)
        canvas.mpl_connect('motion_notify_event', update_cursor)
    
    def export_favorite(self):
        if not self.selected_fields:
            messagebox.showwarning("No Selection", "No fields selected to export as favorite.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Save Favorite"
        )
        if not file_path:
            return
        
        try:
            with open(file_path, 'w') as f:
                json.dump(list(self.selected_fields), f)
            messagebox.showinfo("Success", "Favorite exported successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export favorite: {str(e)}")

    def import_favorite(self):
        file_path = filedialog.askopenfilename(
            title="Select Favorite File",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if not file_path:
            return
        
        try:
            with open(file_path, 'r') as f:
                favorite = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load favorite: {str(e)}")
            return
        
        # Validate paths against current data
        valid_paths = set()
        for path in favorite:
            parts = path.split('/')
            if len(parts) != 3:
                continue
            msg_type, instance_id, field = parts
            if msg_type in self.message_data:
                if instance_id in self.message_data[msg_type]:
                    if field in self.message_data[msg_type][instance_id]['data']:
                        valid_paths.add(path)
        
        self.selected_fields = valid_paths
        self.populate_tree()  # Refresh tree and update selections
        messagebox.showinfo("Success", f"Imported {len(valid_paths)} valid fields.")

def open_xml_exporter():
    if XmlExporterGUI._instance is None:
        root = tk.Toplevel()
        exporter = XmlExporterGUI(root)
    else:
        messagebox.showinfo("Info", "XML Exporter is already open")

if __name__ == "__main__":
    root = tk.Tk()
    ttk.Button(root, text="Open XML Exporter", command=open_xml_exporter).pack(padx=20, pady=20)
    root.mainloop()