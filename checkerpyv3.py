import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import requests
import re
import json
import subprocess
import threading
from datetime import datetime
import queue
from collections import Counter
import numpy as np

# Import matplotlib for pie charts
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available. Pie chart export disabled.")

class IPTVStreamTester:
    def __init__(self, root):
        self.root = root
        self.root.title("IPTV Stream Quality Tester")
        self.root.geometry("1000x700")
        
        self.channels = []
        self.groups = {}
        self.test_results = []
        self.test_queue = queue.Queue()
        self.is_testing = False
        
        self.create_widgets()
    
    def create_widgets(self):
        # Notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab 1: M3U Playlist
        self.m3u_frame = ttk.Frame(notebook)
        notebook.add(self.m3u_frame, text='M3U Playlist')
        self.create_m3u_tab()
        
        # Tab 2: Xtream Codes
        self.xtream_frame = ttk.Frame(notebook)
        notebook.add(self.xtream_frame, text='Xtream Codes')
        self.create_xtream_tab()
        
        # Tab 3: Results
        self.results_frame = ttk.Frame(notebook)
        notebook.add(self.results_frame, text='Test Results')
        self.create_results_tab()
    
    def create_m3u_tab(self):
        # M3U URL/File input
        input_frame = ttk.LabelFrame(self.m3u_frame, text="M3U Source", padding=10)
        input_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(input_frame, text="M3U URL:").grid(row=0, column=0, sticky='w', pady=5)
        self.m3u_url_entry = ttk.Entry(input_frame, width=50)
        self.m3u_url_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(input_frame, text="Load from File", 
                  command=self.load_m3u_file).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(input_frame, text="Load from URL", 
                  command=self.load_m3u_url).grid(row=0, column=3, padx=5, pady=5)
        
        # Groups selection
        self.create_groups_section(self.m3u_frame)
    
    def create_xtream_tab(self):
        # Xtream login frame
        login_frame = ttk.LabelFrame(self.xtream_frame, text="Xtream Codes Login", padding=10)
        login_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(login_frame, text="Server URL:").grid(row=0, column=0, sticky='w', pady=5)
        self.xtream_server = ttk.Entry(login_frame, width=40)
        self.xtream_server.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(login_frame, text="Username:").grid(row=1, column=0, sticky='w', pady=5)
        self.xtream_username = ttk.Entry(login_frame, width=40)
        self.xtream_username.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(login_frame, text="Password:").grid(row=2, column=0, sticky='w', pady=5)
        self.xtream_password = ttk.Entry(login_frame, width=40, show="*")
        self.xtream_password.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Button(login_frame, text="Connect", 
                  command=self.connect_xtream).grid(row=3, column=1, pady=10)
        
        # Groups selection
        self.create_groups_section(self.xtream_frame)
    
    def create_groups_section(self, parent):
        # Groups frame
        groups_frame = ttk.LabelFrame(parent, text="Channel Groups", padding=10)
        groups_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Listbox for groups
        list_frame = ttk.Frame(groups_frame)
        list_frame.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.groups_listbox = tk.Listbox(list_frame, selectmode='multiple', 
                                         yscrollcommand=scrollbar.set)
        self.groups_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.groups_listbox.yview)
        
        # Buttons
        button_frame = ttk.Frame(groups_frame)
        button_frame.pack(side='right', fill='y', padx=10)
        
        ttk.Button(button_frame, text="Select All", 
                  command=self.select_all_groups).pack(pady=5)
        ttk.Button(button_frame, text="Deselect All", 
                  command=self.deselect_all_groups).pack(pady=5)
        ttk.Button(button_frame, text="Start Testing", 
                  command=self.start_testing).pack(pady=20)
        ttk.Button(button_frame, text="Stop Testing", 
                  command=self.stop_testing).pack(pady=5)
        
        # Progress
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(button_frame, textvariable=self.progress_var, 
                 wraplength=150).pack(pady=10)
        
        self.progress_bar = ttk.Progressbar(button_frame, mode='determinate')
        self.progress_bar.pack(pady=5)
    
    def create_results_tab(self):
        # Results display
        columns = ('Channel', 'Group', 'Resolution', 'FPS', 'Bitrate', 'Codec', 'Status')
        
        self.results_tree = ttk.Treeview(self.results_frame, columns=columns, 
                                         show='tree headings')
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(self.results_frame, orient='vertical', 
                                 command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        self.results_tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y', pady=10)
        
        # Export buttons frame
        export_frame = ttk.Frame(self.results_frame)
        export_frame.pack(pady=5)
        
        ttk.Button(export_frame, text="Export to CSV", 
                  command=self.export_to_csv).pack(side='left', padx=5)
        ttk.Button(export_frame, text="Export to TXT", 
                  command=self.export_to_txt).pack(side='left', padx=5)
        ttk.Button(export_frame, text="Export Pie Chart (PNG)", 
                  command=self.export_pie_charts).pack(side='left', padx=5)
    
    def load_m3u_file(self):
        filename = filedialog.askopenfilename(
            title="Select M3U File",
            filetypes=(("M3U files", "*.m3u"), ("All files", "*.*"))
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.parse_m3u(content)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read file: {str(e)}")
    
    def load_m3u_url(self):
        url = self.m3u_url_entry.get()
        if url:
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                # Try different encodings
                try:
                    content = response.content.decode('utf-8')
                except UnicodeDecodeError:
                    content = response.content.decode('latin-1')
                self.parse_m3u(content)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load M3U: {str(e)}")
    
    def parse_m3u(self, content):
        """Fixed M3U parser with better group-title extraction"""
        self.channels = []
        self.groups = {}
        
        lines = content.split('\n')
        current_channel = {}
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            if line.startswith('#EXTINF'):
                # Extract group-title using multiple patterns
                group = "Uncategorized"
                
                # Pattern 1: group-title="..."
                group_match = re.search(r'group-title="([^"]*)"', line, re.IGNORECASE)
                if group_match:
                    group = group_match.group(1).strip()
                else:
                    # Pattern 2: group-title='...'
                    group_match = re.search(r"group-title='([^']*)'", line, re.IGNORECASE)
                    if group_match:
                        group = group_match.group(1).strip()
                
                # Extract channel name - everything after the last comma
                name = "Unknown"
                comma_split = line.split(',', 1)
                if len(comma_split) > 1:
                    name = comma_split[1].strip()
                
                # Store tvg-id and tvg-logo if available
                tvg_id_match = re.search(r'tvg-id="([^"]*)"', line, re.IGNORECASE)
                tvg_logo_match = re.search(r'tvg-logo="([^"]*)"', line, re.IGNORECASE)
                
                current_channel = {
                    'name': name,
                    'group': group,
                    'tvg_id': tvg_id_match.group(1) if tvg_id_match else None,
                    'tvg_logo': tvg_logo_match.group(1) if tvg_logo_match else None
                }
                
            elif line and not line.startswith('#') and current_channel:
                current_channel['url'] = line
                self.channels.append(current_channel)
                
                # Add to groups dictionary
                group_name = current_channel['group']
                if group_name not in self.groups:
                    self.groups[group_name] = []
                self.groups[group_name].append(current_channel)
                
                current_channel = {}
        
        self.update_groups_listbox()
        messagebox.showinfo("Success", 
                          f"Loaded {len(self.channels)} channels in {len(self.groups)} groups")
    
    def connect_xtream(self):
        server = self.xtream_server.get().rstrip('/')
        username = self.xtream_username.get()
        password = self.xtream_password.get()
        
        if not all([server, username, password]):
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        try:
            # Authenticate
            auth_url = f"{server}/player_api.php?username={username}&password={password}"
            response = requests.get(auth_url, timeout=30)
            auth_data = response.json()
            
            if auth_data.get('user_info', {}).get('auth') != 1:
                messagebox.showerror("Error", "Authentication failed")
                return
            
            # Get categories first
            categories_url = f"{server}/player_api.php?username={username}&password={password}&action=get_live_categories"
            categories_response = requests.get(categories_url, timeout=30)
            categories = {cat['category_id']: cat['category_name'] 
                         for cat in categories_response.json()}
            
            # Get live streams
            streams_url = f"{server}/player_api.php?username={username}&password={password}&action=get_live_streams"
            streams_response = requests.get(streams_url, timeout=30)
            streams = streams_response.json()
            
            # Parse channels
            self.channels = []
            self.groups = {}
            
            for stream in streams:
                category_id = stream.get('category_id', '0')
                group_name = categories.get(category_id, 'Uncategorized')
                
                channel = {
                    'name': stream.get('name', 'Unknown'),
                    'group': group_name,
                    'url': f"{server}/live/{username}/{password}/{stream['stream_id']}.ts",
                    'stream_id': stream.get('stream_id'),
                    'epg_channel_id': stream.get('epg_channel_id'),
                    'stream_icon': stream.get('stream_icon')
                }
                
                self.channels.append(channel)
                
                if group_name not in self.groups:
                    self.groups[group_name] = []
                self.groups[group_name].append(channel)
            
            self.update_groups_listbox()
            messagebox.showinfo("Success", 
                              f"Connected! Loaded {len(self.channels)} channels in {len(self.groups)} groups")
            
        except Exception as e:
            messagebox.showerror("Error", f"Connection failed: {str(e)}")
    
    def update_groups_listbox(self):
        self.groups_listbox.delete(0, tk.END)
        for group in sorted(self.groups.keys()):
            self.groups_listbox.insert(tk.END, 
                                      f"{group} ({len(self.groups[group])} channels)")
    
    def select_all_groups(self):
        self.groups_listbox.select_set(0, tk.END)
    
    def deselect_all_groups(self):
        self.groups_listbox.select_clear(0, tk.END)
    
    def start_testing(self):
        selected_indices = self.groups_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select at least one group")
            return
        
        # Get selected groups
        selected_groups = []
        for idx in selected_indices:
            group_text = self.groups_listbox.get(idx)
            # Extract group name before the last parenthesis
            group_name = group_text.rsplit(' (', 1)[0]
            selected_groups.append(group_name)
        
        # Get channels from selected groups
        channels_to_test = []
        for group in selected_groups:
            if group in self.groups:
                channels_to_test.extend(self.groups[group])
        
        if not channels_to_test:
            messagebox.showerror("Error", "No channels found in selected groups")
            return
        
        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        self.is_testing = True
        self.test_results = []
        self.progress_bar['maximum'] = len(channels_to_test)
        self.progress_bar['value'] = 0
        
        # Start testing in separate thread
        thread = threading.Thread(target=self.test_channels, 
                                 args=(channels_to_test,))
        thread.daemon = True
        thread.start()
    
    def stop_testing(self):
        self.is_testing = False
        self.progress_var.set("Testing stopped")
    
    def test_channels(self, channels):
        for idx, channel in enumerate(channels):
            if not self.is_testing:
                break
            
            self.progress_var.set(f"Testing {idx+1}/{len(channels)}: {channel['name'][:30]}")
            result = self.test_stream(channel)
            self.test_results.append(result)
            
            # Update UI
            self.root.after(0, self.update_results_display, result)
            self.root.after(0, self.progress_bar.step, 1)
        
        self.progress_var.set(f"Complete! Tested {len(channels)} channels")
        self.is_testing = False
    
    def test_stream(self, channel):
        """Fixed stream testing with proper bitrate detection"""
        result = {
            'channel': channel['name'],
            'group': channel['group'],
            'url': channel['url'],
            'resolution': 'N/A',
            'fps': 'N/A',
            'bitrate': 'N/A',
            'codec': 'N/A',
            'status': 'Testing...'
        }
        
        try:
            # Use ffprobe with specific options for live streams
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-hide_banner',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height,r_frame_rate,bit_rate,codec_name',
                '-show_entries', 'format=bit_rate',
                '-print_format', 'json',
                '-analyzeduration', '10000000',
                '-probesize', '10000000',
                '-timeout', '15000000',
                channel['url']
            ]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE)
            stdout, stderr = process.communicate(timeout=20)
            
            if stdout:
                data = json.loads(stdout)
                
                # Extract video stream info
                streams = data.get('streams', [])
                if streams and len(streams) > 0:
                    stream = streams[0]
                    
                    # Resolution
                    width = stream.get('width', 'N/A')
                    height = stream.get('height', 'N/A')
                    if width != 'N/A' and height != 'N/A':
                        result['resolution'] = f"{width}x{height}"
                    
                    # FPS calculation
                    fps_str = stream.get('r_frame_rate', '0/0')
                    if '/' in fps_str:
                        try:
                            num, den = map(int, fps_str.split('/'))
                            if den != 0:
                                result['fps'] = f"{num/den:.2f}"
                        except:
                            result['fps'] = 'N/A'
                    
                    # Bitrate - try stream first, then format
                    bitrate = stream.get('bit_rate')
                    if not bitrate or bitrate == 'N/A':
                        # Try format bitrate
                        format_data = data.get('format', {})
                        bitrate = format_data.get('bit_rate')
                    
                    if bitrate and bitrate != 'N/A':
                        try:
                            bitrate_kbps = int(bitrate) / 1000
                            if bitrate_kbps >= 1000:
                                result['bitrate'] = f"{bitrate_kbps/1000:.2f} Mbps"
                            else:
                                result['bitrate'] = f"{bitrate_kbps:.0f} Kbps"
                        except:
                            result['bitrate'] = 'N/A'
                    
                    # Codec
                    result['codec'] = stream.get('codec_name', 'N/A')
                    result['status'] = 'OK'
                else:
                    result['status'] = 'No video stream'
            else:
                result['status'] = 'Probe failed'
                
        except subprocess.TimeoutExpired:
            result['status'] = 'Timeout'
            try:
                process.kill()
            except:
                pass
        except Exception as e:
            result['status'] = f'Error: {str(e)[:40]}'
        
        return result
    
    def update_results_display(self, result):
        self.results_tree.insert('', 'end', values=(
            result['channel'],
            result['group'],
            result['resolution'],
            result['fps'],
            result['bitrate'],
            result['codec'],
            result['status']
        ))
    
    def export_to_csv(self):
        """Export results to CSV file"""
        if not self.test_results:
            messagebox.showwarning("Warning", "No results to export")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*"))
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("Channel,Group,Resolution,FPS,Bitrate,Codec,Status\n")
                    for result in self.test_results:
                        # Escape commas in channel names
                        channel_name = result['channel'].replace(',', ';')
                        group_name = result['group'].replace(',', ';')
                        f.write(f'"{channel_name}","{group_name}",'
                               f"{result['resolution']},{result['fps']},"
                               f"{result['bitrate']},{result['codec']},"
                               f"{result['status']}\n")
                
                messagebox.showinfo("Success", f"Results exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {str(e)}")
    
    def export_to_txt(self):
        """Export results to formatted text file"""
        if not self.test_results:
            messagebox.showwarning("Warning", "No results to export")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    # Write header
                    f.write("=" * 100 + "\n")
                    f.write("IPTV STREAM TEST RESULTS\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Total Channels Tested: {len(self.test_results)}\n")
                    f.write("=" * 100 + "\n\n")
                    
                    # Count statistics
                    successful = sum(1 for r in self.test_results if r['status'] == 'OK')
                    failed = len(self.test_results) - successful
                    
                    f.write("SUMMARY STATISTICS\n")
                    f.write("-" * 100 + "\n")
                    f.write(f"Successful Tests: {successful}\n")
                    f.write(f"Failed Tests: {failed}\n")
                    f.write(f"Success Rate: {(successful/len(self.test_results)*100):.1f}%\n\n")
                    
                    # Resolution distribution
                    resolutions = [r['resolution'] for r in self.test_results if r['resolution'] != 'N/A']
                    if resolutions:
                        res_count = Counter(resolutions)
                        f.write("RESOLUTION DISTRIBUTION\n")
                        f.write("-" * 100 + "\n")
                        for res, count in res_count.most_common():
                            f.write(f"{res}: {count} channels ({count/len(resolutions)*100:.1f}%)\n")
                        f.write("\n")
                    
                    # FPS distribution
                    fps_values = [r['fps'] for r in self.test_results if r['fps'] != 'N/A']
                    if fps_values:
                        fps_count = Counter(fps_values)
                        f.write("FPS DISTRIBUTION\n")
                        f.write("-" * 100 + "\n")
                        for fps, count in fps_count.most_common():
                            f.write(f"{fps} FPS: {count} channels ({count/len(fps_values)*100:.1f}%)\n")
                        f.write("\n")
                    
                    # Detailed results
                    f.write("DETAILED CHANNEL RESULTS\n")
                    f.write("=" * 100 + "\n\n")
                    
                    for idx, result in enumerate(self.test_results, 1):
                        f.write(f"Channel #{idx}\n")
                        f.write("-" * 100 + "\n")
                        f.write(f"Name: {result['channel']}\n")
                        f.write(f"Group: {result['group']}\n")
                        f.write(f"Resolution: {result['resolution']}\n")
                        f.write(f"FPS: {result['fps']}\n")
                        f.write(f"Bitrate: {result['bitrate']}\n")
                        f.write(f"Codec: {result['codec']}\n")
                        f.write(f"Status: {result['status']}\n")
                        f.write("\n")
                
                messagebox.showinfo("Success", f"Results exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {str(e)}")
    
    def export_pie_charts(self):
        """Export a single pie chart showing combined resolution+FPS distribution"""
        if not self.test_results:
            messagebox.showwarning("Warning", "No results to export")
            return
        
        if not MATPLOTLIB_AVAILABLE:
            messagebox.showerror("Error", "Matplotlib is required for chart export.\nInstall it with: pip install matplotlib")
            return
        
        # Ask for file to save chart
        filename = filedialog.asksaveasfilename(
            title="Save Pie Chart",
            defaultextension=".png",
            filetypes=(("PNG files", "*.png"), ("All files", "*.*"))
        )
        
        if not filename:
            return
        
        try:
            # Filter successful results only
            successful_results = [r for r in self.test_results if r['status'] == 'OK']
            
            if not successful_results:
                messagebox.showwarning("Warning", "No successful test results to visualize")
                return
            
            # Combine resolution and FPS into single categories
            combined_data = []
            for result in successful_results:
                resolution = result.get('resolution', 'N/A')
                fps = result.get('fps', 'N/A')
                
                # Skip if either is N/A
                if resolution == 'N/A' or fps == 'N/A':
                    continue
                
                # Parse resolution to get height (e.g., "1920x1080" -> "1080p")
                if 'x' in resolution:
                    height = resolution.split('x')[1]
                    res_label = f"{height}p"
                else:
                    res_label = resolution
                
                # Parse FPS (remove .00 if present)
                try:
                    fps_float = float(fps)
                    fps_label = str(int(fps_float)) if fps_float == int(fps_float) else fps
                except:
                    fps_label = fps
                
                # Combine as "720p60", "1080p30", etc.
                combined_label = f"{res_label}{fps_label}"
                combined_data.append(combined_label)
            
            if not combined_data:
                messagebox.showwarning("Warning", "No valid data to create chart")
                return
            
            # Count occurrences
            data_count = Counter(combined_data)
            
            # Sort by count (descending) for better visualization
            sorted_items = data_count.most_common()
            labels = [item[0] for item in sorted_items]
            sizes = [item[1] for item in sorted_items]
            
            # Create figure
            fig, ax = plt.subplots(figsize=(12, 10))
            
            # Generate title with date
            current_date = datetime.now().strftime('%B %d')
            fig.suptitle(f'IPTV Stream Quality Distribution: {current_date}', 
                         fontsize=18, fontweight='bold', y=0.98)
            
            # Color scheme
            colors = plt.cm.tab20c(range(len(labels)))
            
            # Helper function for percentage labels
            def make_autopct(values):
                def my_autopct(pct):
                    total = sum(values)
                    val = int(round(pct*total/100.0))
                    return f'{pct:.1f}%' if pct > 2 else ''  # Hide labels for small slices
                return my_autopct
            
            # Create pie chart
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=None,  # Labels will be outside
                colors=colors,
                autopct=make_autopct(sizes),
                startangle=90,
                pctdistance=0.85,
                explode=[0.02] * len(sizes)  # Slight explosion for all slices
            )
            
            # Customize percentage text
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(11)
                autotext.set_fontweight('bold')
            
            # Add labels outside the pie with counts
            for i, (label, size) in enumerate(zip(labels, sizes)):
                # Calculate angle for label placement
                angle = (wedges[i].theta2 + wedges[i].theta1) / 2
                x = 1.3 * np.cos(np.radians(angle))
                y = 1.3 * np.sin(np.radians(angle))
                
                # Determine horizontal alignment
                ha = 'left' if x > 0 else 'right'
                
                # Add label with count
                ax.text(x, y, f'{label} ({size})', 
                       ha=ha, va='center', fontsize=11, fontweight='bold')
            
            # Equal aspect ratio ensures circular pie
            ax.axis('equal')
            
            # Adjust layout
            plt.tight_layout(rect=[0, 0, 1, 0.96])
            
            # Save the figure
            plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            messagebox.showinfo("Success", 
                              f"Pie chart exported successfully!\n\n"
                              f"File: {filename}\n"
                              f"Total channels: {len(combined_data)}\n"
                              f"Categories: {len(labels)}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Chart export failed: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = IPTVStreamTester(root)
    root.mainloop()
