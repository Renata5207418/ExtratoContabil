import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import * as XLSX from 'xlsx';
import { 
  Users, 
  FileCheck, 
  Send, 
  AlertCircle, 
  Download, 
  TrendingUp,
  Calendar,
  X,
  Search,
  Trophy 
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const StatCard = ({ label, value, subtext, icon: Icon, trend, onClick, clickable, theme = 'brand' }) => {
  const themeStyles = {
    brand: "bg-[#fdb913]/10 text-[#fdb913] group-hover:bg-[#fdb913] group-hover:text-white",
    gray: "bg-gray-100 text-gray-500 group-hover:bg-gray-500 group-hover:text-white",
    blue: "bg-blue-100 text-blue-500 group-hover:bg-blue-500 group-hover:text-white",
    green: "bg-green-100 text-green-500 group-hover:bg-green-500 group-hover:text-white",
    orange: "bg-orange-100 text-orange-500 group-hover:bg-orange-500 group-hover:text-white",
  };

  return (
    <div 
      onClick={onClick}
      className={`bg-white p-6 rounded-[28px] shadow-sm border border-white flex flex-col gap-4 group transition-all ${
        clickable 
          ? 'cursor-pointer hover:-translate-y-1 hover:shadow-xl hover:border-gray-200 active:scale-[0.98]' 
          : 'hover:shadow-md'
      }`}
    >
      <div className="flex justify-between items-start">
        <div className={`p-3 rounded-2xl transition-colors ${themeStyles[theme]}`}>
          <Icon size={22} />
        </div>
        <div className="flex flex-col items-end">
          <span className="text-[9px] font-black text-gray-300 uppercase tracking-[0.2em]">{label}</span>
          {trend && (
            <span className="text-[10px] text-green-500 font-bold flex items-center gap-1">
              <TrendingUp size={12} /> {trend}
            </span>
          )}
        </div>
      </div>
      <div>
        <h4 className="text-3xl font-bold text-[#3a3a3a] tracking-tight">{value}</h4>
        <p className="text-[10px] text-gray-400 font-bold uppercase tracking-tight mt-1">{subtext}</p>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  
  const [mesFiltro, setMesFiltro] = useState(() => {
    const data = new Date();
    data.setMonth(data.getMonth() - 1); 
    return data.toISOString().slice(0, 7); 
  });

  const [showMonthPicker, setShowMonthPicker] = useState(false);
  const [pickerYear, setPickerYear] = useState(() => parseInt(mesFiltro.split('-')[0]));
  const mesesPT = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
  
  const [modalConfig, setModalConfig] = useState({ isOpen: false, type: null }); 
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const fetchDashboard = async () => {
      setLoading(true); 
      try {
        const token = localStorage.getItem('token'); 
        
        const [ano, mes] = mesFiltro.split('-');
        const mesParaApi = `${mes}.${ano}`;

        const response = await fetch(`http://localhost:5000/api/extratos/dashboard?mes=${mesParaApi}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          setDashboardData(data);
        }
      } catch (error) {
        console.error("Erro ao buscar dados do dashboard", error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, [mesFiltro]); 

  const exportarExcelGeral = () => {
    if (!dashboardData) return;
    const { com_envio, sem_envio } = dashboardData.listas_excel;
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(com_envio), "Com Envio no Mês");
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(sem_envio), "Pendente (Sem Envio)");
    XLSX.writeFile(wb, `Relatorio_Geral_Extratos_${mesFiltro}.xlsx`);
  };

  const exportarExcelModal = () => {
    const dataToExport = getModalData();
    if (dataToExport.length === 0) return;
    
    const ws = XLSX.utils.json_to_sheet(dataToExport);
    const wb = XLSX.utils.book_new();
    const sheetName = modalConfig.type === 'com_envio' ? 'Empresas com Envio' : 'Empresas Pendentes';
    
    XLSX.utils.book_append_sheet(wb, ws, sheetName);
    XLSX.writeFile(wb, `${sheetName.replace(/ /g, '_')}_${mesFiltro}.xlsx`);
  };

  const openModal = (type) => {
    setSearchTerm('');
    setModalConfig({ isOpen: true, type });
  };
  const closeModal = () => setModalConfig({ isOpen: false, type: null });

  const getModalData = () => {
    if (!dashboardData || !modalConfig.type) return [];
    const list = dashboardData.listas_excel[modalConfig.type];
    
    if (!searchTerm) return list;
    
    return list.filter(emp => 
      emp["Razão Social"].toLowerCase().includes(searchTerm.toLowerCase()) ||
      String(emp["Código Domínio"]).includes(searchTerm)
    );
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex h-full min-h-[60vh] items-center justify-center">
          <div className="flex flex-col items-center gap-4 text-gray-500 font-medium">
            <div className="w-8 h-8 border-4 border-[#fdb913] border-t-transparent rounded-full animate-spin"></div>
            Sincronizando competência {mesFiltro.split('-')[1]}/{mesFiltro.split('-')[0]}...
          </div>
        </div>
      </Layout>
    );
  }

  const { estatisticas, grafico } = dashboardData;
  const modalData = getModalData();

  const top5Empresas = dashboardData.listas_excel?.com_envio
    ? [...dashboardData.listas_excel.com_envio]
        .sort((a, b) => b["Arquivos Processados"] - a["Arquivos Processados"]) 
        .slice(0, 5) 
    : [];

  return (
    <Layout>
      <div className="flex justify-between items-center mb-8">
        <div className="flex items-center gap-3 bg-white p-1.5 rounded-2xl border border-white shadow-sm">
          <div className="relative">
            <button 
              onClick={() => {
                setPickerYear(parseInt(mesFiltro.split('-')[0]));
                setShowMonthPicker(!showMonthPicker);
              }}
              className="flex items-center gap-2 px-4 py-2 bg-gray-50 rounded-xl border border-gray-100 hover:bg-gray-200 transition-colors focus:ring-2 focus:ring-[#fdb913]/30 outline-none"
            >
              <Calendar size={14} className="text-gray-400" />
              <span className="text-[11px] font-black text-[#3a3a3a] uppercase tracking-widest">
                {(() => {
                  const [ano, mes] = mesFiltro.split('-');
                  return new Date(ano, mes - 1).toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' });
                })()}
              </span>
            </button>

            {showMonthPicker && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setShowMonthPicker(false)}></div>
                <div className="absolute top-full left-0 mt-2 w-64 bg-white shadow-2xl rounded-2xl border border-gray-100 z-50 p-4 animate-fade-in">
                  <div className="flex justify-between items-center mb-4 px-2">
                    <button onClick={() => setPickerYear(y => y - 1)} className="p-1 hover:bg-gray-100 rounded-lg text-gray-500 font-bold">&lt;</button>
                    <span className="text-sm font-black text-[#3a3a3a]">{pickerYear}</span>
                    <button onClick={() => setPickerYear(y => y + 1)} className="p-1 hover:bg-gray-100 rounded-lg text-gray-500 font-bold">&gt;</button>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    {mesesPT.map((mesNome, index) => {
                      const strMes = String(index + 1).padStart(2, '0');
                      const valorCompleto = `${pickerYear}-${strMes}`;
                      const isSelected = mesFiltro === valorCompleto;

                      return (
                        <button
                          key={index}
                          onClick={() => {
                            setMesFiltro(valorCompleto);
                            setShowMonthPicker(false);
                          }}
                          className={`py-2 text-xs font-bold rounded-xl transition-all ${
                            isSelected 
                              ? 'bg-[#fdb913] text-white shadow-md shadow-yellow-500/20' 
                              : 'text-gray-500 hover:bg-gray-100 hover:text-[#3a3a3a]'
                          }`}
                        >
                          {mesNome}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        <button 
          onClick={exportarExcelGeral}
          className="flex items-center gap-2 bg-[#3a3a3a] text-white px-5 py-3 rounded-xl text-[10px] font-black uppercase tracking-[0.15em] hover:bg-[#252525] transition-all shadow-xl shadow-gray-200 active:scale-95"
        >
          <Download size={16} />
          Exportar Base Completa
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard 
          label="Carteira" 
          value={estatisticas.carteira} 
          subtext="Empresas na Domínio" 
          icon={Users} 
          theme="gray"
        />
        <StatCard 
          label="Processamento" 
          value={estatisticas.processamento} 
          subtext={`PDFs lidos em ${mesFiltro.split('-')[1]}/${mesFiltro.split('-')[0]}`} 
          icon={FileCheck} 
          theme="blue"
        />
        <StatCard 
          label="Processadas" 
          value={`${estatisticas.engajamento} (${estatisticas.engajamento_pct}%)`} 
          subtext="Empresas com envios no mês" 
          icon={Send} 
          clickable={true}
          onClick={() => openModal('com_envio')}
          theme="green"
        />
        <StatCard 
          label="Pendente" 
          value={`${estatisticas.pendente} (${estatisticas.pendente_pct}%)`} 
          subtext="Empresas sem envio no mês" 
          icon={AlertCircle}
          clickable={true}
          onClick={() => openModal('sem_envio')}
          theme="orange"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white p-8 rounded-[32px] shadow-sm border border-white">
          <div className="flex justify-between items-center mb-8">
            <h3 className="text-sm font-black text-[#3a3a3a] uppercase tracking-widest">Fluxo de Envios</h3>
            <div className="h-1 w-10 bg-[#fdb913] rounded-full"></div>
          </div>
          
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={grafico}>
                <defs>
                  <linearGradient id="colorEnvios" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#fdb913" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#fdb913" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f1f1" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fontSize: 10, fontWeight: 700, fill: '#9ca3af'}} dy={10} />
                <YAxis hide />
                <Tooltip contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)'}} itemStyle={{fontSize: '12px', fontWeight: 800, color: '#3a3a3a'}} />
                <Area type="monotone" dataKey="envios" stroke="#fdb913" strokeWidth={4} fillOpacity={1} fill="url(#colorEnvios)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-[#3a3a3a] p-8 rounded-[32px] shadow-sm text-white flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-black uppercase tracking-widest mb-2">Resumo Operacional</h3>
            <p className="text-xs text-gray-400 font-medium leading-relaxed">
              O processamento está operando com alta precisão na extração de dados bancários baseando-se na carteira Domínio.
            </p>
          </div>
          <div className="space-y-4 mt-8">
             <div className="bg-white/5 p-4 rounded-2xl border border-white/5">
                <p className="text-[10px] font-bold text-gray-500 uppercase mb-1">Média de tempo por PDF</p>
                <p className="text-xl font-bold">1.2 segundos</p>
             </div>
             <div className="bg-white/5 p-4 rounded-2xl border border-white/5">
                <p className="text-[10px] font-bold text-gray-500 uppercase mb-1">Empresas Processadas</p>
                <p className="text-xl font-bold">{estatisticas.engajamento}</p>
             </div>
          </div>
        </div>
      </div>

      <div className="mt-6 bg-white p-8 rounded-[32px] shadow-sm border border-white">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-sm font-black text-[#3a3a3a] uppercase tracking-widest flex items-center gap-3">
            <Trophy size={18} className="text-[#fdb913]" />
            Top 5 Empresas com mais arquivos processados
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr>
                <th className="pb-3 text-[10px] font-black text-gray-400 uppercase tracking-widest border-b border-gray-100">Empresa</th>
                <th className="pb-3 text-[10px] font-black text-gray-400 uppercase tracking-widest border-b border-gray-100 text-right w-32">Quantidade</th>
              </tr>
            </thead>
            <tbody>
              {top5Empresas.map((emp, idx) => (
                <tr key={emp["Código Domínio"]} className="group hover:bg-gray-50/50 transition-colors">
                  <td className="py-4 border-b border-gray-50 text-sm font-bold text-[#3a3a3a] flex items-center gap-4">
                    <span className={`w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-black shrink-0 ${
                      idx === 0 ? 'bg-[#fdb913] text-white shadow-md shadow-yellow-500/20' : 'bg-gray-100 text-gray-400'
                    }`}>
                      {idx + 1}
                    </span>
                    <span className="truncate">{emp["Razão Social"]}</span>
                  </td>
                  <td className="py-4 border-b border-gray-50 text-base font-black text-[#3a3a3a] text-right">
                    {emp["Arquivos Processados"]}
                  </td>
                </tr>
              ))}
              {top5Empresas.length === 0 && (
                <tr>
                  <td colSpan="2" className="py-8 text-center text-gray-400 text-sm font-medium">
                    Ainda não há arquivos processados no mês selecionado.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {modalConfig.isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-[#0f172a]/60 backdrop-blur-sm transition-opacity">
          <div className="bg-white rounded-[32px] shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden animate-fade-in relative">
            
            <div className="p-8 pb-6 flex justify-between items-center border-b border-gray-100 bg-white">
              <div>
                <h3 className="text-2xl font-bold text-[#3a3a3a] tracking-tight">
                  {modalConfig.type === 'com_envio' ? 'Empresas com Envios' : 'Empresas Pendentes'}
                </h3>
                <p className="text-xs text-gray-400 font-medium mt-1">
                  {modalConfig.type === 'com_envio' ? 'Lista de empresas que já processaram arquivos neste mês.' : 'Lista de empresas ativas na Domínio sem envios recentes.'}
                </p>
              </div>
              <button 
                onClick={closeModal}
                className="w-10 h-10 bg-gray-50 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-xl flex items-center justify-center transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            <div className="px-8 py-4 bg-gray-50 border-b border-gray-100 flex gap-4 items-center">
              <div className="relative flex-grow">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input 
                  type="text" 
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Buscar por nome ou código..." 
                  className="w-full pl-12 pr-4 py-3 bg-white border border-gray-200 rounded-xl text-sm outline-none focus:border-[#fdb913] focus:ring-4 focus:ring-[#fdb913]/10 transition-all shadow-sm text-gray-700"
                />
              </div>
            </div>

            <div className="flex-grow overflow-y-auto p-8 bg-white">
              <div className="min-w-full">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr>
                      <th className="pb-4 text-[10px] font-black text-gray-400 uppercase tracking-widest border-b border-gray-100 w-24">Código</th>
                      <th className="pb-4 text-[10px] font-black text-gray-400 uppercase tracking-widest border-b border-gray-100">Razão Social</th>
                      <th className="pb-4 text-[10px] font-black text-gray-400 uppercase tracking-widest border-b border-gray-100 text-right">
                        {modalConfig.type === 'com_envio' ? 'Arquivos Lidos' : 'Status'}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {modalData.length > 0 ? (
                      modalData.map((emp) => (
                        <tr key={emp["Código Domínio"]} className="hover:bg-gray-50 transition-colors group">
                          <td className="py-4 border-b border-gray-50 text-sm font-bold text-gray-500">#{emp["Código Domínio"]}</td>
                          <td className="py-4 border-b border-gray-50 text-sm font-bold text-[#3a3a3a] truncate max-w-md">{emp["Razão Social"]}</td>
                          <td className="py-4 border-b border-gray-50 text-right">
                            {modalConfig.type === 'com_envio' ? (
                              <span className="inline-flex items-center justify-center px-3 py-1 rounded-full bg-green-50 text-green-600 text-xs font-bold border border-green-100">
                                {emp["Arquivos Processados"]} docs
                              </span>
                            ) : (
                              <span className="inline-flex items-center justify-center px-3 py-1 rounded-full bg-red-50 text-red-500 text-xs font-bold border border-red-100">
                                Pendente
                              </span>
                            )}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="3" className="py-10 text-center text-gray-400 text-sm font-medium">
                          Nenhuma empresa encontrada com os filtros atuais.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="p-6 bg-gray-50 border-t border-gray-100 flex justify-between items-center">
              <span className="text-xs font-bold text-gray-500 uppercase tracking-widest">
                Total: {modalData.length} registros
              </span>
              <div className="flex gap-3">
                <button 
                  onClick={closeModal}
                  className="px-6 py-2.5 bg-white border border-gray-200 text-gray-600 hover:bg-gray-100 rounded-xl text-[11px] font-bold uppercase tracking-widest transition-all"
                >
                  Fechar
                </button>
                <button 
                  onClick={exportarExcelModal}
                  className="flex items-center gap-2 bg-[#474745] text-[#faf9f7] px-6 py-2.5 rounded-xl text-[11px] font-bold uppercase tracking-widest hover:bg-[#6e6d6a] transition-all shadow-md shadow-yellow-500/20 active:scale-95"
                >
                  <Download size={16} />
                  Baixar Lista (.XLSX)
                </button>
              </div>
            </div>
            
          </div>
        </div>
      )}
    </Layout>
  );
};

export default Dashboard;
