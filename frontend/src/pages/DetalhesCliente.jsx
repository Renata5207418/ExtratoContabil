import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import Layout from '../components/Layout';
import api from '../services/api';
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Download,
  ExternalLink,
  Eye,
  FileText,
  Hash,
  History,
  Loader2,
  Pencil,
  X
} from 'lucide-react';
import { toast } from 'sonner';

const parseResumoDetalhado = (conteudo) => {
  if (!conteudo) return null;

  try {
    return typeof conteudo === 'string' ? JSON.parse(conteudo) : conteudo;
  } catch (e) {
    return null;
  }
};

const simNao = (valor) => {
  if (valor === true) return 'Sim';
  if (valor === false) return 'Não';
  return 'Não identificado';
};

const formatarModoLeitura = (modo) => {
  const mapa = {
    pdf_metadados: 'PDF - Metadados',
    pdf_texto: 'PDF - Texto extraído',
    pdf_ocr: 'PDF - OCR',
    pdf_erro: 'PDF - Erro',
    pdf_sem_pymupdf: 'PDF - Sem PyMuPDF',
    ofx_estruturado: 'OFX - Estruturado',
    ofxparse: 'OFX - Estruturado',
    ofx_manual: 'OFX - Manual',
    ofx_erro: 'OFX - Erro',
    extensao_nao_suportada: 'Extensão não suportada'
  };

  return mapa[modo] || formatadorSeguro(modo);
};

const InfoLeitura = ({ label, value }) => (
  <div className="bg-white/5 border border-white/5 rounded-xl p-3 text-xs">
    <p className="text-[#fdb913] font-black uppercase tracking-widest text-[9px] mb-1">
      {label}
    </p>

    <p className="text-white/90 break-words font-bold">
      {formatadorSeguro(value)}
    </p>
  </div>
);

const RenderResumoIA = ({ conteudo, selectedFile }) => {
  const dados = parseResumoDetalhado(conteudo);

  if (!dados) {
    return (
      <div className="bg-white/5 border border-white/5 rounded-2xl p-5 text-center">
        <AlertTriangle size={22} className="text-gray-400 mx-auto mb-2" />

        <p className="text-gray-300 text-[11px] font-black uppercase tracking-widest">
          Resumo indisponível
        </p>

        <p className="text-gray-400 text-[10px] font-medium mt-2">
          Abra o PDF original para conferência manual.
        </p>
      </div>
    );
  }

  const modoLeitura = dados.modo_leitura || dados.origem_extracao || 'pdf_metadados';
  const metadadosExtraidos = dados.metadados_extraidos === true;
  const semMovimento = dados.sem_movimento === true;
  const qtdMovimentacoes = Number(dados.qtd_movimentacoes || 0);

  const { banco, periodo } = separarBancoPeriodo(selectedFile?.banco_periodo);
  const tipo = selectedFile?.tipo || selectedFile?.tipo_documento || 'N/A';

  if (semMovimento) {
    return (
      <div className="space-y-4">
        <div className="bg-white/5 border border-green-400/20 rounded-2xl p-5 text-center">
          <CheckCircle2 size={24} className="text-green-400 mx-auto mb-2" />

          <p className="text-gray-200 text-[11px] font-black uppercase tracking-widest">
            Sem movimento identificado
          </p>

          <p className="text-gray-400 text-[10px] font-medium mt-2">
            O sistema identificou ausência de movimentação. A conferência final continua sendo visual pelo PDF original.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <InfoLeitura label="Banco" value={banco} />
          <InfoLeitura label="Período" value={periodo} />
          <InfoLeitura label="Tipo" value={tipo} />
          <InfoLeitura label="Modo" value={formatarModoLeitura(modoLeitura)} />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div
        className={`border rounded-2xl p-5 text-center ${
          metadadosExtraidos
            ? 'bg-white/5 border-green-400/20'
            : 'bg-white/5 border-dashed border-[#fdb913]/30'
        }`}
      >
        {metadadosExtraidos ? (
          <CheckCircle2 size={24} className="text-green-400 mx-auto mb-2" />
        ) : (
          <AlertTriangle size={22} className="text-[#fdb913] mx-auto mb-2" />
        )}

        <p className="text-gray-200 text-[11px] font-black uppercase tracking-widest">
          {metadadosExtraidos ? 'Leitura automática concluída' : 'Conferência necessária'}
        </p>

        <p className="text-gray-400 text-[10px] font-medium mt-2">
          {metadadosExtraidos
            ? 'Banco, período e tipo foram identificados. Confira o conteúdo diretamente no PDF original.'
            : 'Banco ou período não foram identificados com segurança. Preencha manualmente antes de validar.'}
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        <InfoLeitura label="Banco" value={banco} />
        <InfoLeitura label="Período" value={periodo} />
        <InfoLeitura label="Tipo" value={tipo} />
        <InfoLeitura label="Modo" value={formatarModoLeitura(modoLeitura)} />
        <InfoLeitura label="Sem movimento" value={simNao(dados.sem_movimento)} />
        <InfoLeitura
          label="Movimentos OFX"
          value={qtdMovimentacoes > 0 ? qtdMovimentacoes : 'N/A'}
        />
      </div>
    </div>
  );
};

const normalizar = (valor) => String(valor || '').trim();

const formatadorSeguro = (texto) => {
  if (!texto || texto === 'null' || texto === 'undefined') return 'N/A';
  return texto;
};

const separarBancoPeriodo = (bancoPeriodo) => {
  const partes = String(bancoPeriodo || '').split(' / ');

  return {
    banco: formatadorSeguro(partes[0]),
    periodo: formatadorSeguro(partes[1])
  };
};

const arquivoPrecisaConferencia = (arq) => {
  const { banco, periodo } = separarBancoPeriodo(arq?.banco_periodo);

  const bancoLower = banco.toLowerCase();
  const periodoLower = periodo.toLowerCase();

  const bancoRuim =
    !banco ||
    banco === 'N/A' ||
    bancoLower.includes('desconhecido') ||
    bancoLower.includes('inexistente');

  const periodoRuim =
    !periodo ||
    periodo === 'N/A' ||
    periodoLower.includes('não identificado') ||
    periodoLower.includes('nao identificado');

  return bancoRuim || periodoRuim;
};

const SituacaoBadge = ({ arq }) => {
  const precisaConferir = arquivoPrecisaConferencia(arq);
  const dados = parseResumoDetalhado(arq?.resumo_detalhado);

  if (precisaConferir) {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border bg-yellow-50 text-yellow-700 border-yellow-100 text-[9px] font-black uppercase tracking-widest">
        <AlertTriangle size={11} />
        Conferir
      </span>
    );
  }

  if (dados?.sem_movimento === true) {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border bg-blue-50 text-blue-600 border-blue-100 text-[9px] font-black uppercase tracking-widest">
        <CheckCircle2 size={11} />
        Sem movimento
      </span>
    );
  }

  if (
    dados?.modo_leitura === 'ofx_estruturado' ||
    dados?.origem_extracao === 'ofxparse' ||
    dados?.origem_extracao === 'ofx_manual'
  ) {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border bg-green-50 text-green-600 border-green-100 text-[9px] font-black uppercase tracking-widest">
        <CheckCircle2 size={11} />
        OFX lido
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border bg-green-50 text-green-600 border-green-100 text-[9px] font-black uppercase tracking-widest">
      <CheckCircle2 size={11} />
      Identificado
    </span>
  );
};

const DetalhesCliente = () => {
  const { codigo } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const [filtro, setFiltro] = useState('todos');

  const [selectedFile, setSelectedFile] = useState(null);
  const [editBanco, setEditBanco] = useState('');
  const [editPeriodo, setEditPeriodo] = useState('');
  const [editObs, setEditObs] = useState('');
  const [savingDetails, setSavingDetails] = useState(false);
  const [showAnalysis, setShowAnalysis] = useState(false);

  const mesBusca = searchParams.get('mes') || (() => {
    const d = new Date();
    d.setMonth(d.getMonth() - 1);

    const ano = d.getFullYear();
    const mes = String(d.getMonth() + 1).padStart(2, '0');

    return `${mes}.${ano}`;
  })();

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        const response = await api.get(`/extratos/cliente/${codigo}?mes=${mesBusca}`);
        setData(response.data);
      } catch (err) {
        console.error('Erro ao buscar detalhes:', err);
        toast.error('Erro ao buscar detalhes do cliente');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [codigo, mesBusca]);

  const arquivos = data?.arquivos || [];

    const numerosSolicitacoes = useMemo(() => {
    const numerosBackend = data?.solicitacao?.numeros_solicitacoes || [];

    if (numerosBackend.length > 0) {
      return numerosBackend.filter(Boolean);
    }

    return [
      ...new Set(
        arquivos
          .map((arq) => arq.numero_solicitacao)
          .filter(Boolean)
      )
    ];
  }, [data, arquivos]);

  const totalSolicitacoes =
    data?.solicitacao?.quantidade_solicitacoes ?? numerosSolicitacoes.length;

  const resumo = useMemo(() => {
    const total = arquivos.length;
    const conferir = arquivos.filter((arq) => arquivoPrecisaConferencia(arq)).length;
    const editados = arquivos.filter((arq) => Boolean(arq.ultima_edicao_por)).length;
    const ok = total - conferir;

    return {
      total,
      ok,
      conferir,
      editados
    };
  }, [arquivos]);

  const arquivosFiltrados = useMemo(() => {
    if (filtro === 'conferir') {
      return arquivos.filter((arq) => arquivoPrecisaConferencia(arq));
    }

    if (filtro === 'editados') {
      return arquivos.filter((arq) => Boolean(arq.ultima_edicao_por));
    }

    return arquivos;
  }, [arquivos, filtro]);

  const hasUnsavedChanges = useMemo(() => {
    if (!selectedFile) return false;

    return (
      editBanco !== (selectedFile.bancoOriginalInput || '') ||
      editPeriodo !== (selectedFile.periodoOriginalInput || '') ||
      editObs !== (selectedFile.observacaoOriginalInput || '')
    );
  }, [selectedFile, editBanco, editPeriodo, editObs]);

  const abrirModalArquivo = (arq) => {
    const { banco, periodo } = separarBancoPeriodo(arq.banco_periodo);

    const bancoInicial =
      banco === 'N/A' ||
      banco === 'Desconhecido' ||
      banco === 'Inexistente'
        ? ''
        : banco;

    const periodoInicial =
      periodo === 'N/A' ||
      periodo === 'Não identificado'
        ? ''
        : periodo;

    const observacaoInicial = arq.observacao || '';

    setSelectedFile({
      ...arq,
      bancoLimpo: banco,
      periodoLimpo: periodo,
      bancoOriginalInput: bancoInicial,
      periodoOriginalInput: periodoInicial,
      observacaoOriginalInput: observacaoInicial
    });

    setEditBanco(bancoInicial);
    setEditPeriodo(periodoInicial);
    setEditObs(observacaoInicial);
    setShowAnalysis(false);
  };

  const fecharModalArquivo = () => {
    if (savingDetails) return;

    if (hasUnsavedChanges) {
      const confirmar = window.confirm(
        'Existem alterações não salvas neste arquivo. Deseja fechar mesmo assim?'
      );

      if (!confirmar) return;
    }

    setSelectedFile(null);
    setEditBanco('');
    setEditPeriodo('');
    setEditObs('');
    setShowAnalysis(false);
  };

  const handleSalvarDetalhesArquivo = async () => {
    if (!selectedFile?.id) return;

    const bancoFinal = editBanco.trim() || 'Desconhecido';
    const periodoFinal = editPeriodo.trim() || 'N/A';
    const observacaoFinal = editObs || '';

    try {
      setSavingDetails(true);

      const resp = await api.put(`/extratos/arquivo/${selectedFile.id}/detalhes`, {
        banco: bancoFinal,
        periodo: periodoFinal,
        observacao: observacaoFinal
      });

      const arquivoAtualizado = resp.data.arquivo;

      setData((prev) => ({
        ...prev,
        arquivos: prev.arquivos.map((a) =>
          a.id === selectedFile.id
            ? {
                ...a,
                banco_periodo: arquivoAtualizado.banco_periodo,
                observacao: arquivoAtualizado.observacao,
                ultima_edicao_por: arquivoAtualizado.ultima_edicao_por,
                ultima_edicao_em: arquivoAtualizado.ultima_edicao_em,
                historico_edicoes: arquivoAtualizado.historico_edicoes
              }
            : a
        )
      }));

      const bancoInputAtualizado =
        arquivoAtualizado.banco === 'Desconhecido' ? '' : arquivoAtualizado.banco;

      const periodoInputAtualizado =
        arquivoAtualizado.periodo === 'N/A' ? '' : arquivoAtualizado.periodo;

      setSelectedFile((prev) => ({
        ...prev,
        banco_periodo: arquivoAtualizado.banco_periodo,
        bancoLimpo: arquivoAtualizado.banco,
        periodoLimpo: arquivoAtualizado.periodo,
        observacao: arquivoAtualizado.observacao,
        ultima_edicao_por: arquivoAtualizado.ultima_edicao_por,
        ultima_edicao_em: arquivoAtualizado.ultima_edicao_em,
        historico_edicoes: arquivoAtualizado.historico_edicoes,
        bancoOriginalInput: bancoInputAtualizado,
        periodoOriginalInput: periodoInputAtualizado,
        observacaoOriginalInput: arquivoAtualizado.observacao || ''
      }));

      setEditBanco(bancoInputAtualizado);
      setEditPeriodo(periodoInputAtualizado);
      setEditObs(arquivoAtualizado.observacao || '');

      toast.success(resp.data.mensagem || 'Informações atualizadas com sucesso!');
    } catch (err) {
      console.error('Erro ao salvar detalhes do arquivo:', err);
      toast.error('Erro ao salvar alterações');
    } finally {
      setSavingDetails(false);
    }
  };

  const abrirPdfOriginal = (arquivoId) => {
    const token = localStorage.getItem('token');

    if (!token) {
      toast.error('Sessão expirada. Faça login novamente.');
      return;
    }

    const baseURL = api.defaults.baseURL || 'http://localhost:5000/api';
    const url = `${baseURL}/extratos/arquivo/${arquivoId}/visualizar?jwt=${encodeURIComponent(token)}`;

    window.open(url, '_blank');
  };

  const handleDownload = async () => {
    if (!data?.solicitacao?.id) return;

    try {
      const response = await api.get(
        `/extratos/solicitacao/${data.solicitacao.id}/exportar`,
        {
          responseType: 'blob'
        }
      );

      const contentDisposition = response.headers['content-disposition'];

      let filename = `Relatorio_Extratos_${data?.cliente?.codigo || 'cliente'}_${mesBusca}.xlsx`;

      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^"]+)"?/);

        if (match?.[1]) {
          filename = match[1];
        }
      }

      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });

      const url = window.URL.createObjectURL(blob);

      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);

      document.body.appendChild(link);
      link.click();

      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success('Relatório baixado com sucesso!');
    } catch (err) {
      console.error('Erro ao baixar relatório:', err);
      toast.error('Erro ao baixar relatório');
    }
  };

  const handleValidarLote = async () => {
    if (!data?.solicitacao?.id) return;

    if (resumo.conferir > 0) {
      const confirmar = window.confirm(
        `Existem ${resumo.conferir} arquivo(s) para conferência. Deseja validar o lote mesmo assim?`
      );

      if (!confirmar) return;
    }

    try {
      const resp = await api.post(`/extratos/validar/${data.solicitacao.id}`);

      toast.success(resp.data.mensagem);

      setData((prev) => ({
        ...prev,
        solicitacao: {
          ...prev.solicitacao,
          validado: true,
          validado_por: resp.data.validado_por,
          data_validacao: new Date().toLocaleString('pt-BR')
        }
      }));
    } catch (err) {
      console.error('Erro ao validar lote:', err);
      toast.error('Erro ao validar lote');
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center py-20 gap-3">
          <Loader2 className="animate-spin text-[#fdb913]" size={32} />
          <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">
            Carregando processamento...
          </p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="mb-6">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-[10px] font-black text-gray-400 uppercase tracking-widest hover:text-[#3a3a3a]"
        >
          <ArrowLeft size={14} />
          Voltar para a lista
        </button>
      </div>

      <div className="bg-white rounded-[24px] shadow-sm border border-white p-8 mb-6">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-5">
          <div>
            <h2 className="text-2xl font-bold text-[#3a3a3a] tracking-tight">
              {data?.cliente?.nome}
            </h2>

            <div className="flex flex-wrap items-center gap-4 mt-2">
              <p className="text-xs text-gray-400 font-bold uppercase tracking-wider">
                CNPJ: {data?.cliente?.cnpj} | Código: {data?.cliente?.codigo}
              </p>
            </div>

            <div className="flex flex-wrap gap-2 mt-4">
              {totalSolicitacoes > 0 && (
                  <span className="px-3 py-1 rounded-full bg-gray-50 text-gray-500 border border-gray-100 text-[9px] font-black uppercase tracking-widest">
                    {totalSolicitacoes} solicitação{totalSolicitacoes > 1 ? 'ões' : ''}
                  </span>
                )}

              <span className="px-3 py-1 rounded-full bg-green-50 text-green-600 border border-green-100 text-[9px] font-black uppercase tracking-widest">
                {resumo.ok} identificados
              </span>

              {resumo.conferir > 0 && (
                <span className="px-3 py-1 rounded-full bg-yellow-50 text-yellow-700 border border-yellow-100 text-[9px] font-black uppercase tracking-widest">
                  {resumo.conferir} para conferir
                </span>
              )}

              {resumo.editados > 0 && (
                <span className="px-3 py-1 rounded-full bg-gray-50 text-gray-500 border border-gray-100 text-[9px] font-black uppercase tracking-widest">
                  {resumo.editados} editado(s)
                </span>
              )}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {data?.solicitacao && (
              <button
                onClick={handleDownload}
                className="flex items-center gap-2 bg-gray-100 text-gray-600 px-4 py-2 rounded-xl font-bold text-[10px] uppercase hover:bg-gray-200"
              >
                <Download size={16} />
                Exportar Excel
              </button>
            )}

            {data?.solicitacao &&
              (data.solicitacao.validado ? (
                <div className="flex items-center gap-2 bg-green-50 px-4 py-2 rounded-xl border border-green-100 text-green-600">
                  <CheckCircle2 size={16} />
                  <span className="text-[9px] font-black uppercase">Validado</span>
                </div>
              ) : (
                <button
                  onClick={handleValidarLote}
                  className="flex items-center gap-2 bg-[#fdb913] text-[#3a3a3a] px-4 py-2 rounded-xl font-bold text-[10px] uppercase hover:bg-yellow-400"
                >
                  <CheckCircle2 size={16} />
                  Validar lote
                </button>
              ))}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-[24px] shadow-sm border border-white p-4 mb-6">
        <div className="flex flex-wrap gap-2">
          {[
            { key: 'todos', label: `Todos (${resumo.total})` },
            { key: 'conferir', label: `Conferir (${resumo.conferir})` },
            { key: 'editados', label: `Editados (${resumo.editados})` }
          ].map((btn) => (
            <button
              key={btn.key}
              onClick={() => setFiltro(btn.key)}
              className={`px-4 py-2 rounded-xl border text-[10px] font-black uppercase tracking-widest transition-all ${
                filtro === btn.key
                  ? 'bg-[#3a3a3a] text-white border-[#3a3a3a]'
                  : 'bg-gray-50 text-gray-500 border-gray-100 hover:bg-gray-100'
              }`}
            >
              {btn.label}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-[24px] shadow-sm border border-white overflow-hidden">
        <table className="w-full text-left">
          <thead>
            <tr className="bg-gray-50/50">
              <th className="px-6 py-4 text-[10px] font-black text-gray-400 uppercase tracking-widest">
                Arquivo
              </th>
              <th className="px-6 py-4 text-[10px] font-black text-gray-400 uppercase tracking-widest">
                Solicitação
              </th>
              <th className="px-6 py-4 text-[10px] font-black text-gray-400 uppercase tracking-widest">
                Banco / Período
              </th>
              <th className="px-6 py-4 text-[10px] font-black text-gray-400 uppercase tracking-widest">
                Situação
              </th>
              <th className="px-6 py-4 text-right text-[10px] font-black text-gray-400 uppercase tracking-widest">
                Ações
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-gray-50">
            {arquivosFiltrados.map((arq, idx) => {
              const { banco, periodo } = separarBancoPeriodo(arq.banco_periodo);
              const precisaConferir = arquivoPrecisaConferencia(arq);

              return (
                <tr key={arq.id || idx} className="hover:bg-gray-50/50">
                  <td className="px-6 py-4">
                    <p className="text-xs font-bold text-[#3a3a3a] break-words">
                      {arq.arquivo}
                    </p>

                    <div className="flex flex-wrap gap-2 mt-1">
                      {arq.tipo && (
                        <span className="text-[9px] text-gray-400 font-black uppercase tracking-widest">
                          {arq.tipo}
                        </span>
                      )}

                      {arq.ultima_edicao_por && (
                        <span className="inline-flex items-center gap-1 text-[9px] text-gray-400 font-black uppercase tracking-widest">
                          <History size={10} />
                          Editado
                        </span>
                      )}
                    </div>
                  </td>

                  <td className="px-6 py-4">
                    {arq.numero_solicitacao ? (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-gray-50 text-gray-500 border border-gray-100 text-[9px] font-black uppercase tracking-widest">
                        <Hash size={10} />
                        #{arq.numero_solicitacao}
                      </span>
                    ) : (
                      <span className="text-[10px] font-bold text-gray-300 uppercase">
                        -
                      </span>
                    )}
                  </td>

                  <td className="px-6 py-4">
                    <div className="flex flex-col gap-1">
                      <p className="text-xs font-bold text-[#3a3a3a]">
                        {banco}
                      </p>

                      <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">
                        {periodo}
                      </p>
                    </div>
                  </td>

                  <td className="px-6 py-4">
                    <SituacaoBadge arq={arq} />
                  </td>

                  <td className="px-6 py-4">
                    <div className="flex items-center justify-end gap-2">                     

                      <button
                        onClick={() => abrirModalArquivo(arq)}
                        className="p-2 bg-gray-50 text-gray-400 rounded-lg hover:bg-[#3a3a3a] hover:text-white transition-all"
                        title="Visualizar e editar"
                      >
                        <Eye size={16} />
                      </button>

                       <button
                        onClick={() => abrirPdfOriginal(arq.id)}
                        className="p-2 bg-gray-50 text-gray-400 rounded-lg hover:bg-[#fdb913] hover:text-white transition-all"
                        title="Abrir PDF original"
                      >
                        <ExternalLink size={16} />
                      </button>
                      
                    </div>
                  </td>
                </tr>
              );
            })}

            {arquivosFiltrados.length === 0 && (
              <tr>
                <td
                  colSpan={5}
                  className="px-6 py-10 text-center text-xs font-bold text-gray-400 uppercase tracking-widest"
                >
                  Nenhum arquivo encontrado para este filtro.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {selectedFile && (
        <div className="fixed inset-0 bg-[#3a3a3a]/60 backdrop-blur-sm z-50 overflow-y-auto p-4">
          <div className="min-h-full flex items-start sm:items-center justify-center py-4">
            <div className="bg-white w-full max-w-xl max-h-[calc(100vh-2rem)] rounded-[32px] shadow-2xl overflow-hidden border border-white flex flex-col">
              <div className="shrink-0 p-6 border-b border-gray-50 flex justify-between items-start bg-gray-50/50">
                <div className="flex items-start gap-3 min-w-0">
                  <div className="p-2 bg-[#fdb913] rounded-lg text-white shrink-0">
                    <FileText size={18} />
                  </div>

                  <div className="min-w-0">
                    {selectedFile?.numero_solicitacao && (
                      <p className="mt-1 inline-flex items-center gap-1.5 text-[9px] font-black uppercase tracking-widest text-gray-400">
                        <Hash size={10} />
                        Solicitação #{selectedFile.numero_solicitacao}
                      </p>
                    )}

                    <button
                      type="button"
                      onClick={() => abrirPdfOriginal(selectedFile.id)}
                      className="mt-2 inline-flex items-center gap-1.5 text-[9px] font-black uppercase tracking-widest text-[#fdb913] hover:text-[#3a3a3a]"
                    >
                      <ExternalLink size={12} />
                      Ver PDF original
                    </button>

                    {selectedFile?.ultima_edicao_por && selectedFile?.ultima_edicao_em && (
                      <p className="mt-2 text-[9px] font-bold text-gray-400 uppercase tracking-widest">
                        Última edição por {selectedFile.ultima_edicao_por} em {selectedFile.ultima_edicao_em}
                      </p>
                    )}
                  </div>
                </div>

                <button
                  onClick={fecharModalArquivo}
                  disabled={savingDetails}
                  className="text-gray-300 hover:text-[#3a3a3a] transition-colors disabled:opacity-50 shrink-0 ml-4"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-6 space-y-5">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[9px] font-black text-gray-400 uppercase tracking-widest mb-2 ml-1">
                      Banco
                    </label>

                    <input
                      list="lista-bancos"
                      type="text"
                      className="w-full bg-gray-50 border border-gray-200 rounded-2xl px-4 py-3 text-xs text-[#3a3a3a] font-bold focus:outline-none focus:ring-2 focus:ring-[#fdb913]/40 focus:border-[#fdb913]"
                      placeholder="Ex: Banco Inter"
                      value={editBanco}
                      onChange={(e) => setEditBanco(e.target.value)}
                    />

                    <datalist id="lista-bancos">
                      <option value="Banco Inter" />
                      <option value="Itaú" />
                      <option value="Bradesco" />
                      <option value="Caixa Econômica Federal" />
                      <option value="Banco do Brasil" />
                      <option value="Santander" />
                      <option value="Sicoob" />
                      <option value="Sicredi" />
                      <option value="Nubank" />
                      <option value="C6 Bank" />
                      <option value="XP Investimentos" />
                      <option value="Omie.CASH" />
                      <option value="Transpocred" />
                      <option value="PagSeguro" />
                      <option value="Stone" />
                      <option value="Desconhecido" />
                    </datalist>
                  </div>

                  <div>
                    <label className="block text-[9px] font-black text-gray-400 uppercase tracking-widest mb-2 ml-1">
                      Período
                    </label>

                    <input
                      type="text"
                      className="w-full bg-gray-50 border border-gray-200 rounded-2xl px-4 py-3 text-xs text-[#3a3a3a] font-bold focus:outline-none focus:ring-2 focus:ring-[#fdb913]/40 focus:border-[#fdb913]"
                      placeholder="Ex: 04/2026"
                      value={editPeriodo}
                      onChange={(e) => setEditPeriodo(e.target.value)}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2 ml-1">
                    <p className="text-[9px] font-black text-gray-400 uppercase tracking-widest">
                      Observação interna
                    </p>

                    <span className="text-[9px] font-bold text-gray-300 uppercase">
                      Opcional
                    </span>
                  </div>

                  <textarea
                    className="w-full min-h-[110px] bg-gray-50 border border-gray-200 rounded-2xl px-4 py-3 text-xs text-[#3a3a3a] font-medium focus:outline-none focus:ring-2 focus:ring-[#fdb913]/40 focus:border-[#fdb913] resize-y"
                    placeholder="Ex: Cliente enviou extrato sem movimentação / verificar manualmente no PDF..."
                    value={editObs}
                    onChange={(e) => setEditObs(e.target.value)}
                  />
                </div>

                <div className="border border-gray-100 rounded-2xl overflow-hidden">
                  <button
                    type="button"
                    onClick={() => setShowAnalysis((prev) => !prev)}
                    className="w-full flex items-center justify-between gap-3 bg-gray-50 px-4 py-3 text-left"
                  >
                    <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">
                      Leitura automática
                    </p>

                    <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">
                      {showAnalysis ? 'Ocultar' : 'Ver'}
                    </span>
                  </button>

                  {showAnalysis && (
                    <div className="p-4 bg-[#3a3a3a]">
                      <RenderResumoIA
                        conteudo={selectedFile.resumo_detalhado}
                        selectedFile={selectedFile}
                      />
                    </div>
                  )}
                </div>
              </div>

              <div className="shrink-0 p-6 border-t border-gray-100 bg-white">
                {hasUnsavedChanges && (
                  <p className="text-[10px] font-bold text-yellow-700 bg-yellow-50 border border-yellow-100 rounded-xl px-4 py-2 mb-3 text-center uppercase tracking-widest">
                    Existem alterações não salvas
                  </p>
                )}

                <div className="flex flex-col sm:flex-row gap-3">
                  <button
                    onClick={handleSalvarDetalhesArquivo}
                    disabled={savingDetails || !hasUnsavedChanges}
                    className="flex-1 bg-[#fdb913] hover:bg-yellow-400 disabled:opacity-60 disabled:cursor-not-allowed text-[#3a3a3a] py-4 rounded-xl font-black text-[11px] uppercase tracking-widest transition-all flex items-center justify-center gap-2"
                  >
                    {savingDetails ? (
                      <>
                        <Loader2 size={16} className="animate-spin" />
                        Salvando...
                      </>
                    ) : (
                      <>
                        <Pencil size={16} />
                        Salvar alterações
                      </>
                    )}
                  </button>

                  <button
                    onClick={fecharModalArquivo}
                    disabled={savingDetails}
                    className="flex-1 bg-[#3a3a3a] hover:bg-[#252525] disabled:opacity-60 disabled:cursor-not-allowed text-white py-4 rounded-xl font-black text-[11px] uppercase tracking-widest transition-all"
                  >
                    Fechar
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
};

export default DetalhesCliente;