import React from 'react';
import { Router, Route } from 'wouter';
import { UserProvider } from './context/UserContext';
import NavBar from './components/NavBar';
import Login from './components/Login';
import Home from './components/Home';
import ProtectedRoute from './components/ProtectedRoute';
import './App.css';

const App: React.FC = () => {
  return (
    <UserProvider>
      <NavBar />
      <Router>
        <Route path='/login' component={Login} />
        <Route path='/'>
          <ProtectedRoute>
            <Home />
          </ProtectedRoute>
        </Route>
      </Router>
    </UserProvider>
  );
};

export default App;
