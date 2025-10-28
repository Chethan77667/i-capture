# iCapture - File Upload & Management System

A modern, responsive web application built with Flask for managing participant file uploads with admin and user dashboards.

## Features

### Admin Features
- **College Management**: Add and manage colleges
- **Participant Registration**: Register participants with college assignment
- **File Access**: View all participant files with filtering and search
- **Dashboard**: Comprehensive admin dashboard with statistics

### User Features
- **Secure Login**: Login using participant ID and phone number
- **File Upload**: Upload photos and videos with drag-and-drop support
- **File Viewing**: View uploaded files with grid/list options
- **File Management**: Filter by file type and search functionality

### Technical Features
- **Responsive Design**: Mobile-first design with beautiful animations
- **File Organization**: Automatic folder creation based on user ID
- **File Validation**: Type and size validation for uploads
- **Modern UI**: Gradient backgrounds, smooth transitions, and interactive elements

## Installation

1. **Clone or download the project files**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Access the application**:
   - Open your browser and go to `http://localhost:5000`
   - Default admin credentials: `admin` / `admin123`

## Usage

### Admin Login
1. Go to the home page and click "Admin Login"
2. Use credentials: `admin` / `admin123`
3. Add colleges and participants
4. View all participant files

### User Login
1. Go to the home page and click "Participant Login"
2. Use participant ID and phone number (set by admin)
3. Upload photos and videos
4. View uploaded files

## File Structure

```
icapture/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── admin_login.html
│   ├── admin_dashboard.html
│   ├── admin_files.html
│   ├── admin_participant_files.html
│   ├── user_login.html
│   ├── user_dashboard.html
│   └── view_files.html
├── static/              # Static assets
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── uploads/             # Uploaded files (created automatically)
```

## Database Models

- **College**: Stores college information
- **Participant**: Stores participant details linked to colleges
- **FileUpload**: Stores file metadata linked to participants
- **Admin**: Stores admin credentials

## File Upload System

- Files are organized in user-specific folders (`uploads/{participant_id}/`)
- Files are renamed as `p1.jpg`, `p2.mp4`, etc.
- Supports images (JPG, PNG, GIF) and videos (MP4, AVI, MOV)
- Maximum file size: 10MB

## Customization

### Styling
- Modify `static/css/style.css` for custom styling
- Colors, animations, and responsive breakpoints can be adjusted

### Functionality
- Add new file types in `app.py` upload validation
- Modify file size limits in the upload route
- Add new admin features by extending the dashboard

## Security Features

- Password hashing for admin accounts
- File type validation
- Secure filename handling
- Session management

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge

## Troubleshooting

1. **Port already in use**: Change the port in `app.py` (last line)
2. **File upload issues**: Check file permissions and disk space
3. **Database errors**: Delete `icapture.db` to reset the database

## License

This project is open source and available under the MIT License.
