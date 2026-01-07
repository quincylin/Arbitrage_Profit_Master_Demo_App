
import React, { useState } from 'react';

interface CopyToClipboardButtonProps {
    textToCopy: string;
}

const CheckIcon: React.FC = () => (
    <svg className="w-3 h-3 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
    </svg>
);

const CopyIcon: React.FC = () => (
    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
    </svg>
);

export const CopyToClipboardButton: React.FC<CopyToClipboardButtonProps> = ({ textToCopy }) => {
    const [isCopied, setIsCopied] = useState(false);

    const handleCopy = () => {
        if (!textToCopy || isCopied) return;

        navigator.clipboard.writeText(textToCopy).then(() => {
            setIsCopied(true);
            setTimeout(() => {
                setIsCopied(false);
            }, 1500);
        }).catch(err => {
            console.error('Failed to copy text: ', err);
        });
    };
    
    const title = textToCopy ? `Copy ${textToCopy}` : 'Nothing to copy';

    return (
        <button
            onClick={handleCopy}
            className={`bg-white hover:bg-indigo-50 border-l border-slate-200 p-1.5 text-slate-400 hover:text-indigo-600 transition h-full flex items-center justify-center ${isCopied ? 'bg-emerald-50' : ''}`}
            title={title}
            disabled={!textToCopy}
        >
            {isCopied ? <CheckIcon /> : <CopyIcon />}
        </button>
    );
};
