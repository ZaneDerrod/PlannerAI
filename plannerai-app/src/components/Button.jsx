// src/components/Button.jsx
export default function Button({ children, onClick, type = "button" }) {
    return (
      <button
        type={type}
        onClick={onClick}
        className="rounded-lg bg-blue-600 px-6 py-3 text-white font-medium
                   hover:bg-blue-700 active:scale-95 transition"
      >
        {children}
      </button>
    );
  }
  