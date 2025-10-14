/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./src/**/*.{js,jsx,ts,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'maroon': '#7A0019',
                'gold': '#FFCC33',
                'dark-gray': '#2B2B2B',
                'message-bg': '#E8E8E8',
            },
            animation: {
                'fade-in': 'fadeIn 0.7s ease-in-out',
                'fade-out': 'fadeOut 0.7s ease-in-out',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                fadeOut: {
                    '0%': { opacity: '1' },
                    '100%': { opacity: '0' },
                },
            },
        },
    },
    plugins: [],
}
