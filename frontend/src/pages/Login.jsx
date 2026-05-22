import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { toast } from 'sonner';
import { Eye, EyeOff, Lock, Mail, UserPlus, ArrowRight, ArrowLeft, AlertCircle } from 'lucide-react';

const Login = () => {
  const [mode, setMode] = useState('login');
  const [formData, setFormData] = useState({ email: '', password: '', username: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  
  const navigate = useNavigate();

  // Ajustado para text-xs e py-2.5 para um visual mais técnico e limpo
  const inputClass = "w-full pl-10 pr-4 py-2.5 bg-gray-50/50 border border-gray-100 rounded-xl outline-none focus:bg-white focus:border-gray-300 focus:ring-4 focus:ring-gray-500/5 transition-all text-xs font-medium placeholder:text-gray-300 text-gray-700";
  const labelClass = "text-[9px] uppercase font-bold text-gray-400 ml-1 tracking-widest block mb-1";

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (mode === 'login') {
        const { data } = await api.post('/auth/login', { email: formData.email, password: formData.password });
          localStorage.setItem('token', data.token);
          
          // Salvamos exatamente a chave 'username' que o Layout espera ler
          localStorage.setItem('username', data.usuario.username);
          
          toast.success('Bem-vindo de volta!'); 
          navigate('/dashboard');        
      } else if (mode === 'signup') {
        await api.post('/auth/register', { 
          username: formData.username, 
          email: formData.email, 
          password: formData.password 
        });
        
        toast.success('Conta criada com sucesso!', {
          description: 'Agora você já pode realizar o login.',
        });
        setMode('login');
      }
    } catch (err) {
      const mensagemErro = err.response?.data?.erro || 'Erro na autenticação.';
      setError(mensagemErro);
      toast.error('Ops! Algo deu errado', { description: mensagemErro }); // Mensagem de erro
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f3f4f6] px-4 py-10">
      <div className="flex w-full max-w-[800px] bg-white rounded-[32px] shadow-2xl overflow-hidden h-fit border border-white">
        
        {/* LADO ESQUERDO */}
        <div className="hidden md:flex flex-col items-center justify-center w-[42%] bg-[#3a3a3a] p-10 text-center relative overflow-hidden">
          <div className="absolute right-0 top-0 h-full w-1.5 bg-[#fdb913]"></div>
          
          <div className="flex flex-col items-center">
            {/* Logo ajustada para w-32 para não dominar demais o espaço */}
            <img src="/logos.png" alt="SCRYTA" className="w-32 mb-6" />
            <div className="space-y-2">
              <h2 className="text-lg font-bold text-white tracking-tight">ExtratoContabil</h2>
              <div className="h-0.5 w-6 bg-[#fdb913] mx-auto opacity-80"></div>
              <p className="text-[#fdb913] text-[8px] uppercase font-bold tracking-[0.4em] pt-1 leading-relaxed">
                Extração Inteligente de Dados
              </p>
            </div>
          </div>          
        </div>

        {/* LADO DIREITO */}
        <div className="flex flex-col justify-center w-full md:w-[58%] py-10 px-12 bg-white">
          <div className="mb-6">
            <h1 className="text-xl font-bold text-[#3a3a3a] mb-1.5 leading-tight">
              {mode === 'login' ? 'Acesse sua conta' : 'Nova Conta'}
            </h1>
            <p className="text-gray-400 text-xs font-medium">
              Gestão de extratos para contabilidade.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-50 text-red-600 text-[10px] p-3 rounded-xl border border-red-100 font-bold flex items-center justify-center gap-2">
                <AlertCircle size={14} /> {error}
              </div>
            )}

            {mode === 'signup' && (
              <div>
                <label className={labelClass}>Usuário</label>
                <div className="relative">
                  <UserPlus className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-300" size={16} />
                  <input name="username" type="text" className={inputClass} placeholder="Usuário" onChange={handleInputChange} required />
                </div>
              </div>
            )}

            <div>
              <label className={labelClass}>E-mail Corporativo</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-300" size={16} />
                <input name="email" type="email" className={inputClass} placeholder="email@scryta.com.br" onChange={handleInputChange} required />
              </div>
            </div>

            <div>
              <label className={labelClass}>Senha</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-300" size={16} />
                <input
                  name="password"
                  type={showPassword ? "text" : "password"}
                  className={inputClass}
                  placeholder="••••••••"
                  onChange={handleInputChange}
                  required
                />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400">
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button 
              type="submit" 
              disabled={loading} 
              className="w-full bg-[#3a3a3a] hover:bg-[#252525] text-white py-3 rounded-xl font-bold text-[11px] uppercase tracking-widest transition-all flex items-center justify-center gap-2 mt-2 shadow-lg shadow-gray-200 active:scale-[0.98]"
            >
              {loading ? 'Entrando...' : 'Entrar no Sistema'}
              {!loading && <ArrowRight size={14} />}
            </button>

            {mode === 'login' && (
              <div className="text-center pt-1">
                <button type="button" onClick={() => setMode('forgot')} className="text-[9px] text-gray-400 font-bold hover:text-[#fdb913] uppercase tracking-wider">
                  Esqueci minha senha
                </button>
              </div>
            )}
          </form>

          <div className="mt-8 text-center border-t border-gray-50 pt-6">
            <p className="text-[10px] text-gray-400 font-bold">
              {mode === 'login' ? (
                <>Novo por aqui? <button onClick={() => setMode('signup')} className="text-[#3a3a3a] font-bold hover:underline uppercase ml-1">Crie sua conta</button></>
              ) : (
                <button onClick={() => setMode('login')} className="text-[#3a3a3a] font-bold flex items-center justify-center gap-2 mx-auto uppercase">
                  <ArrowLeft size={12} /> Voltar para o Login
                </button>
              )}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;