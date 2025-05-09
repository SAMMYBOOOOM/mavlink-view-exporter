import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pymavlink import mavutil
import xml.etree.ElementTree as ET
import os

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
            self.master.geometry("500x600")
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
            text="Reload Log", 
            command=self.reload_log
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Clear Selection",
            command=self.clear_selection
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
        msg_type = self.tree.parent(item)
        if not msg_type:  # Clicked on message type
            return
        
        msg_id = self.tree.parent(msg_type)
        if not msg_id:  # Clicked on instance ID
            return

        # This must be a field
        field = self.tree.item(item)['text']
        full_path = f"{self.tree.item(msg_id)['text']}/{self.tree.item(msg_type)['text']}/{field}"

        if full_path in self.selected_fields:
            self.selected_fields.remove(full_path)
            self.tree.item(item, tags=('unchecked',))
        else:
            self.selected_fields.add(full_path)
            self.tree.item(item, tags=('checked',))

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

    def reload_log(self):
        if self.log_file and os.path.exists(self.log_file):
            self.parse_log_file()
            self.populate_tree()
            messagebox.showinfo("Info", "Log file reloaded successfully")

    def parse_log_file(self):
        # [Previous parse_log_file implementation remains the same]
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
        
        for msg_id in sorted(self.message_data.keys()):
            id_node = self.tree.insert('', 'end', text=msg_id)
            
            for instance_id, data in sorted(self.message_data[msg_id].items(), key=lambda x: int(x[0])):
                instance_node = self.tree.insert(id_node, 'end', text=instance_id)
                
                for field in sorted(data['data'].keys()):
                    self.tree.insert(instance_node, 'end', text=field, tags=('unchecked',))

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
        
        # Create XML structure
        root = ET.Element("MAVLinkData")
        
        # Parse selected fields and gather data
        field_data = {}
        min_length = float('inf')
        
        for full_path in self.selected_fields:
            msg_id, msg_type, field = full_path.split('/')
            data = self.message_data[msg_id][msg_type]
            times = data['times']
            values = data['data'][field]
            field_data[field] = values
            min_length = min(min_length, len(times))
        
        # Create records
        for i in range(min_length):
            record = ET.SubElement(root, "Record")
            ET.SubElement(record, "Time").text = f"{int(data['times'][i])}"
            for field, values in field_data.items():
                safe_field = field.replace(' ', '_').replace('[', '').replace(']', '')
                ET.SubElement(record, safe_field).text = str(values[i])
        
        tree = ET.ElementTree(root)
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
        messagebox.showinfo("Success", f"XML exported to:\n{file_path}")

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