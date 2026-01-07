
import React, { useState, useRef, useEffect } from 'react';
import { validateKey } from '../services/serpApiService';

// --- Helper Icon Components ---
const SmallSpinner: React.FC = () => <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-slate-400"></div>;
const ValidIcon: React.FC = () => (
  <svg className="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);
const InvalidIcon: React.FC = () => (
  <svg className="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);


interface SidebarProps {
    apiKey: string;
    setApiKey: (key: string) => void;
    onStartResearch: (file: File) => void;
    isLoading: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ apiKey, setApiKey, onStartResearch, isLoading }) => {
    const [file, setFile] = useState<File | null>(null);
    const [dragActive, setDragActive] = useState(false);
    const [validationStatus, setValidationStatus] = useState<'idle' | 'validating' | 'valid' | 'invalid'>('idle');
    const [validationMessage, setValidationMessage] = useState('');
    const fileInputRef = useRef<HTMLInputElement>(null);
    const debounceTimeoutRef = useRef<number | null>(null);

    useEffect(() => {
        if (debounceTimeoutRef.current) clearTimeout(debounceTimeoutRef.current);

        if (!apiKey) {
            setValidationStatus('idle');
            setValidationMessage('');
            return;
        }

        setValidationStatus('validating');
        setValidationMessage('');

        debounceTimeoutRef.current = window.setTimeout(async () => {
            const { isValid, message } = await validateKey(apiKey);
            setValidationStatus(isValid ? 'valid' : 'invalid');
            setValidationMessage(message);
        }, 500); // 500ms debounce delay

        return () => {
            if (debounceTimeoutRef.current) clearTimeout(debounceTimeoutRef.current);
        };
    }, [apiKey]);


    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };
    
    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setFile(e.dataTransfer.files[0]);
        }
    };

    const handleButtonClick = () => {
        fileInputRef.current?.click();
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (file && validationStatus === 'valid') {
            onStartResearch(file);
        }
    };

    const getBorderColor = () => {
        switch (validationStatus) {
            case 'valid': return 'border-green-500 focus:border-green-500 focus:ring-green-500';
            case 'invalid': return 'border-red-500 focus:border-red-500 focus:ring-red-500';
            default: return 'border-slate-300 focus:border-indigo-500 focus:ring-indigo-500';
        }
    };

    return (
        <aside className="w-80 bg-white border-r border-slate-200 p-6 flex flex-col shadow-lg">
            <h2 className="text-xl font-bold text-slate-800 mb-6">Controls</h2>
            <form onSubmit={handleSubmit} className="flex flex-col h-full">
                <div className="space-y-6">
                    <div>
                        <label htmlFor="api-key" className="block text-sm font-medium text-slate-700 mb-1">
                            SerpApi API Key
                        </label>
                         <div className="relative">
                            <input
                                id="api-key"
                                type="password"
                                value={apiKey}
                                onChange={(e) => setApiKey(e.target.value)}
                                placeholder="Enter your API key"
                                className={`block w-full px-3 py-2 bg-white border rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:ring-1 ${getBorderColor()}`}
                                aria-invalid={validationStatus === 'invalid'}
                                aria-describedby="api-key-status"
                            />
                            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                                {validationStatus === 'validating' && <SmallSpinner />}
                                {validationStatus === 'valid' && <ValidIcon />}
                                {validationStatus === 'invalid' && <InvalidIcon />}
                            </div>
                        </div>
                        <p id="api-key-status" className={`mt-2 text-xs h-4 ${validationStatus === 'valid' ? 'text-green-600' : 'text-red-600'}`}>
                            {validationMessage}
                        </p>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                            Upload Keepa CSV
                        </label>
                        <div 
                            onDragEnter={handleDrag}
                            onDragOver={handleDrag}
                            onDragLeave={handleDrag}
                            onDrop={handleDrop}
                            onClick={handleButtonClick}
                            className={`flex justify-center items-center w-full h-32 px-6 py-4 border-2 border-dashed rounded-lg cursor-pointer transition-colors ${dragActive ? 'border-indigo-500 bg-indigo-50' : 'border-slate-300 bg-slate-50 hover:bg-slate-100'}`}
                        >
                            <div className="text-center">
                                <p className="text-sm text-slate-500">
                                    {file ? file.name : 'Drag & drop or click to upload'}
                                </p>
                            </div>
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept=".csv"
                                onChange={handleFileChange}
                                className="hidden"
                            />
                        </div>
                    </div>
                </div>

                <div className="mt-auto">
                     <button
                        type="submit"
                        disabled={validationStatus !== 'valid' || !file || isLoading}
                        className="w-full bg-indigo-600 text-white font-semibold py-2.5 px-4 rounded-lg shadow-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-slate-400 disabled:cursor-not-allowed transition"
                    >
                        {isLoading ? 'Researching...' : 'Start Research'}
                    </button>
                    <p className="text-xs text-slate-400 mt-3 text-center">
                        Your API key is used directly and never stored.
                    </p>
                </div>
            </form>
        </aside>
    );
};
