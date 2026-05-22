import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner'; 
import Login from './pages/Login';
import Acompanhamento from './pages/Acompanhamento';
import Dashboard from './pages/Dashboard';
import DetalhesCliente from './pages/DetalhesCliente';

const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-right" richColors expand={false} />
      
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/acompanhamento" element={<PrivateRoute><Acompanhamento /></PrivateRoute>} />
        <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
        <Route path="/extratos/:codigo" element={<PrivateRoute><DetalhesCliente /></PrivateRoute>} />
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;