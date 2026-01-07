import React, { useEffect } from 'react';

interface ImageModalProps {
  imageUrl: string;
  onClose: () => void;
}

export const ImageModal: React.FC<ImageModalProps> = ({ imageUrl, onClose }) => {
  useEffect(() => {
    const handleEsc = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleEsc);
    return () => {
      window.removeEventListener('keydown', handleEsc);
    };
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-75 flex justify-center items-center z-50 p-4 animate-fade-in"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <button
        className="absolute top-4 right-4 text-white text-4xl leading-none font-bold hover:text-slate-300 transition"
        onClick={onClose}
        aria-label="Close image view"
      >
        &times;
      </button>
      <div
        className="relative max-w-full max-h-full"
        onClick={(e) => e.stopPropagation()} // Prevent closing when clicking the image itself
      >
        <img
          src={imageUrl}
          alt="Zoomed product view"
          className="max-w-full max-h-[90vh] object-contain rounded-lg shadow-2xl"
        />
      </div>
    </div>
  );
};
