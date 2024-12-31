import subprocess
import sys

# List of required packages
required_packages = [
    "requests",
    "asyncio",
    "psutil"
    # Built-in libraries like tkinter, os, threading, etc., don't need installation.
]

def install_and_import(package):
    """
    Attempts to import the package. If the package is not installed, installs it using pip.
    """
    try:
        __import__(package)
    except ImportError:
        print(f"{package} is not installed. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"{package} has been installed successfully.")
    except Exception as e:
        print(f"An error occurred during installation of {package}: {e}")

# Ensure required packages are installed
for package in required_packages:
    install_and_import(package)

# Now you can safely import all required modules
import tkinter as tk
from tkinter import filedialog, messagebox
import os,re,threading,psutil,requests,asyncio
# Global variables for pausing
global_email_settings = {}
valid_emails_global = []
pause_event = threading.Event()
pause_button_state = "SEND"

def handle_file_upload(entry):
    global valid_emails_global  # Access the global variable
    filepath = filedialog.askopenfilename(
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if filepath:
        entry.delete(0, tk.END)
        entry.insert(0, filepath)

        try:
            # Validate and count emails
            with open(filepath, "r") as file:
                email_list = [line.strip() for line in file if line.strip()]
                valid_emails_global = [email for email in email_list if is_valid_email(email)]  # Update global list

            # Update label with the total number of valid emails
            total_emails = len(valid_emails_global)
            file_label.config(text=f"Emails Loaded:[{total_emails}]")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process file: {e}")

    # Validate inputs after file upload
    validate_inputs()

# Helper function to validate email addresses
def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

# Function to send an email
def send_email(email_url, cookies, headers, html_content, recipient, email_settings):
    json_data = {
        'to': [recipient],
        'cc': [],
        'bcc': [],
        'isHTML': 1,
        'text': html_content,
        **email_settings,
    }

    try:
        response = requests.post(
            email_url,  # Use the dynamic email URL
            cookies=cookies,
            headers=headers,
            json=json_data,
        )
        return response
    except Exception as e:
        return f"Error: {e}"

# Function to load configuration from a file
def load_config(cookies_text, headers_text, email_settings_dict):
    global email_url  # Declare email_url as a global variable
    filepath = filedialog.askopenfilename(
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if filepath:
        try:
            with open(filepath, "r") as file:
                config = {}
                exec(file.read(), {}, config)

                # Extract cookies, headers, email settings, and email URL
                cookies = config.get("cookies", {})
                headers = config.get("headers", {})
                email_settings = config.get("email_settings", {})
                email_url = config.get("email_url", None)  # Extract email_url

                if not email_url:
                    raise ValueError("Missing 'email_url' in configuration file.")

                # Update the GUI fields
                cookies_text.delete("1.0", tk.END)
                cookies_text.insert("1.0", str(cookies))

                headers_text.delete("1.0", tk.END)
                headers_text.insert("1.0", str(headers))

                email_settings_dict.clear()
                email_settings_dict.update(email_settings)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")

    # Validate inputs after loading config
    validate_inputs()

async def send_emails_to_list(cookies, headers, html_content, debug_text, root, email_settings):
    try:
        # Access the global list of valid emails
        total_emails = len(valid_emails_global)
        if total_emails == 0:
            raise ValueError("No valid emails to process.")

        # Use the dynamically loaded email_url
        global email_url  # Ensure email_url is accessible
        if not email_url:
            raise ValueError("Email URL not loaded. Please load the configuration.")

        update_debug_window(debug_text, "", "", "", "Processing", f"[{total_emails}] Emails ...", "info")

        for i, email in enumerate(valid_emails_global, start=1):
            pause_event.wait()

            response = await asyncio.to_thread(send_email, email_url, cookies, headers, html_content, email, email_settings)

            if isinstance(response, str):
                update_debug_window(debug_text, i, total_emails, email, "Failed", response, "error")
            elif response.status_code == 200:
                update_debug_window(debug_text, i, total_emails, email, "Success", "200", "success")
                with open("emails_working.txt", "a") as success_file:
                    success_file.write(f"{email}\n")
            else:
                try:
                    response_json = response.json()
                    failure_message = response_json.get("message", "Unknown Error")
                    if ": " in failure_message:
                        failure_message = failure_message.split(": ", 1)[-1]
                except:
                    failure_message = response.text or "Unknown Error"

                update_debug_window(
                    debug_text,
                    i,
                    total_emails,
                    email,
                    "Failed",
                    f"{response.status_code} | {failure_message}",
                    "error"
                )

            root.update_idletasks()
        update_debug_window(debug_text, "", "", "", "sending", f"[{total_emails}] Emails finished...opening txt valid emails file ", "info")
    except ValueError as ve:
        messagebox.showerror("Error", str(ve))
    except Exception as e:
        messagebox.showerror("Error", f"Failed to process file: {e}")

# Function to Dynamically Update the Valid Count
def update_valid_count(count):
    valid_label.config(text=f"Valid: {count}")

def update_debug_window(debug_text, index, total, email, status, details, tag="info"):
    try:
        # Convert `total` to an integer if it's not already
        total = int(total)
    except ValueError:
        total = 0  # Default to 0 if conversion fails

    # Format the message with index, total, email, status, and details
    if total > 0:
        formatted_message = f"{index}/{total} {email} | {status} | {details}\n"
    else:
        formatted_message = f"{status} | {details}\n"

    # Configure tag styles
    debug_text.tag_configure("success", foreground="green", font=("Consolas", 10, "bold"))  # Smaller font size
    debug_text.tag_configure("error", foreground="red", font=("Consolas", 10, "bold"))  # Smaller font size
    debug_text.tag_configure("info", foreground="#B8860B", font=("Consolas", 10, "bold"))  # Dark yellow

    # Insert formatted message into debug text area
    debug_text.insert(tk.END, formatted_message, tag)
    debug_text.see(tk.END)  # Auto-scroll to the end

    # Update the valid count if the email was successful
    if tag == "success":
        current_count = int(valid_label.cget("text").replace("Valid:", "").strip() or 0)
        update_valid_count(current_count + 1)

# Function to Handle Sending Emails
def handle_send():
    global pause_button_state, pause_event

    if pause_button_state == "SEND":
        # Clear the debug log when SEND is pressed
        debug_text.delete("1.0", tk.END)

        # Change button to PAUSE mode
        pause_button_state = "PAUSE"
        send_button.config(text="PAUSE", bg="orange")

        # Start processing
        cookies = eval(cookies_text.get("1.0", tk.END).strip())
        headers = eval(headers_text.get("1.0", tk.END).strip())
        html_content = html_text.get("1.0", tk.END).strip()
        filepath = file_entry.get().strip()

        if not filepath:
            messagebox.showerror("Error", "Please select an email list file.")
            return

        # Clear the old working emails file
        with open("emails_working.txt", "w") as file:
            pass  # Clear the file by writing nothing

        # Reset Counter and Set Status to Running
        update_status(running=True)

        # Set the pause_event to allow processing
        pause_event.set()

        # Run the email-sending process in a separate thread
        thread = threading.Thread(
            target=lambda: asyncio.run(
                send_emails_to_list(
                    cookies, headers, html_content, debug_text, root, global_email_settings
                )
            )
        )
        thread.start()

        # Monitor the thread
        monitor_thread_and_open_file(thread)

    elif pause_button_state == "PAUSE":
        # Pause the process and update status to PAUSED
        pause_button_state = "RESUME"
        send_button.config(text="RESUME", bg="green")
        update_status(paused=True)

        # Clear the pause event to pause the thread
        pause_event.clear()

    elif pause_button_state == "RESUME":
        # Resume the process and update status to RUNNING
        pause_button_state = "PAUSE"
        send_button.config(text="PAUSE", bg="orange")
        update_status(running=True)

        # Set the pause event to resume the thread
        pause_event.set()
def validate_inputs():
    # Check if there are valid emails
    filepath = file_entry.get().strip()
    has_valid_emails = False
    if filepath and os.path.exists(filepath):
        try:
            with open(filepath, "r") as file:
                email_list = [line.strip() for line in file if is_valid_email(line.strip())]
                has_valid_emails = len(email_list) > 0
        except:
            pass

    # Check if cookies and headers are provided
    has_valid_config = cookies_text.get("1.0", tk.END).strip() and headers_text.get("1.0", tk.END).strip()

    # Enable or disable the SEND button based on the validation
    if has_valid_emails and has_valid_config:
        send_button.config(state="normal", bg="#39FF14")  # Active button with white text
    else:
        send_button.config(state="disabled", bg="gray")  # Disabled button with white text

def monitor_thread_and_open_file(thread):
    global pause_button_state

    if thread.is_alive():
        # Check again after 100ms
        root.after(100, lambda: monitor_thread_and_open_file(thread))
    else:
        # Reset the button to SEND mode
        pause_button_state = "SEND"
        send_button.config(text="SEND", bg="#39FF14")

        # Once the thread finishes, open the working emails file
        try:
            file_path = "emails_working.txt"
            if os.path.exists(file_path):
                os.startfile(file_path)  # Opens the file with the default text editor
            else:
                messagebox.showerror("Error", "File not found: emails_working.txt")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open the file: {e}")
        
        update_status(running=False)

def update_status(running=True, paused=False):
    if paused:
        # Set status to PAUSED
        status_label.config(text="PAUSED", fg="orange", font=("Consolas", 14, "bold"))  # Update text to orange
        status_frame.config(highlightbackground="orange")  # Update frame border to orange
    elif running:
        # Set status to RUNNING
        status_label.config(text="RUNNING", fg="yellow", font=("Consolas", 14, "bold"))  # Update text to yellow
        status_frame.config(highlightbackground="yellow")  # Update frame border to yellow
    else:
        # Set status to FINISHED
        status_label.config(text="FINISHED", fg="green", font=("Consolas", 14, "bold"))  # Update text to green
        status_frame.config(highlightbackground="green")  # Update frame border to green

def update_ram_usage():
    # Get the current process
    process = psutil.Process(os.getpid())

    # Get the memory usage of the current process in GB
    ram_usage = process.memory_info().rss / (1024 ** 3)  # Convert to GB

    # Update the RAM usage label dynamically
    ram_label.config(text=f"RAM: {ram_usage:.2f} GB")

    # Schedule the function to run again after 1000ms (1 second)
    root.after(1000, update_ram_usage)


# GUI setup
root = tk.Tk()
root.title("Mr_Mailer v 1.0")
root.geometry("800x500")  # Default size
root.minsize(850, 600)  # Minimum fixed size

# Center the window on the screen
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = 860
window_height = 580
x_cordinate = int((screen_width / 2) - (window_width / 2))
y_cordinate = int((screen_height / 2) - (window_height / 2))
root.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

root.configure(bg="#0D0D0D")

# Configure the root grid for responsiveness
root.rowconfigure(1, weight=1)
root.rowconfigure(2, weight=1)
root.rowconfigure(4, weight=1)
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)

title_label = tk.Label(root, text="MR MAILER", font=("Consolas", 18, "bold"), fg="#39FF14", bg="#0D0D0D")
title_label.grid(row=0, column=0, columnspan=2, pady=10, sticky="n")

# Cookies and Headers Section
cookies_headers_frame = tk.Frame(root, bg="#0D0D0D")
cookies_headers_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=5, sticky="nsew")
cookies_headers_frame.columnconfigure(1, weight=1)

# Cookies Row
cookies_label = tk.Label(cookies_headers_frame, text="COOKIES:", font=("Consolas", 12,"bold"), fg="#39FF14", bg="#0D0D0D", anchor="w")
cookies_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
cookies_text = tk.Text(cookies_headers_frame, height=3, font=("Consolas", 7), bg="#1A1A1A", fg="#39FF14", insertbackground="#39FF14", wrap=tk.WORD, relief="flat")
cookies_text.grid(row=0, column=1, sticky="nsew", padx=10, pady=5)

# Headers Row
headers_label = tk.Label(cookies_headers_frame, text="HEADERS:", font=("Consolas", 12,"bold"), fg="#39FF14", bg="#0D0D0D", anchor="w")
headers_label.grid(row=1, column=0, sticky="w", padx=10, pady=5)
headers_text = tk.Text(cookies_headers_frame, height=3, font=("Consolas", 7), bg="#1A1A1A", fg="#39FF14", insertbackground="#39FF14", wrap=tk.WORD, relief="flat")
headers_text.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)

# HTML Content Section
# HTML Content Section (Styled with Light Gray Background)
html_frame = tk.Frame(root, bg="#1E1E1E")  # Lighter gray for the frame
html_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=5, sticky="nsew")
html_frame.columnconfigure(0, weight=1)

# HTML Label
html_label = tk.Label(
    html_frame, 
    text="MESSAGE", 
    font=("Consolas", 12, "bold"), 
    fg="#39FF14", 
    bg="#1E1E1E",  # Match the lighter gray
    anchor="center"
)
html_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)

# HTML Text Area
html_text = tk.Text(
    html_frame,
    height=5,
    font=("Consolas", 10, "bold"),
    bg="#F5F5F5",  # Light gray background for the text area
    fg="black",  # Green text to match the hacker theme
    wrap=tk.WORD,
    relief="flat"
)
html_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

# File Upload Section
# File Upload Section
file_frame = tk.Frame(root, bg="#0D0D0D")
file_frame.grid(row=3, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
file_frame.columnconfigure(1, weight=1)

file_label = tk.Label(file_frame, text="EMAILS LIST:", font=("Consolas", 12, "bold"), fg="#39FF14", bg="#0D0D0D", anchor="w")
file_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)

file_entry = tk.Entry(file_frame, font=("Consolas", 8), bg="#1A1A1A", fg="#39FF14", insertbackground="#39FF14", relief="flat")
file_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=5)

# Adjusting the Browse Button Size
file_button = tk.Button(
    file_frame,
    text="BROWSE",
    font=("Consolas", 9, "bold"),  # Bold text
    bg="#39FF14",
    fg="#0D0D0D",
    relief="flat",
    width=8,  # Smaller width
    command=lambda: handle_file_upload(file_entry)
)
file_button.grid(row=0, column=2, padx=10, pady=5)

# Debug Output Section
# Debug Output Section (Full Width with Light Gray Background)
debug_frame = tk.Frame(root, bg="#1E1E1E")  # Lighter gray for the frame
debug_frame.grid(row=4, column=0, columnspan=2, padx=20, pady=5, sticky="nsew")
debug_frame.rowconfigure(0, weight=1)
debug_frame.columnconfigure(0, weight=1)

# Debug Label
debug_label = tk.Label(
    debug_frame, 
    text="LOGS", 
    font=("Consolas", 13, "bold"), 
    fg="#39FF14", 
    bg="#1E1E1E",  # Match the lighter gray
    anchor="center"
)
debug_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)

# Debug Text Area
debug_text = tk.Text(
    debug_frame,
    height=5,
    font=("Consolas", 8, "bold"),
    bg="#F5F5F5",  # Light gray background for the text area
    fg="black",  # Green text to match the hacker theme  # Green cursor
    wrap=tk.WORD,
    relief="flat"
)
debug_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

# Buttons Section (Full Width)
buttons_frame = tk.Frame(root, bg="#0D0D0D")
buttons_frame.grid(row=5, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
buttons_frame.columnconfigure(0, weight=1)
buttons_frame.columnconfigure(1, weight=1)

config_button = tk.Button(buttons_frame, text="LOAD CONFIG", font=("Consolas", 12, "bold"), bg="#39FF14", fg="#0D0D0D", relief="flat", command=lambda: load_config(cookies_text, headers_text, global_email_settings))
config_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

send_button = tk.Button(buttons_frame, text="SEND", font=("Consolas", 12, "bold"), bg="#39FF14", fg="#0D0D0D", relief="flat", command=handle_send)
send_button.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

# Status Section
# Status Section
status_frame = tk.Frame(root, bg="#0D0D0D")
status_frame.grid(row=6, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
status_frame.columnconfigure(0, weight=1)  # Left side (for Valid label)
status_frame.columnconfigure(1, weight=1)  # Center (RAM Label)
status_frame.columnconfigure(2, weight=1)  # Right side (Status Label)

# Valid Label (on the left)
valid_label = tk.Label(
    status_frame,
    text="",
    font=("Consolas", 13, "bold"),
    fg="#39FF14",
    bg="#0D0D0D",
    anchor="w"  # Left-aligned
)
valid_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)

# RAM Usage Label (in the center)
ram_label = tk.Label(
    status_frame,
    text="RAM: Calculating...",
    font=("Consolas", 11, "bold"),
    fg="white",
    bg="#0D0D0D",
    anchor="center"  # Center-aligned
)
ram_label.grid(row=0, column=1, sticky="nsew", padx=10, pady=5)

# Status Label (on the right)
status_label = tk.Label(
    status_frame,
    text="",
    font=("Consolas", 13, "bold"),  # Bold text for consistency
    fg="#39FF14",
    bg="#0D0D0D",
    anchor="e"  # Right-aligned
)
status_label.grid(row=0, column=2, sticky="e", padx=10, pady=5)
# Perform initial validation to disable SEND button by default
# Footer Section
footer_frame = tk.Frame(root, bg="#0D0D0D")
footer_frame.grid(row=7, column=0, columnspan=2, sticky="ew")

footer_label = tk.Label(
    footer_frame,
    text=" Made by Mrbadr1",
    font=("Consolas", 10, "italic"),
    fg="gray",
    bg="#0D0D0D",
    anchor="w"  # Left-aligned (extreme left)
)
footer_label.pack(side="left", fill="both")  # Pack to ensure it stays at the left

validate_inputs()
update_ram_usage()
root.mainloop()
