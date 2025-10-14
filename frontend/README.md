# GopherGPT - University of Minnesota AI Chat Interface

A beautiful React chat interface for GopherGPT with smooth transitions and University of Minnesota branding.

## Features

- **Three-Page Interface**: Landing page, transition page, and chat interface
- **Smooth Transitions**: Fade effects between pages with 700ms duration
- **University Branding**: Minnesota M logo, maroon and gold colors
- **Gradient Borders**: Beautiful maroon-to-gold gradient borders on input and messages
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Chat**: Backend integration with loading states and error handling
- **Keyboard Support**: Enter key to send messages

## Design Specifications

### Colors
- **Maroon**: #7A0019
- **Gold**: #FFCC33
- **Background**: #2B2B2B (dark gray)
- **Message Background**: #E8E8E8

### Pages
1. **Landing Page**: Welcome text, Goldy mascot, input box
2. **Transition Page**: Faded M logo, input box
3. **Chat Interface**: Messages, avatars, persistent input

## Installation

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm start
   ```

3. **Open in Browser**
   Navigate to `http://localhost:3000`

## Backend Integration

The app expects a backend server running on `http://localhost:8000` with the following endpoint:

### POST /chat
- **Request Body**: `{ "message": "user text" }`
- **Response**: `{ "response": "bot reply" }`

### Example Backend (Python Flask)
```python
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    
    # Your AI logic here
    response = f"Hello! You said: {user_message}"
    
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(port=8000, debug=True)
```

## Project Structure

```
src/
├── App.js          # Main application component
├── App.css         # Custom styles and animations
├── index.js        # React entry point
└── index.css       # Tailwind CSS imports and global styles
```

## Technologies Used

- **React 18** with hooks (useState, useEffect, useRef)
- **Tailwind CSS** for styling
- **Lucide React** for icons
- **Custom CSS** for gradient borders and animations

## Customization

### Colors
Edit `tailwind.config.js` to modify the color scheme:
```javascript
colors: {
  'maroon': '#7A0019',
  'gold': '#FFCC33',
  'dark-gray': '#2B2B2B',
  'message-bg': '#E8E8E8',
}
```

### Backend URL
Change the API endpoint in `App.js`:
```javascript
const response = await fetch('http://localhost:8000/chat', {
  // ... fetch options
});
```

## Production Build

```bash
npm run build
```

This creates an optimized production build in the `build` folder.

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge

## License

This project is created for the University of Minnesota GopherGPT initiative.
