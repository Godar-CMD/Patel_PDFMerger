import os
import sys
import json
import requests
from tkinter import *
from tkinter import ttk, filedialog, messagebox, simpledialog
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
import img2pdf
from PIL import Image
import fitz  # PyMuPDF
import tempfile
from pathlib import Path

CURRENT_VERSION = "1.0.0"
UPDATE_URL = "https://api.github.com/repos/YOUR_USERNAME/PDF_Merger/releases/latest"  # Replace with your repository

class PDFMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"PDF Merger v{CURRENT_VERSION}")
        self.root.geometry("800x600")
        self.root.configure(bg="#ffffff")
        
        # Initialize variables
        self.selected_files = []
        self.current_feature = None
        self.temp_dir = tempfile.mkdtemp()
        self.setup_styles()
        self.create_interface()
        self.check_for_updates()
        
    def setup_styles(self):
        style = ttk.Style()
        
        # Feature buttons style (Merge, Split, etc.)
        style.configure(
            "Feature.TButton",
            padding=15,
            font=('Segoe UI', 12),
            background="#ffffff",
            borderwidth=2,
            relief="raised"
        )
        
        # Selected feature style
        style.configure(
            "Selected.TButton",
            padding=15,
            font=('Segoe UI', 12, 'bold'),
            background="#0078D4",
            foreground="white"
        )
        
        # Action buttons style
        style.configure(
            "Action.TButton",
            padding=12,
            font=('Segoe UI', 11, 'bold'),
            background="#0078D4",
            foreground="white"
        )
        
        # Hover effects
        style.map(
            "Feature.TButton",
            background=[("active", "#f0f0f0")]
        )
        
        style.map(
            "Action.TButton",
            background=[("active", "#106EBE")],
            foreground=[("active", "white")]
        )
    
    def create_interface(self):
        # Main container
        main_frame = Frame(self.root, bg="#ffffff")
        main_frame.pack(expand=True, fill='both', padx=30, pady=20)
        
        # Title
        title_label = Label(
            main_frame,
            text="PDF Merger",
            font=('Segoe UI', 24, 'bold'),
            fg="#1a1a1a",
            bg="#ffffff"
        )
        title_label.pack(pady=(0, 20))
        
        # Tools Frame
        tools_frame = ttk.LabelFrame(main_frame, text="PDF Tools", padding=10)
        tools_frame.pack(fill='x', pady=(0, 20))
        
        # Tool buttons in grid layout
        self.tools = {
            "Merge PDFs": self.select_merge,
            "Split PDF": self.select_split,
            "Convert to PDF": self.select_convert,
            "Compress PDF": self.select_compress,
            "Extract Images": self.select_extract,
            "Rotate Pages": self.select_rotate
        }
        
        self.tool_buttons = {}
        for i, (text, command) in enumerate(self.tools.items()):
            btn = ttk.Button(
                tools_frame,
                text=text,
                command=command,
                style="Feature.TButton",
                width=15
            )
            btn.grid(row=i//3, column=i%3, padx=5, pady=5, sticky='ew')
            self.tool_buttons[text] = btn
        
        # Configure grid columns to be equal width
        tools_frame.grid_columnconfigure(0, weight=1)
        tools_frame.grid_columnconfigure(1, weight=1)
        tools_frame.grid_columnconfigure(2, weight=1)
        
        # File Selection Frame
        self.action_frame = Frame(main_frame, bg="#ffffff", height=80)
        self.action_frame.pack(fill='x', pady=(0, 20))
        self.action_frame.pack_propagate(False)
        
        # Center the buttons in the frame
        self.button_container = Frame(self.action_frame, bg="#ffffff")
        self.button_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # File selection buttons (initially hidden)
        self.select_btn = Button(
            self.button_container,
            text="Select PDF",
            command=self.add_files,
            font=('Segoe UI', 12, 'bold'),
            fg='white',
            bg='#0078D4',
            activebackground='#106EBE',
            activeforeground='white',
            padx=20,
            pady=10,
            relief='raised',
            cursor='hand2'
        )
        
        self.remove_btn = Button(
            self.button_container,
            text="Remove Selected",
            command=self.remove_selected,
            font=('Segoe UI', 12, 'bold'),
            fg='white',
            bg='#0078D4',
            activebackground='#106EBE',
            activeforeground='white',
            padx=20,
            pady=10,
            relief='raised',
            cursor='hand2'
        )
        
        # Process Button Frame (for Merge, Split, etc.)
        self.process_frame = Frame(main_frame, bg="#ffffff", height=80)
        self.process_frame.pack(fill='x', pady=(0, 20))
        self.process_frame.pack_propagate(False)
        
        # Center the process button
        self.process_container = Frame(self.process_frame, bg="#ffffff")
        self.process_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Process button (initially hidden)
        self.process_btn = Button(
            self.process_container,
            text="Process",
            font=('Segoe UI', 12, 'bold'),
            fg='white',
            bg='#107C10',  # Green color for process button
            activebackground='#0B5C0B',
            activeforeground='white',
            padx=30,
            pady=10,
            relief='raised',
            cursor='hand2'
        )
        
        # Rotation options frame (for Rotate Pages feature)
        self.rotation_frame = Frame(main_frame, bg="#ffffff")
        self.rotation_var = StringVar(value="90")
        
        rotation_label = Label(
            self.rotation_frame,
            text="Rotation Angle:",
            font=('Segoe UI', 11),
            bg="#ffffff"
        )
        rotation_label.pack(side='left', padx=5)
        
        for angle in ["90", "180", "270"]:
            rb = Radiobutton(
                self.rotation_frame,
                text=f"{angle}°",
                value=angle,
                variable=self.rotation_var,
                font=('Segoe UI', 11),
                bg="#ffffff"
            )
            rb.pack(side='left', padx=5)
        
        # File List Frame
        self.list_frame = ttk.LabelFrame(main_frame, text="Selected Files", padding=10)
        self.list_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        # File list with scrollbar
        self.file_list = ttk.Treeview(
            self.list_frame,
            columns=("Name", "Type", "Size"),
            show="headings",
            selectmode="extended"
        )
        
        self.file_list.heading("Name", text="File Name")
        self.file_list.heading("Type", text="File Type")
        self.file_list.heading("Size", text="Size")
        
        # Set column widths
        self.file_list.column("Name", width=300)
        self.file_list.column("Type", width=100)
        self.file_list.column("Size", width=100)
        
        scrollbar = ttk.Scrollbar(self.list_frame, orient="vertical", command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=scrollbar.set)
        
        self.file_list.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Status bar
        self.status_label = Label(
            main_frame,
            text="Select a feature to begin",
            font=('Segoe UI', 10),
            fg="#666666",
            bg="#ffffff",
            anchor='w'
        )
        self.status_label.pack(fill='x', pady=(10, 0))
        
        # Initially hide file selection related widgets
        self.list_frame.pack_forget()
        self.action_frame.pack_forget()
        self.process_frame.pack_forget()
        self.rotation_frame.pack_forget()
    
    def select_feature(self, feature):
        # Reset previously selected feature
        if self.current_feature:
            self.tool_buttons[self.current_feature].configure(style="Feature.TButton")
        
        # Set new feature
        self.current_feature = feature
        self.tool_buttons[feature].configure(style="Selected.TButton")
        
        # Show file selection buttons
        self.action_frame.pack(fill='x', pady=(0, 20))
        self.list_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        # Update button text and visibility based on feature
        if feature == "Merge PDFs":
            self.select_btn.configure(text="Select PDFs")
            self.select_btn.pack(side='left', padx=10)
            self.remove_btn.pack(side='left', padx=10)
            self.process_btn.configure(text="Merge PDFs", command=self.merge_pdfs)
            self.process_frame.pack(fill='x', pady=(0, 20))
            self.process_btn.pack()
            self.rotation_frame.pack_forget()
            
        elif feature == "Split PDF":
            self.select_btn.configure(text="Select PDF")
            self.select_btn.pack(side='left', padx=10)
            self.remove_btn.pack_forget()
            self.process_btn.configure(text="Split PDF", command=self.split_pdf)
            self.process_frame.pack(fill='x', pady=(0, 20))
            self.process_btn.pack()
            self.rotation_frame.pack_forget()
            
        elif feature == "Convert to PDF":
            self.select_btn.configure(text="Select Images")
            self.select_btn.pack(side='left', padx=10)
            self.remove_btn.pack(side='left', padx=10)
            self.process_btn.configure(text="Convert to PDF", command=self.convert_to_pdf)
            self.process_frame.pack(fill='x', pady=(0, 20))
            self.process_btn.pack()
            self.rotation_frame.pack_forget()
            
        elif feature == "Compress PDF":
            self.select_btn.configure(text="Select PDF")
            self.select_btn.pack(side='left', padx=10)
            self.remove_btn.pack_forget()
            self.process_btn.configure(text="Compress PDF", command=self.compress_pdf)
            self.process_frame.pack(fill='x', pady=(0, 20))
            self.process_btn.pack()
            self.rotation_frame.pack_forget()
            
        elif feature == "Extract Images":
            self.select_btn.configure(text="Select PDF")
            self.select_btn.pack(side='left', padx=10)
            self.remove_btn.pack_forget()
            self.process_btn.configure(text="Extract Images", command=self.extract_images)
            self.process_frame.pack(fill='x', pady=(0, 20))
            self.process_btn.pack()
            self.rotation_frame.pack_forget()
            
        elif feature == "Rotate Pages":
            self.select_btn.configure(text="Select PDF")
            self.select_btn.pack(side='left', padx=10)
            self.remove_btn.pack_forget()
            self.process_btn.configure(text="Rotate Pages", command=self.rotate_pages)
            self.process_frame.pack(fill='x', pady=(0, 20))
            self.process_btn.pack()
            self.rotation_frame.pack(fill='x', pady=(0, 20))
        
        self.update_status(f"Selected feature: {feature}")
    
    def select_merge(self):
        self.select_feature("Merge PDFs")
    
    def select_split(self):
        self.select_feature("Split PDF")
    
    def select_convert(self):
        self.select_feature("Convert to PDF")
    
    def select_compress(self):
        self.select_feature("Compress PDF")
    
    def select_extract(self):
        self.select_feature("Extract Images")
    
    def select_rotate(self):
        self.select_feature("Rotate Pages")
    
    def add_files(self):
        if not self.current_feature:
            self.update_status("Please select a feature first")
            return
            
        if self.current_feature == "Merge PDFs":
            files = filedialog.askopenfilenames(
                title="Select PDF files to merge",
                filetypes=[("PDF files", "*.pdf")]
            )
        elif self.current_feature == "Split PDF":
            files = filedialog.askopenfilename(
                title="Select a PDF file to split",
                filetypes=[("PDF files", "*.pdf")]
            )
            if files:  # Convert single file to tuple
                files = (files,)
        elif self.current_feature == "Convert to PDF":
            files = filedialog.askopenfilenames(
                title="Select images to convert",
                filetypes=[
                    ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff"),
                    ("All files", "*.*")
                ]
            )
        elif self.current_feature == "Compress PDF":
            files = filedialog.askopenfilename(
                title="Select a PDF file to compress",
                filetypes=[("PDF files", "*.pdf")]
            )
            if files:
                files = (files,)
        elif self.current_feature == "Extract Images":
            files = filedialog.askopenfilename(
                title="Select a PDF file to extract images",
                filetypes=[("PDF files", "*.pdf")]
            )
            if files:
                files = (files,)
        elif self.current_feature == "Rotate Pages":
            files = filedialog.askopenfilename(
                title="Select a PDF file to rotate",
                filetypes=[("PDF files", "*.pdf")]
            )
            if files:
                files = (files,)
        
        for file in files:
            if file and file not in self.selected_files:
                self.selected_files.append(file)
                file_name = os.path.basename(file)
                file_ext = os.path.splitext(file)[1].upper()[1:]
                file_size = os.path.getsize(file)
                
                # Show size in KB or MB based on size
                if file_size > 1024*1024:
                    size_text = f"{file_size/(1024*1024):.1f} MB"
                else:
                    size_text = f"{file_size/1024:.1f} KB"
                
                self.file_list.insert("", "end", values=(file_name, file_ext, size_text))
        
        if files:
            self.update_status(f"Added {len(files) if isinstance(files, tuple) else 1} file(s)")
    
    def remove_selected(self):
        selected_items = self.file_list.selection()
        for item in selected_items:
            file_name = self.file_list.item(item)['values'][0]
            file_path = next(f for f in self.selected_files if os.path.basename(f) == file_name)
            self.selected_files.remove(file_path)
            self.file_list.delete(item)
        
        if selected_items:
            self.update_status(f"Removed {len(selected_items)} file(s)")
    
    def update_status(self, message):
        self.status_label.config(text=message)
        self.root.update()
        
    def merge_pdfs(self):
        if not self.selected_files:
            messagebox.showerror("Error", "Please select PDF files first")
            return
            
        try:
            save_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF Files", "*.pdf")],
                title="Save Merged PDF"
            )
            
            if save_path:
                merger = PdfMerger()
                for pdf in self.selected_files:
                    merger.append(pdf)
                merger.write(save_path)
                merger.close()
                self.update_status("PDFs merged successfully")
                messagebox.showinfo("Success", "PDFs merged successfully!")
        except Exception as e:
            self.update_status("Error occurred")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            
    def split_pdf(self):
        if not self.selected_files:
            messagebox.showerror("Error", "Please select a PDF file first")
            return
        
        if len(self.selected_files) > 1:
            messagebox.showerror("Error", "Please select only one PDF file")
            return
            
        try:
            pdf_path = self.selected_files[0]
            pdf = PdfReader(pdf_path)
            num_pages = len(pdf.pages)
            
            save_dir = filedialog.askdirectory(title="Select Output Directory")
            if not save_dir:
                return
                
            base_name = Path(pdf_path).stem
            
            for page_num in range(num_pages):
                pdf_writer = PdfWriter()
                pdf_writer.add_page(pdf.pages[page_num])
                
                output_path = os.path.join(save_dir, f"{base_name}_page_{page_num + 1}.pdf")
                with open(output_path, "wb") as output_file:
                    pdf_writer.write(output_file)
                    
            self.update_status(f"PDF split into {num_pages} pages")
            messagebox.showinfo("Success", f"PDF split into {num_pages} pages!")
        except Exception as e:
            self.update_status("Error occurred")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            
    def convert_to_pdf(self):
        if not self.selected_files:
            messagebox.showerror("Error", "Please select image files first")
            return
            
        try:
            save_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF Files", "*.pdf")],
                title="Save PDF"
            )
            
            if save_path:
                image_list = []
                for img_path in self.selected_files:
                    if Path(img_path).suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
                        with open(img_path, 'rb') as img_file:
                            image_list.append(img_file.read())
                
                if image_list:
                    with open(save_path, "wb") as pdf_file:
                        pdf_file.write(img2pdf.convert(image_list))
                    self.update_status("Images converted to PDF successfully")
                    messagebox.showinfo("Success", "Images converted to PDF successfully!")
                else:
                    messagebox.showerror("Error", "No valid image files selected")
        except Exception as e:
            self.update_status("Error occurred")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            
    def compress_pdf(self):
        if not self.selected_files:
            messagebox.showerror("Error", "Please select a PDF file first")
            return
            
        if len(self.selected_files) > 1:
            messagebox.showerror("Error", "Please select only one PDF file")
            return
            
        try:
            pdf_path = self.selected_files[0]
            doc = fitz.open(pdf_path)
            
            save_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF Files", "*.pdf")],
                title="Save Compressed PDF"
            )
            
            if save_path:
                doc.save(save_path, garbage=4, deflate=True, clean=True)
                doc.close()
                
                original_size = os.path.getsize(pdf_path)
                compressed_size = os.path.getsize(save_path)
                reduction = (original_size - compressed_size) / original_size * 100
                
                self.update_status(f"PDF compressed successfully ({reduction:.1f}% reduction)")
                messagebox.showinfo("Success", f"PDF compressed successfully!\nSize reduction: {reduction:.1f}%")
        except Exception as e:
            self.update_status("Error occurred")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            
    def extract_images(self):
        if not self.selected_files:
            messagebox.showerror("Error", "Please select a PDF file first")
            return
            
        if len(self.selected_files) > 1:
            messagebox.showerror("Error", "Please select only one PDF file")
            return
            
        try:
            pdf_path = self.selected_files[0]
            doc = fitz.open(pdf_path)
            
            save_dir = filedialog.askdirectory(title="Select Output Directory")
            if not save_dir:
                return
                
            image_count = 0
            for page_num in range(len(doc)):
                page = doc[page_num]
                images = page.get_images()
                
                for img_index, img in enumerate(images):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    image_ext = base_image["ext"]
                    image_path = os.path.join(save_dir, f"image_{page_num + 1}_{img_index + 1}.{image_ext}")
                    
                    with open(image_path, "wb") as image_file:
                        image_file.write(image_bytes)
                        image_count += 1
            
            doc.close()
            self.update_status(f"Extracted {image_count} images from PDF")
            messagebox.showinfo("Success", f"Extracted {image_count} images from PDF!")
        except Exception as e:
            self.update_status("Error occurred")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            
    def rotate_pages(self):
        if not self.selected_files:
            messagebox.showerror("Error", "Please select a PDF file first")
            return
            
        if len(self.selected_files) > 1:
            messagebox.showerror("Error", "Please select only one PDF file")
            return
            
        try:
            pdf_path = self.selected_files[0]
            doc = fitz.open(pdf_path)
            
            rotation = self.rotation_var.get()
            
            if rotation not in ["90", "180", "270"]:
                messagebox.showerror("Error", "Invalid rotation angle")
                return
                
            save_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF Files", "*.pdf")],
                title="Save Rotated PDF"
            )
            
            if save_path:
                for page in doc:
                    page.set_rotation(int(rotation))
                doc.save(save_path)
                doc.close()
                
                self.update_status("PDF rotated successfully")
                messagebox.showinfo("Success", "PDF rotated successfully!")
        except Exception as e:
            self.update_status("Error occurred")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            
    def check_for_updates(self):
        try:
            response = requests.get(UPDATE_URL)
            if response.status_code == 200:
                latest_version = response.json()["tag_name"].replace("v", "")
                if self._is_newer_version(latest_version):
                    if messagebox.askyesno("Update Available", 
                        f"A new version {latest_version} is available. Would you like to update?"):
                        self.download_update(response.json()["assets"][0]["browser_download_url"])
        except Exception as e:
            print(f"Failed to check for updates: {e}")
            
    def _is_newer_version(self, latest_version):
        current = [int(x) for x in CURRENT_VERSION.split(".")]
        latest = [int(x) for x in latest_version.split(".")]
        return latest > current
        
    def download_update(self, download_url):
        try:
            response = requests.get(download_url)
            if response.status_code == 200:
                update_file = "PDF_Merger_new.exe"
                with open(update_file, "wb") as f:
                    f.write(response.content)
                    
                # Create update batch script
                with open("update.bat", "w") as f:
                    f.write(f'''@echo off
                        timeout /t 2 /nobreak
                        move /y "{update_file}" "{sys.executable}"
                        start "" "{sys.executable}"
                        del "%~f0"
                        ''')
                
                os.system("start update.bat")
                self.root.quit()
        except Exception as e:
            messagebox.showerror("Update Failed", f"Failed to download update: {e}")

def main():
    root = Tk()
    app = PDFMergerApp(root)
    
    # Center window on screen
    window_width = 800
    window_height = 600
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width/2 - window_width/2)
    center_y = int(screen_height/2 - window_height/2)
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    
    root.mainloop()

if __name__ == '__main__':
    main()
