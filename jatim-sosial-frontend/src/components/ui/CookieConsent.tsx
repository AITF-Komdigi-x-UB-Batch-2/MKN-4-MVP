import React, { useState, useEffect } from 'react';
import { ShieldCheck, Cookie } from 'lucide-react';

const CookieConsent: React.FC = () => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Periksa apakah user sudah menyetujui cookie sebelumnya
    const consent = localStorage.getItem('cookie_consent_accepted');
    if (!consent) {
      // Tampilkan banner dengan sedikit delay agar animasi masuknya smooth
      const timer = setTimeout(() => {
        setIsVisible(true);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem('cookie_consent_accepted', 'true');
    setIsVisible(false);
  };

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-6 left-6 right-6 md:left-auto md:right-6 md:max-w-md z-50 animate-slide-up">
      <div className="bg-white/90 backdrop-blur-md border border-slate-200/60 shadow-2xl rounded-2xl p-6 flex flex-col gap-4 text-slate-800 transition-all duration-300">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-xl shrink-0">
            <Cookie size={24} className="animate-pulse" />
          </div>
          <div className="flex flex-col gap-1">
            <h4 className="font-semibold text-slate-900 text-sm md:text-base flex items-center gap-1.5">
              Pemberitahuan Penggunaan Cookie
              <ShieldCheck size={16} className="text-emerald-600" />
            </h4>
            <p className="text-xs md:text-sm text-slate-600 leading-relaxed">
              Situs ini menggunakan cookie esensial untuk mengelola sesi login dan keamanan Anda.
            </p>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 pt-2 border-t border-slate-100">
          <button
            onClick={handleAccept}
            className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs md:text-sm rounded-xl transition-all duration-200 shadow-md shadow-blue-500/20 hover:shadow-lg hover:shadow-blue-500/30 cursor-pointer active:scale-95"
          >
            Saya Mengerti
          </button>
        </div>
      </div>
    </div>
  );
};

export default CookieConsent;
