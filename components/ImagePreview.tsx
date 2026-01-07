import React from 'react';

interface ImagePreviewProps {
  src: string;
  top: number;
  left: number;
}

export const ImagePreview: React.FC<ImagePreviewProps> = ({ src, top, left }) => {
  // Simple fade-in animation class
  const animationClasses = 'opacity-0 animate-fade-in';

  return (
    <div
      className={`fixed z-50 pointer-events-none transition-opacity duration-200 ${animationClasses}`}
      style={{ top, left }}
    >
      <img
        src={src}
        alt="Product preview"
        className="w-64 h-64 object-contain bg-white p-2 rounded-lg border border-slate-300 shadow-2xl"
      />
    </div>
  );
};
