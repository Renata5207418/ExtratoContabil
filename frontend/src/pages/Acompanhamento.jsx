import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import api from '../services/api';
import { ArrowUpRight, Calendar, Loader2, RefreshCw, Search, ChevronUp, ChevronDown, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, CheckCircle2, Clock, Minus } from 'lucide-react';
import { toast } from 'sonner';

const Acompanhamento = () => {
  // --- ESTADOS COM MEMÓRIA DE SESSÃO ---
  const [busca, setBusca] = useState(() => sessionStorage.getItem('extratos_busca') || '');
  
  // NOVO: Estado para controlar a Aba
  const [abaAtiva, setAbaAtiva] = useState(() => sessionStorage.getItem('extratos_abaAtiva') || 'pendentes');
  
  const [sortConfig, setSortConfig] = useState(() => {
    const saved = sessionStorage.getItem('extratos_sortConfig');
    return saved ? JSON.parse(saved) : { key: 'recebidos', direction: 'desc' }; 
  });

  const [paginaAtual, setPaginaAtual] = useState(() => {
    const saved = sessionStorage.getItem('extratos_paginaAtual');
    return saved ? Number(saved) : 1;
  });
  
  const [itensPorPagina, setItensPorPagina] = useState(() => {
    const saved = sessionStorage.getItem('extratos_itensPorPagina');
    return saved ? Number(saved) : 10;
  });

  // Filtro de mês (salvando na sessão para não perder ao voltar da tela de detalhes)
  const [mesFiltro, setMesFiltro] = useState(() => {
    const saved = sessionStorage.getItem('extratos_mesFiltro');
    if (saved) return saved;
    const data = new Date();
    data.setMonth(data.getMonth() - 1); 
    return data.toISOString().slice(0, 7); 
  });

  const [empresas, setEmpresas] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Estados para o Calendário Customizado
  const [showMonthPicker, setShowMonthPicker] = useState(false);
  const [pickerYear, setPickerYear] = useState(() => parseInt(mesFiltro.split('-')[0]));
  const mesesPT = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];

  // --- EFEITOS PARA SALVAR NA MEMÓRIA ---
  useEffect(() => sessionStorage.setItem('extratos_busca', busca), [busca]);
  useEffect(() => sessionStorage.setItem('extratos_abaAtiva', abaAtiva), [abaAtiva]); // Salva aba
  useEffect(() => sessionStorage.setItem('extratos_sortConfig', JSON.stringify(sortConfig)), [sortConfig]);
  useEffect(() => sessionStorage.setItem('extratos_paginaAtual', paginaAtual), [paginaAtual]);
  useEffect(() => sessionStorage.setItem('extratos_itensPorPagina', itensPorPagina), [itensPorPagina]);
  useEffect(() => sessionStorage.setItem('extratos_mesFiltro', mesFiltro), [mesFiltro]);

  const fetchEmpresas = async () => {
    try {
      setLoading(true);
      const [ano, mes] = mesFiltro.split('-');
      const mesParaApi = `${mes}.${ano}`;
      
      const { data } = await api.get(`/extratos/acompanhamento?mes=${mesParaApi}`);
      setEmpresas(data.dados || []);
    } catch (err) {
      console.error("Erro na API:", err);
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  // Recarrega sempre que o mês mudar
  useEffect(() => {
    fetchEmpresas();
  }, [mesFiltro]);

  // --- LÓGICA DE ORDENAÇÃO E FILTRO DE ABAS ---
  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') direction = 'desc';
    setSortConfig({ key, direction });
    setPaginaAtual(1); 
  };

  const SortIcon = ({ columnKey }) => {
    if (sortConfig.key !== columnKey) return <ChevronDown size={14} className="text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity" />;
    return sortConfig.direction === 'asc' ? <ChevronUp size={14} className="text-[#fdb913]" /> : <ChevronDown size={14} className="text-[#fdb913]" />;
  };

  const dadosFiltradosEOrdenados = React.useMemo(() => {
    // 1. Busca por texto
    let dadosFiltrados = empresas.filter(emp => 
      emp.empresa.toLowerCase().includes(busca.toLowerCase()) || 
      emp.cnpj.includes(busca) ||
      emp.codigo.toString().includes(busca)
    );

    // 2. Filtro por Aba Ativa (Pendente = !validado | Validada = validado)
    if (abaAtiva === 'pendentes') {
      dadosFiltrados = dadosFiltrados.filter(emp => !emp.validado);
    } else if (abaAtiva === 'validadas') {
      dadosFiltrados = dadosFiltrados.filter(emp => emp.validado);
    }

    // 3. Ordenação
    return dadosFiltrados.sort((a, b) => {
      if (sortConfig.key === 'status') {
        const aStat = a.validado ? 2 : (a.recebidos > 0 ? 1 : 0);
        const bStat = b.validado ? 2 : (b.recebidos > 0 ? 1 : 0);
        if (aStat < bStat) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aStat > bStat) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      }
      if (a[sortConfig.key] < b[sortConfig.key]) return sortConfig.direction === 'asc' ? -1 : 1;
      if (a[sortConfig.key] > b[sortConfig.key]) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [empresas, busca, sortConfig, abaAtiva]);

  const totalItens = dadosFiltradosEOrdenados.length;
  const totalPaginas = Math.ceil(totalItens / itensPorPagina) || 1;

  const dadosPaginados = React.useMemo(() => {
    const inicio = (paginaAtual - 1) * itensPorPagina;
    return dadosFiltradosEOrdenados.slice(inicio, inicio + itensPorPagina);
  }, [dadosFiltradosEOrdenados, paginaAtual, itensPorPagina]);

  const handleToggleValidacao = async (id) => {
  try {
    await api.post(`/extratos/toggle-validar/${id}`);
    toast.success("Status de validação atualizado!");
    fetchEmpresas(); // Recarrega a lista
  } catch (err) {
    toast.error("Erro ao alterar status");
  }
};

  return (
    <Layout>
      <div className="bg-white rounded-[24px] shadow-sm border border-white overflow-hidden">
        <div className="p-6 border-b border-gray-50 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h3 className="font-bold text-[#3a3a3a] text-sm uppercase tracking-wider">Acompanhamento de Extratos</h3>
            <p className="text-[10px] text-gray-400 font-bold uppercase mt-1 mb-4">Status de recebimento por empresa</p>
            
            {/* SELETOR DE ABAS */}
            <div className="flex gap-4">
              <button 
                onClick={() => { setAbaAtiva('pendentes'); setPaginaAtual(1); }} 
                className={`text-[10px] font-black uppercase tracking-widest pb-2 border-b-2 transition-all flex items-center gap-2 ${
                  abaAtiva === 'pendentes' ? 'border-[#fdb913] text-[#3a3a3a]' : 'border-transparent text-gray-400 hover:text-gray-600'
                }`}
              >
                Pendentes
                <span className={`px-1.5 py-0.5 rounded-md text-[9px] ${
                  abaAtiva === 'pendentes' ? 'bg-[#fdb913] text-white' : 'bg-gray-100 text-gray-400'
                }`}>
                  {empresas.filter(emp => !emp.validado && emp.recebidos > 0).length}
                </span>
              </button>
              
              <button 
                onClick={() => { setAbaAtiva('validadas'); setPaginaAtual(1); }} 
                className={`text-[10px] font-black uppercase tracking-widest pb-2 border-b-2 transition-all flex items-center gap-2 ${
                  abaAtiva === 'validadas' ? 'border-[#fdb913] text-[#3a3a3a]' : 'border-transparent text-gray-400 hover:text-gray-600'
                }`}
              >
                Validadas
                <span className={`px-1.5 py-0.5 rounded-md text-[9px] ${
                  abaAtiva === 'validadas' ? 'bg-[#fdb913] text-white' : 'bg-gray-100 text-gray-400'
                }`}>
                  {empresas.filter(emp => emp.validado).length}
                </span>
              </button>
            </div>
          </div>
          
          <div className="flex flex-wrap items-center gap-3 w-full md:w-auto mt-4 md:mt-0">
            <div className="relative flex-grow md:flex-grow-0">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-300" size={14} />
              <input 
                type="text" 
                placeholder="Buscar por código, CNPJ ou nome..." 
                value={busca}
                onChange={(e) => {
                  setBusca(e.target.value);
                  setPaginaAtual(1); 
                }}
                className="w-full md:w-64 pl-9 pr-4 py-2 bg-gray-50 border border-gray-100 rounded-xl outline-none focus:bg-white text-xs font-medium placeholder:text-gray-400 transition-all"
              />
            </div>

            <button onClick={fetchEmpresas} className="p-2 text-gray-400 hover:text-[#fdb913] transition-colors" title="Atualizar dados">
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            </button>

            {/* SELETOR NATIVO DE MÊS CUSTOMIZADO */}
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
                  <div className="absolute top-full right-0 mt-2 w-64 bg-white shadow-2xl rounded-2xl border border-gray-100 z-50 p-4 animate-fade-in">
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
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <Loader2 className="animate-spin text-[#fdb913]" size={32} />
            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Sincronizando Banco de Dados...</p>
          </div>
        ) : dadosPaginados.length === 0 ? (
          <div className="py-20 text-center">
            <p className="text-xs text-gray-400 font-bold uppercase">Nenhuma empresa encontrada na aba {abaAtiva}.</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-gray-50/50">
                    <th className="px-6 py-4 cursor-pointer group select-none" onClick={() => handleSort('codigo')}>
                      <div className="flex items-center gap-2 text-[10px] font-black text-gray-400 uppercase tracking-widest">Código <SortIcon columnKey="codigo" /></div>
                    </th>
                    <th className="px-6 py-4 text-[10px] font-black text-gray-400 uppercase tracking-widest">CNPJ</th>
                    <th className="px-6 py-4 cursor-pointer group select-none" onClick={() => handleSort('empresa')}>
                      <div className="flex items-center gap-2 text-[10px] font-black text-gray-400 uppercase tracking-widest">Empresa <SortIcon columnKey="empresa" /></div>
                    </th>
                    <th className="px-6 py-4 cursor-pointer group select-none" onClick={() => handleSort('status')}>
                      <div className="flex items-center gap-2 text-[10px] font-black text-gray-400 uppercase tracking-widest">Status <SortIcon columnKey="status" /></div>
                    </th>
                    <th className="px-6 py-4 cursor-pointer group select-none" onClick={() => handleSort('recebidos')}>
                      <div className="flex items-center justify-center gap-2 text-[10px] font-black text-gray-400 uppercase tracking-widest">Recebidos <SortIcon columnKey="recebidos" /></div>
                    </th>
                    <th className="px-6 py-4 text-[10px] font-black text-gray-400 uppercase tracking-widest">Último Envio</th>
                    <th className="px-6 py-4"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {dadosPaginados.map((emp) => (
                    <tr key={emp.codigo} className="hover:bg-gray-50/50 transition-colors group">
                      <td className="px-6 py-4 text-xs font-bold text-gray-500">#{emp.codigo}</td>
                      <td className="px-6 py-4 text-xs font-medium text-gray-400">{emp.cnpj}</td>
                      <td className="px-6 py-4 text-xs font-bold text-[#3a3a3a]">{emp.empresa}</td>
                      <td className="px-6 py-4">
                        {emp.validado ? (
                          <div className="flex flex-col">
                            <button 
                              onClick={() => handleToggleValidacao(emp.id_solicitacao)}
                              className="px-2 py-1.5 rounded-md text-[9px] font-black bg-green-50 text-green-600 border border-green-200 hover:bg-red-50 hover:text-red-600 uppercase tracking-wider transition-all flex items-center gap-1.5 w-max"
                            >
                              <CheckCircle2 size={12} /> Validado por {emp.validado_por || 'User'}
                            </button>
                            <span className="text-[9px] text-gray-400 mt-1">{emp.data_validacao || ''}</span>
                          </div>
                        ) : emp.recebidos > 0 ? (
                          <button 
                            onClick={() => handleToggleValidacao(emp.id_solicitacao)}
                            className="px-2 py-1.5 rounded-md text-[9px] font-black bg-yellow-50 text-yellow-600 border border-yellow-200 hover:bg-green-50 uppercase tracking-wider flex items-center gap-1.5 w-max"
                          >
                            <Clock size={12} /> Pendente
                          </button>
                        ) : (
                          <span className="px-2 py-1.5 rounded-md text-[9px] font-black bg-gray-50 text-gray-400 border border-gray-100 flex items-center gap-1.5 w-max uppercase tracking-wider">
                            <Minus size={12} /> S/ Arquivos
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span 
                          title={
                            emp.validado 
                              ? 'Validado'
                              : emp.recebidos === 0 
                                ? 'Sem arquivos'
                                : emp.processados === emp.recebidos
                                  ? 'Leitura concluída pela IA'
                                  : `Processando: ${emp.processados || 0} de ${emp.recebidos} arquivos lidos`
                          }
                          className={`px-2 py-1 rounded-md text-[10px] font-black transition-all cursor-help ${
                            emp.validado 
                              ? 'bg-green-600 text-white' 
                              : emp.recebidos === 0
                                ? 'bg-gray-100 text-[#3a3a3a]' 
                                : emp.processados === emp.recebidos
                                  ? 'bg-green-600 text-white' 
                                  : 'bg-yellow-500 text-white' 
                          }`}>
                          {emp.recebidos || 0}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-xs font-medium text-gray-400">{emp.data}</td>
                      <td className="px-6 py-4 text-right">
                        <button 
                          onClick={() => {
                            const [ano, mes] = mesFiltro.split('-');
                            navigate(`/extratos/${emp.codigo}?mes=${mes}.${ano}`);
                          }}
                          className="p-2 bg-gray-50 text-gray-400 rounded-lg group-hover:bg-[#3a3a3a] group-hover:text-white transition-all shadow-sm"
                        >
                          <ArrowUpRight size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* CONTROLES DE PAGINAÇÃO */}
            <div className="p-6 border-t border-gray-50 flex flex-col sm:flex-row justify-between items-center gap-4 bg-gray-50/20">
              <div className="flex items-center gap-2 flex-wrap justify-center sm:justify-start">
                <span className="text-[10px] font-black text-gray-400 uppercase tracking-wider">Exibir:</span>
                <select
                  value={itensPorPagina}
                  onChange={(e) => { setItensPorPagina(Number(e.target.value)); setPaginaAtual(1); }}
                  className="bg-white border border-gray-100 rounded-xl text-xs font-bold text-[#3a3a3a] px-2.5 py-1.5 outline-none shadow-sm transition-all"
                >
                  <option value={10}>10 linhas</option>
                  <option value={20}>20 linhas</option>
                  <option value={50}>50 linhas</option>
                </select>
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider ml-2">
                  Mostrando {totalItens === 0 ? 0 : (paginaAtual - 1) * itensPorPagina + 1} - {Math.min(totalItens, paginaAtual * itensPorPagina)} de {totalItens} registros
                </span>
              </div>

              <div className="flex items-center gap-2">
                <button onClick={() => setPaginaAtual(1)} disabled={paginaAtual === 1} className="p-2 border border-gray-100 bg-white rounded-xl text-gray-400 hover:text-[#3a3a3a] disabled:opacity-40 shadow-sm" title="Primeira página"><ChevronsLeft size={16} /></button>
                <button onClick={() => setPaginaAtual(prev => Math.max(prev - 1, 1))} disabled={paginaAtual === 1} className="p-2 border border-gray-100 bg-white rounded-xl text-gray-400 hover:text-[#3a3a3a] disabled:opacity-40 shadow-sm" title="Página anterior"><ChevronLeft size={16} /></button>
                
                <div className="flex items-center gap-1 px-3 py-1 bg-gray-50 rounded-lg border border-gray-100 select-none">
                  <span className="text-xs font-black text-[#3a3a3a]">{paginaAtual}</span>
                  <span className="text-xs text-gray-300 font-bold">/</span>
                  <span className="text-xs font-bold text-gray-400">{totalPaginas}</span>
                </div>

                <button onClick={() => setPaginaAtual(prev => Math.min(prev + 1, totalPaginas))} disabled={paginaAtual === totalPaginas} className="p-2 border border-gray-100 bg-white rounded-xl text-gray-400 hover:text-[#3a3a3a] disabled:opacity-40 shadow-sm" title="Próxima página"><ChevronRight size={16} /></button>
                <button onClick={() => setPaginaAtual(totalPaginas)} disabled={paginaAtual === totalPaginas} className="p-2 border border-gray-100 bg-white rounded-xl text-gray-400 hover:text-[#3a3a3a] disabled:opacity-40 shadow-sm" title="Última página"><ChevronsRight size={16} /></button>
              </div>
            </div>
          </>
        )}
      </div>
    </Layout>
  );
};

export default Acompanhamento;