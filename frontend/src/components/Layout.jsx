import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, FileText, LogOut, Search, User } from 'lucide-react';

const SidebarItem = ({ icon: Icon, label, active, onClick, isExpanded }) => (
  <button
    onClick={onClick}
    title={!isExpanded ? label : ""} 
    className={`w-full flex items-center p-3 rounded-xl transition-all ${
      active 
        ? 'bg-[#fdb913]/20 text-[#fdb913]' // Amarelo original com 20% de transparência e texto amarelo
        : 'text-gray-400 hover:bg-white/5 hover:text-white'
    } ${!isExpanded ? 'justify-center' : 'justify-start'}`}
  >
    <div className="min-w-[20px] flex justify-center">
      <Icon size={20} />
    </div>
    
    {isExpanded && (
      <span className="ml-4 text-xs font-bold uppercase tracking-widest whitespace-nowrap">
        {label}
      </span>
    )}
  </button>
);

const Layout = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isExpanded, setIsExpanded] = useState(false);
  
  // Resgata o nome do usuário. Se não achar no navegador, exibe 'Usuário'.
  const username = localStorage.getItem('username') || 'Usuário';

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
    { id: 'extratos', label: 'Extratos', icon: FileText, path: '/acompanhamento' },
  ];

  return (
    <div className="min-h-screen bg-[#f3f4f6] flex">
      {/* SIDEBAR */}
      <aside 
        className={`${
          isExpanded ? 'w-64' : 'w-20'
        } bg-[#3a3a3a] flex flex-col py-6 fixed h-full transition-all duration-300 overflow-hidden z-40`}
      >
        
        {/* Header da Sidebar */}
        <div className={`flex items-center mb-10 w-full ${isExpanded ? 'px-5 justify-start' : 'justify-center mt-2'}`}>
          <button 
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center outline-none active:scale-95 transition-all w-full"
            title={isExpanded ? "Recolher menu" : "Expandir menu"}
          >
            {isExpanded ? (
              /* Logo Escrita Completa (Aba Aberta) */
              <img 
                src="/logos.png" 
                alt="Scryta" 
                className="h-10 object-contain ml-2 animate-fade-in" 
              />
            ) : (
              /* Ícone S na Caixinha (Aba Fechada) */
              <div className="w-12 h-11 min-w-[40px] bg-[#fdb913]/20 rounded-lg flex items-center justify-center mx-auto">
                <img 
                  src="/scryta.png" 
                  alt="S" 
                  className="w-5 h-5 object-contain" 
                />
              </div>
            )}
          </button>
        </div>

        <nav className="flex-grow space-y-4 w-full px-3">
          {menuItems.map((item) => (
            <SidebarItem
              key={item.id}
              icon={item.icon}
              label={item.label}
              active={location.pathname === item.path}
              onClick={() => navigate(item.path)}
              isExpanded={isExpanded}
            />
          ))}
        </nav>

        <div className="pb-3 w-full px-2 border-t border-white/5 pt-3 mt-auto">
          <SidebarItem 
            icon={LogOut} 
            label="Sair" 
            isExpanded={isExpanded}
            onClick={() => {
              localStorage.clear();
              navigate('/login');
            }} 
          />
        </div>
      </aside>

      {/* CONTEÚDO PRINCIPAL */}
      <main 
        className={`flex-grow p-8 transition-all duration-300 ${
          isExpanded ? 'ml-64' : 'ml-20'
        }`}
      >
        <header className="flex justify-between items-center mb-8">
          <div>
            <h2 className="text-xl font-bold text-[#3a3a3a]">Extrato Contabilidade</h2>
            <p className="text-xs text-gray-400 font-medium">Extração e conciliação de dados bancários.</p>
          </div>
          
          <div className="flex items-center gap-4">
                        
            {/* Box do Usuário Logado */}
            <div className="flex items-center gap-3 bg-white px-4 py-2 rounded-xl shadow-sm border border-gray-100">
              <div className="w-8 h-8 bg-gray-50 rounded-lg flex items-center justify-center text-[#3a3a3a]">
                <User size={18} />
              </div>
              <span className="text-xs font-bold text-[#3a3a3a] uppercase tracking-widest">
                {username}
              </span>
            </div>
            
          </div>
        </header>

        {children}
      </main>
    </div>
  );
};

export default Layout;