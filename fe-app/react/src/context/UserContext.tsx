import React, { createContext, useContext, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useUserState } from '../state-mgmt/user'; // Use global state

type UserContextType = {
  fetchUser: () => Promise<void>;
};

const UserContext = createContext<UserContextType | undefined>(undefined);

export const UserProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const setUser = useUserState().setData; // Use setData to update user state
  const { refetch } = useQuery(
    ['session'],
    async () => {
      const response = await fetch('/api/session', { credentials: 'include' });
      if (!response.ok) {
        throw new Error('Failed to fetch session data');
      }
      return response.json();
    },
    {
      onSuccess: (data) => setUser({ ...data, isSignedOn: true }),
      onError: () =>
        setUser({ id: '', username: '', isSignedOn: false, bookList: [] }),
      refetchOnWindowFocus: false,
      enabled: false, // Disable automatic query execution
    }
  );

  const fetchUser = async () => {
    try {
      await refetch();
    } catch (error) {
      console.error('Failed to fetch user session:', error);
    }
  };

  useEffect(() => {
    fetchUser(); // Fetch session data on initial load
  }, []);

  return (
    <UserContext.Provider value={{ fetchUser }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = (): UserContextType => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};
