import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import re
import json
import sys
import os
import subprocess
import threading
from datetime import datetime
from collections import Counter
import numpy as np

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Matplotlib not found, pie chart export disabled.")

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and PyInstaller """
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Use this for all ffmpeg subprocess calls:

ffmpeg_path = resource_path(os.path.join("ffmpeg", "ffmpeg.exe"))
ffprobe_path = resource_path(os.path.join("ffmpeg", "ffprobe.exe"))

# Example subprocess call usage:
def run_ffmpeg_command(args):
    command = [ffmpeg_path] + args
    proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc

# Example:
# proc = run_ffmpeg_command(['-version'])
# print(proc.stdout.decode())

# Similarly for ffprobe:
def run_ffprobe_command(args):
    command = [ffprobe_path] + args
    proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc

def get_video_bitrate(url):
    command = [
        'ffmpeg', '-v', 'debug', '-user_agent', 'VLC/3.0.14', '-i', url,
        '-t', '10', '-f', 'null', '-'
    ]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
        output = result.stderr.decode()
        total_bytes = 0
        for line in output.splitlines():
            if "Statistics:" in line:
                if "bytes read" in line:
                    parts = line.split("bytes read")
                    size_str = parts[0].strip().split()[-1]
                    if size_str.isdigit():
                        total_bytes = int(size_str)
                        break
        if total_bytes == 0:
            return "N/A"
        bitrate_kbps = (total_bytes * 8) / 1000 / 10
        return f"{round(bitrate_kbps)} Kbps"
    except Exception:
        return "N/A"


class IPTVStreamTester:
    def __init__(self, root):
        self.root = root
        self.root.title("IPTV Stream Quality Tester")
        self.root.geometry("1000x700")
        self.channels = []
        self.groups = {}
        self.test_results = []
        self.is_testing = False
        self.create_widgets()

    def create_widgets(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        self.m3u_frame = ttk.Frame(notebook)
        notebook.add(self.m3u_frame, text='M3U Playlist')
        self.create_m3u_tab()
        self.xtream_frame = ttk.Frame(notebook)
        notebook.add(self.xtream_frame, text='Xtream Codes')
        self.create_xtream_tab()
        self.results_frame = ttk.Frame(notebook)
        notebook.add(self.results_frame, text='Test Results')
        self.create_results_tab()

    def create_m3u_tab(self):
        input_frame = ttk.LabelFrame(self.m3u_frame, text="M3U Source", padding=10)
        input_frame.pack(fill='x', padx=10, pady=10)
        ttk.Label(input_frame, text="M3U URL:").grid(row=0, column=0, sticky='w', pady=5)
        self.m3u_url_entry = ttk.Entry(input_frame, width=50)
        self.m3u_url_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(input_frame, text="Load from File", command=self.load_m3u_file).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(input_frame, text="Load from URL", command=self.load_m3u_url).grid(row=0, column=3, padx=5, pady=5)
        self.create_groups_section(self.m3u_frame)

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
                try:
                    content = response.content.decode('utf-8')
                except UnicodeDecodeError:
                    content = response.content.decode('latin-1')
                self.parse_m3u(content)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load M3U: {str(e)}")

    def parse_m3u(self, content):
        self.channels = []
        self.groups = {}
        lines = content.split('\n')
        current_channel = {}
        for line in lines:
            line = line.strip()
            if line.startswith('#EXTINF'):
                group = "Uncategorized"
                group_match = re.search(r'group-title="([^"]*)"', line, re.IGNORECASE)
                if group_match:
                    group = group_match.group(1).strip()
                else:
                    group_match = re.search(r"group-title='([^']*)'", line, re.IGNORECASE)
                    if group_match:
                        group = group_match.group(1).strip()
                name = "Unknown"
                comma_split = line.split(',', 1)
                if len(comma_split) > 1:
                    name = comma_split[1].strip()
                current_channel = {'name': name, 'group': group}
            elif line and not line.startswith('#') and current_channel:
                current_channel['url'] = line
                self.channels.append(current_channel)
                group_name = current_channel['group']
                if group_name not in self.groups:
                    self.groups[group_name] = []
                self.groups[group_name].append(current_channel)
                current_channel = {}
        self.update_groups_listbox()
        messagebox.showinfo("Success", f"Loaded {len(self.channels)} channels in {len(self.groups)} groups")

    def create_xtream_tab(self):
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
        ttk.Button(login_frame, text="Connect", command=self.connect_xtream).grid(row=3, column=1, pady=10)
        self.create_groups_section(self.xtream_frame)

    def connect_xtream(self):
        server = self.xtream_server.get().rstrip('/')
        username = self.xtream_username.get()
        password = self.xtream_password.get()
        if not all([server, username, password]):
            messagebox.showerror("Error", "Please fill in all fields")
            return
        try:
            auth_url = f"{server}/player_api.php?username={username}&password={password}"
            response = requests.get(auth_url, timeout=30)
            auth_data = response.json()
            if auth_data.get('user_info', {}).get('auth') != 1:
                messagebox.showerror("Error", "Authentication failed")
                return
            categories_url = f"{server}/player_api.php?username={username}&password={password}&action=get_live_categories"
            categories_response = requests.get(categories_url, timeout=30)
            categories = {cat['category_id']: cat['category_name'] for cat in categories_response.json()}
            streams_url = f"{server}/player_api.php?username={username}&password={password}&action=get_live_streams"
            streams_response = requests.get(streams_url, timeout=30)
            streams = streams_response.json()
            self.channels = []
            self.groups = {}
            for stream in streams:
                category_id = stream.get('category_id', '0')
                group_name = categories.get(category_id, 'Uncategorized')
                channel = {
                    'name': stream.get('name', 'Unknown'),
                    'group': group_name,
                    'url': f"{server}/live/{username}/{password}/{stream['stream_id']}.ts",
                    'stream_id': stream.get('stream_id')
                }
                self.channels.append(channel)
                if group_name not in self.groups:
                    self.groups[group_name] = []
                self.groups[group_name].append(channel)
            self.update_groups_listbox()
            messagebox.showinfo("Success", f"Connected! Loaded {len(self.channels)} channels in {len(self.groups)} groups")
        except Exception as e:
            messagebox.showerror("Error", f"Connection failed: {str(e)}")

    def create_groups_section(self, parent):
        groups_frame = ttk.LabelFrame(parent, text="Channel Groups", padding=10)
        groups_frame.pack(fill='both', expand=True, padx=10, pady=10)
        list_frame = ttk.Frame(groups_frame)
        list_frame.pack(side='left', fill='both', expand=True)
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        self.groups_listbox = tk.Listbox(list_frame, selectmode='multiple', yscrollcommand=scrollbar.set)
        self.groups_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.groups_listbox.yview)
        button_frame = ttk.Frame(groups_frame)
        button_frame.pack(side='right', fill='y', padx=10)
        ttk.Button(button_frame, text="Select All", command=self.select_all_groups).pack(pady=5)
        ttk.Button(button_frame, text="Deselect All", command=self.deselect_all_groups).pack(pady=5)
        ttk.Button(button_frame, text="Start Testing", command=self.start_testing).pack(pady=20)
        ttk.Button(button_frame, text="Stop Testing", command=self.stop_testing).pack(pady=5)
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(button_frame, textvariable=self.progress_var, wraplength=150).pack(pady=10)
        self.progress_bar = ttk.Progressbar(button_frame, mode='determinate')
        self.progress_bar.pack(pady=5)

    def update_groups_listbox(self):
        self.groups_listbox.delete(0, tk.END)
        for group in sorted(self.groups.keys()):
            self.groups_listbox.insert(tk.END, f"{group} ({len(self.groups[group])} channels)")

    def select_all_groups(self):
        self.groups_listbox.select_set(0, 'end')

    def deselect_all_groups(self):
        self.groups_listbox.select_clear(0, 'end')

    def create_results_tab(self):
        columns = ('Channel', 'Group', 'Resolution', 'FPS', 'Bitrate', 'Codec', 'Status')
        self.results_tree = ttk.Treeview(self.results_frame, columns=columns, show='tree headings')
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=120)
        scrollbar = ttk.Scrollbar(self.results_frame, orient='vertical', command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        self.results_tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y', pady=10)
        export_frame = ttk.Frame(self.results_frame)
        export_frame.pack(pady=5)
        ttk.Button(export_frame, text="Export to CSV", command=self.export_to_csv).pack(side='left', padx=5)
        ttk.Button(export_frame, text="Export to TXT", command=self.export_to_txt).pack(side='left', padx=5)
        ttk.Button(export_frame, text="Export Pie Chart (PNG)", command=self.export_pie_charts).pack(side='left', padx=5)

    def start_testing(self):
        selected_indices = self.groups_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select at least one group")
            return
        selected_groups = [self.groups_listbox.get(i).rsplit(' (', 1)[0] for i in selected_indices]
        channels_to_test = []
        for group in selected_groups:
            if group in self.groups:
                channels_to_test.extend(self.groups[group])
        if not channels_to_test:
            messagebox.showerror("Error", "No channels found in selected groups")
            return
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.is_testing = True
        self.test_results = []
        self.progress_bar['maximum'] = len(channels_to_test)
        self.progress_bar['value'] = 0
        threading.Thread(target=self.test_channels, args=(channels_to_test,), daemon=True).start()

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
            self.root.after(0, self.update_results_display, result)
            self.root.after(0, self.progress_bar.step, 1)
        self.progress_var.set(f"Complete! Tested {len(channels)} channels")
        self.is_testing = False

    def test_stream(self, channel):
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
            result['bitrate'] = get_video_bitrate(channel['url'])  # Use only this for bitrate estimation

            import shlex
            import json

            user_agent = "Mozilla/5.0"
            referer = "http://example.com"
            headers = f"User-Agent: {user_agent}\r\nReferer: {referer}\r\n"
            ffprobe_cmd = (
                f'ffprobe -headers "{headers}" -v error -select_streams v:0 -show_entries '
                'stream=width,height,codec_name,r_frame_rate '
                f'-of json "{channel["url"]}"'
            )
            probe = subprocess.run(shlex.split(ffprobe_cmd), stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, timeout=60)
            if probe.returncode != 0:
                result['status'] = "Dead"
                return result
            meta = json.loads(probe.stdout)
            if meta.get('streams'):
                v = meta['streams'][0]
                result['resolution'] = f'{v.get("width", "N/A")}x{v.get("height", "N/A")}'
                rfr = v.get('r_frame_rate')
                try:
                    if rfr and '/' in rfr:
                        num, den = [float(x) for x in rfr.split('/')]
                        result['fps'] = f"{num/den:.2f}"
                except:
                    result['fps'] = rfr or 'N/A'
                result['codec'] = v.get('codec_name', 'N/A')
            result['status'] = "OK"
        except subprocess.TimeoutExpired:
            result['status'] = "Timeout"
        except Exception as e:
            result['status'] = f'Error: {str(e)[:50]}'
        return result

    def update_results_display(self, result):
        self.results_tree.insert('', 'end', values=(
            result['channel'], result['group'], result['resolution'], result['fps'],
            result['bitrate'], result['codec'], result['status']
        ))

    def export_to_csv(self):
        if not self.test_results:
            messagebox.showwarning("Warning", "No results to export")
            return
        filename = filedialog.asksaveasfilename(defaultextension=".csv",
                                                filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("Channel,Group,Resolution,FPS,Bitrate,Codec,Status\n")
                    for r in self.test_results:
                        ch = r['channel'].replace(',', ';')
                        gr = r['group'].replace(',', ';')
                        f.write(f'"{ch}","{gr}",{r["resolution"]},{r["fps"]},{r["bitrate"]},{r["codec"]},{r["status"]}\n')
                messagebox.showinfo("Success", f"Results exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export CSV: {str(e)}")

    def export_to_txt(self):
        if not self.test_results:
            messagebox.showwarning("Warning", "No results to export")
            return
        filename = filedialog.asksaveasfilename(defaultextension=".txt",
                                                filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("="*80 + "\n")
                    f.write("IPTV STREAM TEST RESULTS\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Total Channels Tested: {len(self.test_results)}\n")
                    f.write("="*80 + "\n\n")
                    success = sum(1 for r in self.test_results if r['status'] == 'OK')
                    fail = len(self.test_results) - success
                    f.write(f"Successful Tests: {success}\nFailed Tests: {fail}\n")
                    f.write(f"Success Rate: {(success/len(self.test_results))*100:.1f}%\n\n")
                    resos = [r['resolution'] for r in self.test_results if r['resolution'] != 'N/A']
                    if resos:
                        c = Counter(resos)
                        f.write("Resolution Distribution:\n")
                        for k, v in c.most_common():
                            f.write(f"{k}: {v} channels ({v/len(resos)*100:.1f}%)\n")
                        f.write("\n")
                    fpss = [r['fps'] for r in self.test_results if r['fps'] != 'N/A']
                    if fpss:
                        c = Counter(fpss)
                        f.write("FPS Distribution:\n")
                        for k, v in c.most_common():
                            f.write(f"{k} FPS: {v} channels ({v/len(fpss)*100:.1f}%)\n")
                        f.write("\n")
                    f.write("Detailed Results:\n")
                    f.write("="*80 + "\n")
                    for idx, r in enumerate(self.test_results, 1):
                        f.write(f"#{idx} Name: {r['channel']}\nGroup: {r['group']}\n")
                        f.write(f"Resolution: {r['resolution']}\nFPS: {r['fps']}\n")
                        f.write(f"Bitrate: {r['bitrate']}\nCodec: {r['codec']}\nStatus: {r['status']}\n\n")
                messagebox.showinfo("Success", f"Results exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export TXT: {str(e)}")

    def export_pie_charts(self):
        if not self.test_results:
            messagebox.showwarning("Warning", "No results to export")
            return
        if not MATPLOTLIB_AVAILABLE:
            messagebox.showerror("Error", "Matplotlib needed for pie chart export.\npip install matplotlib")
            return
        filename = filedialog.asksaveasfilename(defaultextension=".png",
                                                filetypes=(("PNG files", "*.png"), ("All files", "*.*")),
                                                title="Save Pie Chart")
        if not filename:
            return
        try:
            successful = [r for r in self.test_results if r['status'] == 'OK']
            if not successful:
                messagebox.showwarning("Warning", "No successful results to create chart")
                return
            combined = []
            for r in successful:
                res = r.get('resolution', 'N/A')
                fps = r.get('fps', 'N/A')
                if res == 'N/A' or fps == 'N/A':
                    continue
                if 'x' in res:
                    h = res.split('x')[1]
                    res_label = f"{h}p"
                else:
                    res_label = res
                try:
                    ffloat = float(fps)
                    fps_label = str(int(ffloat)) if ffloat == int(ffloat) else fps
                except:
                    fps_label = fps
                combined.append(f"{res_label}{fps_label}")
            if not combined:
                messagebox.showwarning("Warning", "No valid data for chart")
                return
            count = Counter(combined)
            labels, sizes = zip(*count.most_common())
            fig, ax = plt.subplots(figsize=(12, 10))
            fig.suptitle(f'IPTV Stream Quality Distribution: {datetime.now().strftime("%B %d")}', fontsize=18, fontweight='bold', y=0.98)
            colors = plt.cm.tab20c(range(len(labels)))
            def autopct_func(vals):
                def my_autopct(pct):
                    total = sum(vals)
                    val = int(round(pct*total/100.0))
                    return f'{pct:.1f}%' if pct > 2 else ''
                return my_autopct
            wedges, texts, autotexts = ax.pie(sizes, labels=None, colors=colors, autopct=autopct_func(sizes),
                                              startangle=90, pctdistance=0.85, explode=[0.02]*len(sizes))
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(11)
                autotext.set_fontweight('bold')
            for i, (label, size) in enumerate(zip(labels, sizes)):
                angle = (wedges[i].theta2 + wedges[i].theta1) / 2
                x = 1.3 * np.cos(np.radians(angle))
                y = 1.3 * np.sin(np.radians(angle))
                ha = 'left' if x > 0 else 'right'
                ax.text(x, y, f'{label} ({size})', ha=ha, va='center', fontsize=11, fontweight='bold')
            ax.axis('equal')
            plt.tight_layout(rect=[0, 0, 1, 0.96])
            plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            messagebox.showinfo("Success", f"Pie chart exported successfully!\nFile: {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export pie chart: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = IPTVStreamTester(root)
    root.mainloop()
