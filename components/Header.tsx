
import React from 'react';
import type { ProcessedProduct } from '../types';
import { exportToCSV } from '../services/csvExporter';


interface HeaderProps {
    products: ProcessedProduct[];
    searchTerm: string;
    setSearchTerm: (term: string) => void;
    showProfitableOnly: boolean;
    setShowProfitableOnly: (show: boolean) => void;
}

export const Header: React.FC<HeaderProps> = ({ products, searchTerm, setSearchTerm, showProfitableOnly, setShowProfitableOnly }) => {
    
    const handleExport = () => {
        exportToCSV(products);
    };

    return (
        <>
            <header className="mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
                <div>
                    <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
                        Arbitrage Profit Master <span className="text-indigo-600">V8</span>
                    </h1>
                    <div className="flex items-center gap-2 mt-2 text-sm text-slate-500">
                        <span className="inline-block w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                        Live Data Mode • <span>{products.length}</span> Products Loaded
                    </div>
                </div>
                <div className="flex flex-wrap gap-3">
                    <button
                        onClick={() => setShowProfitableOnly(!showProfitableOnly)}
                        className={`flex items-center gap-2 border px-5 py-2.5 rounded-xl font-semibold hover:bg-slate-50 transition shadow-sm ${
                            showProfitableOnly
                                ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                                : 'bg-white border-slate-300 text-slate-700'
                        }`}
                    >
                        <span>💰</span>
                        <span>{showProfitableOnly ? 'Show All' : 'Profitable Only'}</span>
                    </button>
                    <button
                        onClick={handleExport}
                        disabled={products.length === 0}
                        className="flex items-center gap-2 border px-5 py-2.5 rounded-xl font-semibold bg-white border-slate-300 text-slate-700 hover:bg-slate-50 transition shadow-sm disabled:bg-slate-100 disabled:text-slate-400 disabled:cursor-not-allowed"
                    >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                           <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                        <span>Export CSV</span>
                    </button>
                </div>
            </header>
            <div className="mb-6">
                <div className="relative w-full md:w-1/3">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <svg className="h-5 w-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                    </div>
                    <input
                        type="text"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        placeholder="Search product title, ASIN, or UPC..."
                        className="block w-full pl-10 pr-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:outline-none transition shadow-sm placeholder:text-slate-400"
                    />
                </div>
            </div>
        </>
    );
};
