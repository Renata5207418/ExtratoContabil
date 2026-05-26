import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/api', 
  
});

// Interceptador de Requisição (Ida)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptador de Resposta (Volta)
api.interceptors.response.use(
  (response) => {
    // Se a requisição deu certo, só repassa a resposta pra frente
    return response;
  },
  (error) => {
    // Se deu erro e o status for 401 (Não Autorizado/Token Expirado)
    if (error.response && error.response.status === 401) {
      // Limpa os dados velhos
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      
      // Força o redirecionamento para o login (caso já não esteja lá)
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    
    // Repassa o erro pra frente caso a tela precise exibir um toast
    return Promise.reject(error);
  }
);

export default api;