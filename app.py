import gradio as gr
import subprocess
import re
import threading
from pathlib import Path
import signal
import time

# Globals for Live Camera
process = None
captured_output = ""
reader_thread = None
output_lock = threading.Lock()

# Function to extract summary from tracking output
def extract_summary(output_text):
    summary_lines = []
    for line in output_text.splitlines():
        if "Done." in line:
            summary_lines.append(line.strip())
    
    if not summary_lines:
        return "No object summary found."

    last_line = summary_lines[-1]
    try:
        resolution_split = re.split(r"\d+x\d+", last_line, maxsplit=1)
        if len(resolution_split) > 1:
            useful_part = resolution_split[1]
        else:
            useful_part = last_line  # fallback

        useful_part = useful_part.split('Done.')[0].strip()

        if not useful_part:
            return "No object summary found."

        return useful_part

    except Exception as e:
        return f"Error parsing summary: {str(e)}"

# Function to find latest exp folder and output video
def find_latest_output_video():
    base_dir = Path("runs/track")
    if not base_dir.exists():
        return None

    # Find all exp folders
    exp_folders = [f for f in base_dir.iterdir() if f.is_dir() and f.name.startswith("exp")]

    if not exp_folders:
        return None

    # Find the latest modified exp folder
    latest_exp_folder = max(exp_folders, key=lambda f: f.stat().st_mtime)

    # Inside that folder, find any .mp4 file
    mp4_files = list(latest_exp_folder.glob("*.mp4"))
    if not mp4_files:
        return None

    # Assume first .mp4 file is the output we want
    return str(mp4_files[0])

# Process Image (no --save-vid, no video output)
def process_image(image_file):
    command = f"python track.py --source '{image_file}'"
    output = subprocess.getoutput(command)
    summary = extract_summary(output)
    return summary

# Process Video (with --save-vid, return summary + video)
def process_video(video_file):
    command = f"python track.py --source '{video_file}' --save-vid"
    output = subprocess.getoutput(command)
    summary = extract_summary(output)
    video_path = find_latest_output_video()
    return summary, video_path

# Read output for Live Camera
def read_output():
    global captured_output
    for line in iter(process.stdout.readline, ''):
        with output_lock:
            captured_output += line
    process.stdout.close()

# Start Live Camera Tracking
def start_camera():
    global process, captured_output, reader_thread
    captured_output = ""
    if process is None:
        process = subprocess.Popen(
            ["python", "track.py", "--source", "0", "--save-vid"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        reader_thread = threading.Thread(target=read_output)
        reader_thread.start()
    return "Live camera tracking started. Press 'Stop' to finish."

def extract_summary_live_camera(output_text):
    max_counter = {}

    for line in output_text.splitlines():
        if "Done." in line:
            try:
                parts = re.split(r"\d+x\d+", line, maxsplit=1)
                if len(parts) > 1:
                    useful_part = parts[1]
                else:
                    useful_part = line
                useful_part = useful_part.split('Done.')[0].strip()

                if useful_part:
                    objects = useful_part.split(",")
                    for obj in objects:
                        obj = obj.strip()
                        if obj:
                            match = re.match(r"(\d+)\s+(.*)", obj)
                            if match:
                                count = int(match.group(1))
                                name = match.group(2).rstrip('s')  # normalize singular

                                if name in max_counter:
                                    max_counter[name] = max(max_counter[name], count)
                                else:
                                    max_counter[name] = count
            except Exception:
                continue

    if not max_counter:
        return "No object summary found."

    summary_lines = [f"{count} {obj}" for obj, count in max_counter.items()]
    return " and ".join(summary_lines)

# Stop Live Camera Tracking (return summary + video)
def stop_camera():
    global process, captured_output, reader_thread
    if process is not None:
        try:
            # Send SIGINT (like pressing Ctrl+C)
            process.send_signal(signal.SIGINT)

            # Wait for the process to exit
            process.wait(timeout=20)

            # Ensure reader thread finishes
            if reader_thread is not None:
                reader_thread.join()

            # After stopping, wait a little to let the OS flush file
            time.sleep(2)  # wait 2 seconds to ensure .mp4 is flushed properly

        except Exception as e:
            captured_output += f"\n[Error while stopping: {str(e)}]"
        finally:
            process = None
            reader_thread = None

        # Extract summary from captured output
        summary = extract_summary_live_camera(captured_output)

        # Now safely find the latest output video
        video_path = find_latest_output_video()
        return summary, video_path

    else:
        return "No process running.", None

# Gradio Interface
with gr.Blocks() as app:
    gr.Markdown("# Object Tracking Service")

    # Image Tab
    with gr.Tab("Image Input"):
        image_input = gr.File(label="Upload Image")
        image_summary = gr.Textbox(label="Summary", lines=3)
        image_button = gr.Button("Run Image Tracking")
        image_button.click(
            fn=process_image,
            inputs=[image_input],
            outputs=[image_summary]
        )

    # Video Tab
    with gr.Tab("Video Input"):
        video_input = gr.File(label="Upload Video")
        video_summary = gr.Textbox(label="Summary", lines=3)
        video_output_video = gr.Video(label="Tracked Output Video")
        video_button = gr.Button("Run Video Tracking")
        video_button.click(
            fn=process_video,
            inputs=[video_input],
            outputs=[video_summary, video_output_video]
        )

    # Live Camera Tab
    with gr.Tab("Live Camera"):
        live_summary = gr.Textbox(label="Summary (after stopping)", lines=3)
        live_output_video = gr.Video(label="Tracked Live Camera Output")
        live_button = gr.Button("Start Camera Tracking")
        stop_button = gr.Button("Stop Camera Tracking and Show Tracked Video and Summary")

        live_button.click(fn=start_camera, outputs=[])
        stop_button.click(fn=stop_camera, outputs=[live_summary, live_output_video])

app.launch(server_name="0.0.0.0", server_port=8080)
