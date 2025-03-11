from flask import Flask, request, jsonify
import os
import re
from tkinter import Tk, messagebox, Label, BooleanVar, Toplevel, Checkbutton, IntVar, Button, Text, Scrollbar, END, Frame, Listbox, MULTIPLE
import string
import time
import threading

app = Flask(__name__)

def clean_filename(filename):
    # Remove numeric suffixes like "(1)" or "(2)" and trim any extra whitespace
    return re.sub(r"\s*\(\d+\)\s*", "", filename).strip()

def get_all_drives():
    """
    Returns a list of all available drives on the system.
    """
    drives = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"  # Windows drive path
        if os.path.exists(drive):
            drives.append(drive)
    print(f"Detected drives: {drives}")
    return drives

def center_window(window, width=400, height=300):
    """
    Centers a given Tkinter window on the screen.
    """
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

def select_drives(drives):
    """
    Displays a popup to let the user select which drives to search.
    Returns the list of selected drives.
    """
    selected_drives = []

    def on_submit():
        # Get selected drives and close the popup
        for i, drive in enumerate(drives):
            if vars[i].get() == 1:
                selected_drives.append(drive)
        root.destroy()

    root = Tk()
    root.title("Select Drives")
    root.attributes("-topmost", True)  # Keep window on top
    center_window(root, 300, 400)  # Center the window

    vars = []
    for drive in drives:
        var = IntVar()
        vars.append(var)
        Checkbutton(root, text=drive, variable=var).pack(anchor='w')

    Button(root, text="Submit", command=on_submit).pack()
    root.mainloop()
    return selected_drives

def delete_files_gui(files):
    """
    Displays a GUI to allow the user to select files to delete.
    Includes an option to keep all files without deletion.
    """
    def on_delete():
        selected_indices = listbox.curselection()
        selected_files = [files[i] for i in selected_indices]

        if not selected_files:
            messagebox.showinfo("No Selection", "No files selected for deletion.")
            return

        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete the selected {len(selected_files)} file(s)?")
        if confirm:
            for file in selected_files:
                try:
                    os.remove(file)
                    log.insert(END, f"Deleted: {file}\n")
                except Exception as e:
                    log.insert(END, f"Error deleting {file}: {e}\n")
            log.insert(END, "\nDeletion complete.\n")
            log.update()

            # Close the popup once deletions are complete
            root.destroy()

    def on_keep_all():
        messagebox.showinfo("Keep All Files", "No files were deleted. Keeping all files.")
        root.destroy()  # Close the popup

    root = Tk()
    root.title("Delete Duplicate Files")
    root.attributes("-topmost", True)  # Keep window on top
    center_window(root, 500, 400)

    frame = Frame(root)
    frame.pack(fill="both", expand=True)

    scrollbar = Scrollbar(frame)
    scrollbar.pack(side="right", fill="y")

    listbox = Listbox(frame, selectmode=MULTIPLE, yscrollcommand=scrollbar.set)
    listbox.pack(fill="both", expand=True)
    scrollbar.config(command=listbox.yview)

    for file in files:
        listbox.insert(END, file)

    button_frame = Frame(root)
    button_frame.pack(fill="x")

    Button(button_frame, text="Delete Selected", command=on_delete).pack(side="left", padx=10, pady=5)
    Button(button_frame, text="Keep All Files", command=on_keep_all).pack(side="left", padx=10, pady=5)

    log = Text(root, height=5, wrap="word")
    log.pack(fill="x", expand=False)

    root.mainloop()

import os
import hashlib
def generate_file_hash(file_path):
    """Generate SHA256 hash for a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read file in chunks to avoid memory overload for large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
    except Exception as e:
        print(f"Error generating hash for {file_path}: {e}")
        return None
    return sha256_hash.hexdigest()


# Function to display a popup with checkboxes to choose files to delete
def prompt_user_to_delete_duplicates(duplicates):
    """
    Displays a GUI to allow the user to select duplicate files to delete.
    Includes an option to keep all files without deletion.
    """
    def on_delete():
        # Get selected indices and corresponding file paths
        selected_indices = listbox.curselection()
        selected_files = [duplicates[i] for i in selected_indices]

        if not selected_files:
            messagebox.showinfo("No Selection", "No files selected for deletion.")
            return

        # Confirm deletion with the user
        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete the selected {len(selected_files)} file(s)?")
        if confirm:
            for file in selected_files:
                try:
                    os.remove(file)
                    log.insert(END, f"Deleted: {file}\n")
                except Exception as e:
                    log.insert(END, f"Error deleting {file}: {e}\n")
            log.insert(END, "\nDeletion complete.\n")
            log.update()

            # Close the window after deletion
            root.destroy()

    def on_keep_all():
        # Notify the user and close the window
        messagebox.showinfo("Keep All Files", "No files were deleted. Keeping all files.")
        root.destroy()

    # Set up the Tkinter root window
    root = Tk()
    root.title("Duplicate Files Found with Changed Names")
    root.attributes("-topmost", True)  # Keep window on top
    root.geometry("500x400")

    # Create the main frame
    frame = Frame(root)
    frame.pack(fill="both", expand=True)

    # Add a scrollbar
    scrollbar = Scrollbar(frame)
    scrollbar.pack(side="right", fill="y")

    # Add a listbox for displaying duplicate files
    listbox = Listbox(frame, selectmode=MULTIPLE, yscrollcommand=scrollbar.set)
    listbox.pack(fill="both", expand=True)
    scrollbar.config(command=listbox.yview)

    # Populate the listbox with duplicate file paths
    for file in duplicates:
        listbox.insert(END, file)

    # Create a frame for buttons
    button_frame = Frame(root)
    button_frame.pack(fill="x")

    # Add buttons for deletion and keeping all files
    Button(button_frame, text="Delete Selected", command=on_delete).pack(side="left", padx=10, pady=5)
    Button(button_frame, text="Keep All Files", command=on_keep_all).pack(side="left", padx=10, pady=5)

    # Add a log area for deletion status
    log = Text(root, height=5, wrap="word")
    log.pack(fill="x", expand=False)

    # Run the Tkinter event loop
    root.mainloop()
    

def search_with_gui(filename, downloads_folder, selected_drives, etags_file_path, etag):
    """
    Displays a GUI with a log of the search process while performing the system-wide search.
    """
    root = Tk()
    root.title("Searching Files")
    root.attributes("-topmost", True)  # Keep window on top
    center_window(root, 500, 400)

    frame = Frame(root)
    frame.pack(fill='both', expand=True)

    scrollbar = Scrollbar(frame)
    scrollbar.pack(side="right", fill="y")

    text_widget = Text(frame, wrap="word", yscrollcommand=scrollbar.set)
    text_widget.pack(fill="both", expand=True)
    scrollbar.config(command=text_widget.yview)

    text_widget.insert(END, f"Starting search for: {filename}\n\n")
    text_widget.update()

    def perform_search():
        start_time = time.time()
        matching_paths = []
        for drive in selected_drives:
            for root_dir, dirs, files in os.walk(drive):
                # Log the current directory being searched
                log_message = f"Searching in: {root_dir}\n"
                text_widget.insert(END, log_message)
                text_widget.see(END)  # Auto-scroll to the end
                text_widget.update()

                # Skip the Downloads folder
                if downloads_folder in root_dir:
                    continue

                for file in files:
                    if clean_filename(file) == filename:
                        matching_paths.append(os.path.join(root_dir, file))

        end_time = time.time()
        search_time = end_time - start_time

        # Display search results
        if matching_paths:
            result_message = f"\nSearch completed in {search_time:.2f} seconds.\nFound files:\n" + "\n".join(matching_paths) + "\n"
        else:
            result_message = f"\nSearch completed in {search_time:.2f} seconds.\nNo files found.\n"

        text_widget.insert(END, result_message)
        text_widget.see(END)
        text_widget.update()

        if matching_paths:
            delete_files_gui(matching_paths)
        
        else:
            try:
                with open(etags_file_path, "r") as etags_file:
                    lines = etags_file.readlines()

                    for line in lines:
                        # Check if the etag in the Etags file matches the one provided
                        if etag in line:
                            # Extract the folder path if etag matches
                            parts = line.split(", ")
                            if len(parts) > 1:
                                folder_path_from_etag = parts[1].strip()  # Get the folder path
                                break
                
            except Exception as e:
                text_widget.insert(END, f"\nError reading Etags file: {str(e)}\n")
                text_widget.update()
                
            # Extract the directory from the full file path
            folder_path = os.path.dirname(folder_path_from_etag)
            print(f"Trimmed folder path: {folder_path}")
            
            file_path = os.path.join(folder_path, filename)  # Combine folder path and filename
            downloaded_file_hash = generate_file_hash(file_path)
            print(downloaded_file_hash)
            
            duplicates = []  # To store duplicate file paths
            duplicate_found = False
            for file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file)
                print(file_path)
                if os.path.isfile(file_path) and file != filename:  # Ensure it's a file, not a directory
                    file_hash = generate_file_hash(file_path)
                    print(file_hash)
                    if file_hash == downloaded_file_hash:
                            print(f"Duplicate found: {file_path}")
                            duplicates.append(file_path)
                            duplicate_found = True
            
            if duplicate_found:
                prompt_user_to_delete_duplicates(duplicates)
            else:
                print("No duplicate found.")
        

    threading.Thread(target=perform_search).start()
    root.mainloop()
    
    

@app.route("/check-duplicate", methods=["POST"])
def check_duplicate():
    data = request.get_json()
    filename = os.path.basename(data.get("filename"))  # Get only the base name
    etag = data.get("etag")  # Retrieve the ETag from the request
    downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
    etags_file_path = os.path.join(downloads_folder, "Etags")

    # Ensure the Etags file exists; create it if necessary
    if not os.path.exists(etags_file_path):
        try:
            with open(etags_file_path, "w") as etags_file:
                etags_file.write("")  # Create an empty file
            print(f"Etags file created at {etags_file_path}.")
        except Exception as e:
            print(f"Error creating Etags file: {e}")

    # Clean the filename to remove any suffixes like "(1)"
    cleaned_filename = clean_filename(filename)
    name_without_extension = os.path.splitext(cleaned_filename)[0]
    print(f"Checking for filename: {filename} (cleaned: {cleaned_filename})")

    duplicate_path = None

    # Check if any file in Downloads folder has the same base name
    for existing_file in os.listdir(downloads_folder):
        if name_without_extension == os.path.splitext(clean_filename(existing_file))[0]:
            duplicate_path = os.path.join(downloads_folder, existing_file)
            break

    if duplicate_path:
        print(f"Duplicate found at: {duplicate_path}")
        return jsonify({"isDuplicate": True, "duplicatePath": duplicate_path})

    print("No duplicate found in Downloads. Notifying extension to start download.")
    response = {"isDuplicate": False, "message": "File not found in Downloads. Begin download."}

    from threading import Thread

    def popup_logic():
        time.sleep(1)
        root = Tk()
        root.attributes("-topmost", True)
        root.withdraw()
        search_choice = messagebox.askyesno(
            "Search Entire System",
            "File not found in Downloads. File started downloading.\nWould you like to search the entire system?"
        )
        root.destroy()

        if search_choice:
            all_drives = get_all_drives()
            selected_drives = select_drives(all_drives)
            if selected_drives:
                search_with_gui(cleaned_filename, downloads_folder, selected_drives, etags_file_path, etag)

    Thread(target=popup_logic).start()
    return jsonify(response), 200


@app.route("/save-file-path", methods=["POST"])
def store_filepath():
    data = request.get_json()
    filepath = data.get("savedPath")  # The path where the file was saved
    filename = data.get("filename")  # Filename to store
    etag = data.get("etag")  # ETag for the file
    print(filename)
    print(etag)

    # Validate the filepath
    if not filepath or not isinstance(filepath, str):
        return jsonify({"success": False, "message": "Invalid or missing filepath"}), 400

    etags_file_path = os.path.join(os.path.expanduser("~"), "Downloads", "Etags")

    
    # Write the new entry to the Etags file without checking or updating
    try:
        with open(etags_file_path, "a") as etags_file:  # Open in append mode
            etags_file.write(f"{filename}: {etag}, {filepath}\n")
            print(f"Added new entry for {filename}.")
    except Exception as e:
        print(f"Error writing ETag to file: {e}")
        return jsonify({"success": False, "message": "Failed to write to Etags file"}), 500


    print(f"Filepath stored successfully for {filename}.")
    return jsonify({"success": True, "message": "Filepath stored successfully"}), 200




if __name__ == "__main__":
    app.run(port=5000)
